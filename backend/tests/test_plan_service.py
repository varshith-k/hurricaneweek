import httpx

import app.services.plan_service as plan_service_module
from app.services.plan_service import PlanService

DECISION_HISTORY = [
    {"stage": "T_MINUS_120", "event_id": "supply_run", "choice_id": "delay_shopping", "consequence": "You risk shortages later."},
]


def test_disabled_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    service = PlanService()
    assert service.enabled is False
    result = service.generate_coach_summary(
        outcome="Safe but Exposed", overall_score=60, preparedness_gaps=["no evacuation plan"],
        strengths=[], decision_history=DECISION_HISTORY,
    )
    assert result is None


class FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"candidates": [{"content": {"parts": [{"text": self._body}]}}]}


def test_valid_json_response_is_parsed(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    service = PlanService()

    body = (
        '{"biggest_mistake": "You delayed buying supplies.", '
        '"best_decision": "You verified your insurance early.", '
        '"what_to_change": "Buy supplies on day one."}'
    )
    monkeypatch.setattr(plan_service_module.httpx, "post", lambda *a, **k: FakeResponse(body))

    result = service.generate_coach_summary(
        outcome="Safe but Exposed", overall_score=60, preparedness_gaps=["no evacuation plan"],
        strengths=["verified insurance"], decision_history=DECISION_HISTORY,
    )
    assert result == {
        "biggest_mistake": "You delayed buying supplies.",
        "best_decision": "You verified your insurance early.",
        "what_to_change": "Buy supplies on day one.",
    }


def test_malformed_json_degrades_to_none(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    service = PlanService()

    monkeypatch.setattr(plan_service_module.httpx, "post", lambda *a, **k: FakeResponse("not valid json"))

    result = service.generate_coach_summary(
        outcome="Safe but Exposed", overall_score=60, preparedness_gaps=[],
        strengths=[], decision_history=DECISION_HISTORY,
    )
    assert result is None


def test_missing_key_in_response_degrades_to_none(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    service = PlanService()

    body = '{"biggest_mistake": "You delayed buying supplies."}'
    monkeypatch.setattr(plan_service_module.httpx, "post", lambda *a, **k: FakeResponse(body))

    result = service.generate_coach_summary(
        outcome="Safe but Exposed", overall_score=60, preparedness_gaps=[],
        strengths=[], decision_history=DECISION_HISTORY,
    )
    assert result is None


def test_network_failure_degrades_to_none(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    service = PlanService()

    def broken_post(*args, **kwargs):
        raise httpx.ConnectError("simulated network failure")

    monkeypatch.setattr(plan_service_module.httpx, "post", broken_post)

    result = service.generate_coach_summary(
        outcome="Safe but Exposed", overall_score=60, preparedness_gaps=[],
        strengths=[], decision_history=DECISION_HISTORY,
    )
    assert result is None
