from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _create_simulation() -> str:
    payload = {
        "player_profile": {
            "cash_on_hand": 400,
            "has_insurance": False,
            "housing_type": "apartment",
            "transport_type": "scooter",
            "household_size": 2,
        }
    }
    response = client.post("/api/simulations", json=payload)
    assert response.status_code == 201
    return response.json()["simulation_id"]


def test_health_check() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_simulation_and_get_event() -> None:
    simulation_id = _create_simulation()
    event_response = client.get(f"/api/simulations/{simulation_id}/event")
    assert event_response.status_code == 200
    event = event_response.json()
    assert event["event_id"] == "t120_supply_run"
    assert event["simulation_complete"] is False
    assert len(event["choices"]) == 3


def test_decision_progression_until_completion() -> None:
    simulation_id = _create_simulation()

    while True:
        event_response = client.get(f"/api/simulations/{simulation_id}/event")
        assert event_response.status_code == 200
        event_payload = event_response.json()

        if event_payload["simulation_complete"]:
            break

        first_choice_id = event_payload["choices"][0]["choice_id"]
        decision_response = client.post(
            f"/api/simulations/{simulation_id}/decisions",
            json={"event_id": event_payload["event_id"], "choice_id": first_choice_id},
        )
        assert decision_response.status_code == 200
        result = decision_response.json()
        assert result["state"]["scores"]["safety"] >= 0
        assert result["state"]["scores"]["financial"] >= 0

        if result["status"] == "completed":
            assert result["next_event"] is None
            assert result["state"]["simulation_complete"] is True
            break


def test_reject_invalid_event_choice() -> None:
    simulation_id = _create_simulation()
    event_response = client.get(f"/api/simulations/{simulation_id}/event")
    event_payload = event_response.json()

    response = client.post(
        f"/api/simulations/{simulation_id}/decisions",
        json={"event_id": event_payload["event_id"], "choice_id": "invalid_choice"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid choice for event"

