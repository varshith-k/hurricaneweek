from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_coverage_check_returns_entries() -> None:
    response = client.get("/api/coverage-check")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["entries"]) >= 7
    assert "not a coverage determination" in payload["disclaimer"]


def test_every_entry_has_required_fields_and_a_not_sure_option() -> None:
    payload = client.get("/api/coverage-check").json()
    seen_ids = set()
    for entry in payload["entries"]:
        assert entry["id"] not in seen_ids
        seen_ids.add(entry["id"])
        assert entry["label"]
        assert entry["wind"]
        assert entry["flood"]
        assert entry["action"]
        assert entry["source"]
    assert "not_sure" in seen_ids


def test_not_sure_entry_is_honest_about_not_knowing() -> None:
    payload = client.get("/api/coverage-check").json()
    not_sure = next(e for e in payload["entries"] if e["id"] == "not_sure")
    assert "don't have a confident" in not_sure["wind"]
    assert "N/A" in not_sure["source"]
