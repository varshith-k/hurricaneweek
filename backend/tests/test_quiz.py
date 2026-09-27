from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_auto_insurance_quiz_returns_questions() -> None:
    response = client.get("/api/quiz/auto-insurance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Auto Insurance Readiness Quiz"
    assert len(payload["questions"]) >= 5


def test_every_question_has_a_valid_correct_index_and_matching_option_count() -> None:
    payload = client.get("/api/quiz/auto-insurance").json()
    seen_ids = set()
    for q in payload["questions"]:
        assert q["id"] not in seen_ids
        seen_ids.add(q["id"])
        assert 0 <= q["correct_index"] < len(q["options"])
        assert len(q["options"]) >= 2
        assert q["explanation"]
        assert q["source"]
