import json
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.services.assistant_service import KNOWLEDGE_PATH, AssistantService, is_emergency, is_greeting, number_check
from app.services.snowflake_service import (
    FactsRepository,
    SnowflakeClient,
    SnowflakeConfig,
    SnowflakeError,
    account_host,
    checked_identifier,
)

client = TestClient(app)

CONFIG = SnowflakeConfig(
    account="myorg-myacct",
    token="test-token",
    role="HW_APP",
    warehouse="HW_WH",
    facts_table="HURRICANE_WEEK.APP.FACTS",
    knowledge_table="HURRICANE_WEEK.APP.KNOWLEDGE",
    cortex_model="llama3.1-70b",
    embed_model="snowflake-arctic-embed-m-v1.5",
    rag_enabled=True,
)
UNCONFIGURED = replace(CONFIG, account="", token="")

FACT_ROW = {
    "ID": "irma_nfip_claims_miami_dade",
    "LABEL": "NFIP flood claims in Miami-Dade from Hurricane Irma",
    "VALUE_NUM": 1234,
    "UNIT": "claims",
    "SOURCE": "FEMA NFIP via Snowflake Public Data",
    "NOTE": "date of loss 2017-09-09..2017-09-12",
    "UPDATED_AT": "2026-09-26",
}
RENTERS_CHUNK = {
    "ID": "kb:renters_insurance_flood",
    "CHUNK": "Does renters insurance cover flooding? Usually not. Flood coverage needs a separate policy; NFIP policies take 30 days.",
    "SOURCE": "Verified Hurricane Week content (verified)",
    "SCORE": 0.8123,
}


class FakeClient:
    def __init__(self, answer: str = "Usually not. You need a separate flood policy, which takes 30 days.", fail: bool = False):
        self.answer = answer
        self.fail = fail
        self.statements: list[tuple[str, list]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def execute(self, statement, bindings=None):
        if self.fail:
            raise SnowflakeError("Snowflake 401: auth failed")
        self.statements.append((statement, bindings or []))
        if "FROM HURRICANE_WEEK.APP.FACTS" in statement:
            return [FACT_ROW]
        if "VECTOR_COSINE_SIMILARITY" in statement:
            return [RENTERS_CHUNK]
        if "AI_COMPLETE" in statement:
            return [{"ANSWER": self.answer}]
        raise AssertionError(statement)


def make_service(tmp_path, config=CONFIG, fake=None, facts_payload=None):
    cache = tmp_path / "facts.json"
    if facts_payload is not None:
        cache.write_text(json.dumps(facts_payload))
    fake = fake or FakeClient()
    service = AssistantService(
        facts=FactsRepository(cache),
        config_loader=lambda: config,
        client_factory=lambda _config: fake,
    )
    return service, fake


# --- Safety rules --------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    ["help, I'm trapped and water is rising", "water is coming in under the door", "my friend is not breathing", "CALL 911"],
)
def test_emergency_detection(text) -> None:
    assert is_emergency(text)


@pytest.mark.parametrize(
    "text",
    [
        "Does renters insurance cover flooding?",
        "How much water should I store?",
        "What should I put in an emergency kit for two people?",
        "What's Miami-Dade's emergency management office phone number?",
    ],
)
def test_non_emergency_questions(text) -> None:
    assert not is_emergency(text)


@pytest.mark.parametrize("text", ["hi", "Hello!", "hey", "thanks", "ok", "good morning"])
def test_greeting_detection(text) -> None:
    assert is_greeting(text)


@pytest.mark.parametrize("text", ["hi, does renters insurance cover flooding?", "How much water should I store?"])
def test_non_greeting_questions(text) -> None:
    assert not is_greeting(text)


def test_greeting_is_answered_without_llm(tmp_path) -> None:
    service, fake = make_service(tmp_path)
    result = service.ask(question="hi")
    assert result["kind"] == "greeting"
    assert result["ai_meta"] is None
    assert fake.statements == []


def test_number_check() -> None:
    context = "NFIP policies take 30 days. 1,234 claims. Average payout 5321.67 USD."
    assert number_check("It takes 30 days; there were 1,234 claims.", context)
    assert number_check("The average was about $5,322.", context)
    assert number_check("Call 911 if in danger.", context)
    assert not number_check("It takes 45 days.", context)


def test_emergency_never_calls_snowflake(tmp_path) -> None:
    service, fake = make_service(tmp_path)
    result = service.ask(question="help, I'm trapped and water is rising")
    assert result["kind"] == "emergency"
    assert "911" in result["answer"]
    assert fake.statements == []


# --- Answer paths ---------------------------------------------------------------------


def test_question_id_returns_verified_answer(tmp_path) -> None:
    service, fake = make_service(tmp_path)
    result = service.ask(question_id="water_supply")
    assert result["kind"] == "verified"
    assert "1 gallon" in result["answer"]
    assert fake.statements == []


def test_cortex_rag_answer(tmp_path) -> None:
    service, fake = make_service(tmp_path)
    result = service.ask(question="Does renters insurance cover flooding?")
    assert result["kind"] == "ai"
    meta = result["ai_meta"]
    assert meta["provider"] == "snowflake-cortex-rag"
    assert meta["number_check"] == "passed"
    assert meta["retrieved"][0] == {"id": "kb:renters_insurance_flood", "source": RENTERS_CHUNK["SOURCE"], "score": 0.8123}
    assert "<question>" in meta["sql_statement"] and "test-token" not in meta["sql_statement"]
    retrieval, completion = fake.statements
    assert retrieval[1][:2] == ["snowflake-arctic-embed-m-v1.5", "Does renters insurance cover flooding?"]
    assert completion[1][0] == "llama3.1-70b"
    assert "Usually not" in completion[1][1]


def test_invented_number_falls_back_to_verified(tmp_path) -> None:
    service, _ = make_service(tmp_path, fake=FakeClient(answer="Flood policies take 90 days to start."))
    result = service.ask(question="Does renters insurance cover flooding?")
    assert result["kind"] == "verified"
    assert result["question_id"] == "renters_insurance_flood"
    assert result["ai_meta"]["number_check"] == "failed"


def test_snowflake_failure_falls_back(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    service, _ = make_service(tmp_path, fake=FakeClient(fail=True))
    result = service.ask(question="Does renters insurance cover flooding?")
    assert result["kind"] == "verified"
    assert result["ai_meta"] is None


def test_unanswerable_without_ai_is_safe_fallback(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    service, _ = make_service(tmp_path, config=UNCONFIGURED)
    result = service.ask(question="qwerty zxcvb")
    assert result["kind"] == "fallback"


def test_history_is_trimmed_to_four_turns(tmp_path) -> None:
    service, fake = make_service(tmp_path)
    history = [{"role": "user", "content": f"turn {index}"} for index in range(6)]
    service.ask(question="Does renters insurance cover flooding?", history=history)
    prompt = fake.statements[-1][1][1]
    assert "turn 5" in prompt and "turn 2" in prompt and "turn 1" not in prompt


# --- Facts and intro --------------------------------------------------------------------


def test_refresh_writes_cache(tmp_path) -> None:
    service, _ = make_service(tmp_path)
    result = service.refresh_context()
    assert result["source"] == "snowflake-live"
    assert result["facts"][0]["value_num"] == 1234
    cached = service.facts.load()
    assert cached["source"] == "cache" and cached["facts"][0]["id"] == FACT_ROW["ID"]


def test_refresh_failure_returns_cache(tmp_path) -> None:
    payload = {"facts": [{"id": "x", "label": "Cached", "value_num": 1, "unit": "u", "source": "s", "note": "n"}], "updated_at": "t"}
    service, _ = make_service(tmp_path, fake=FakeClient(fail=True), facts_payload=payload)
    result = service.refresh_context()
    assert result["source"] == "cache"
    assert result["facts_count"] == 1
    assert result["error"]


def test_intro_without_snowflake(tmp_path) -> None:
    service, _ = make_service(tmp_path, config=UNCONFIGURED)
    intro = service.intro()
    assert "911" in intro["emergency_notice"]
    assert intro["powered_by"]["rag_enabled"] is False
    assert intro["facts_source"] == "none"
    assert intro["suggested_questions"]


def test_knowledge_file_is_well_formed() -> None:
    entries = json.loads(KNOWLEDGE_PATH.read_text())
    ids = [entry["id"] for entry in entries]
    assert len(ids) == len(set(ids))
    for entry in entries:
        assert entry["question"].endswith("?")
        assert entry["answer"] and entry["source"] and entry["status"] == "verified"


# --- SQL API client ---------------------------------------------------------------------


def test_sql_api_client_polls_and_reads_partitions() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.headers["Authorization"] == "Bearer secret"
        assert request.headers["X-Snowflake-Authorization-Token-Type"] == "PROGRAMMATIC_ACCESS_TOKEN"
        if request.method == "POST":
            body = json.loads(request.content)
            assert body["bindings"] == {"1": {"type": "TEXT", "value": "a"}, "2": {"type": "FIXED", "value": "3"}}
            return httpx.Response(202, json={"statementHandle": "h1"})
        if request.url.params.get("partition") == "1":
            return httpx.Response(200, json={"data": [["2", "b"]]})
        return httpx.Response(
            200,
            json={
                "statementHandle": "h1",
                "resultSetMetaData": {
                    "rowType": [{"name": "n", "type": "fixed"}, {"name": "s", "type": "text"}],
                    "partitionInfo": [{}, {}],
                },
                "data": [["1", "a"]],
            },
        )

    with SnowflakeClient("myorg-my_acct", "secret", transport=httpx.MockTransport(handler)) as sf:
        rows = sf.execute("SELECT ?, ?", ["a", 3])
    assert rows == [{"N": 1, "S": "a"}, {"N": 2, "S": "b"}]
    assert str(calls[0].url).startswith("https://myorg-my-acct.snowflakecomputing.com/api/v2/statements")


def test_sql_api_error_message_is_surfaced_without_token() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(401, json={"message": "Invalid token", "code": "390303"}))
    with SnowflakeClient("acct", "secret", transport=transport) as sf:
        with pytest.raises(SnowflakeError) as error:
            sf.execute("SELECT 1")
    assert "Invalid token" in str(error.value) and "secret" not in str(error.value)


def test_date_and_timestamp_decoding() -> None:
    from app.services.snowflake_service import convert_value

    assert convert_value("17419", "date") == "2017-09-10"
    assert convert_value("1505001600.000000000", "timestamp_ntz") == "2017-09-10T00:00:00"
    assert convert_value("1505001600.000000000 1440", "timestamp_tz") == "2017-09-10T00:00:00"


def test_helpers() -> None:
    assert account_host("MyOrg-My_Acct") == "https://myorg-my-acct.snowflakecomputing.com"
    assert checked_identifier("HURRICANE_WEEK.APP.FACTS") == "HURRICANE_WEEK.APP.FACTS"
    with pytest.raises(SnowflakeError):
        checked_identifier("FACTS; DROP TABLE X")


# --- HTTP endpoints (Snowflake forced off so tests never reach the real account) --


@pytest.fixture
def offline_assistant(monkeypatch, tmp_path):
    monkeypatch.setattr(deps.assistant_service, "_config_loader", lambda: UNCONFIGURED)
    monkeypatch.setattr(deps.assistant_service, "facts", FactsRepository(tmp_path / "facts.json"))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_endpoints_work_offline(offline_assistant) -> None:
    intro = client.get("/api/assistant/intro")
    assert intro.status_code == 200
    assert intro.json()["powered_by"]["snowflake_configured"] is False

    emergency = client.post("/api/assistant/ask", json={"question": "help, I'm trapped and water is rising"})
    assert emergency.json()["kind"] == "emergency"

    verified = client.post("/api/assistant/ask", json={"question_id": "floodwater"})
    assert verified.json()["kind"] == "verified"

    assert client.post("/api/assistant/ask", json={"question_id": "nope"}).status_code == 404
    assert client.post("/api/assistant/ask", json={}).status_code == 422
    assert client.post("/api/assistant/ask", json={"question": "x" * 501}).status_code == 422

    refresh = client.post("/api/context/refresh")
    assert refresh.status_code == 200
    assert refresh.json()["source"] == "none" and refresh.json()["error"]


def test_intro_includes_last_run(offline_assistant, monkeypatch) -> None:
    fact = {"id": "f", "label": "Cached fact", "value_num": 7, "unit": "u", "source": "s", "note": "n"}
    monkeypatch.setattr(deps.simulation_engine, "real_world_context_loader", lambda: [fact])
    profile = {"cash_on_hand": 400, "housing_type": "apartment", "transport_type": "car"}
    simulation_id = client.post("/api/simulations", json={"player_profile": profile, "seed": 3}).json()["simulation_id"]
    while True:
        event = client.get(f"/api/simulations/{simulation_id}/event").json()
        if event["simulation_complete"]:
            break
        choice = event["choices"][-1]["choice_id"]
        client.post(f"/api/simulations/{simulation_id}/decisions", json={"event_id": event["event_id"], "choice_id": choice})

    intro = client.get("/api/assistant/intro", params={"simulation_id": simulation_id}).json()
    assert intro["last_run"]["status"] == "completed"
    assert intro["last_run"]["preparedness_gaps"]
    report = client.get(f"/api/simulations/{simulation_id}/report").json()
    assert report["real_world_context"] == [fact]
