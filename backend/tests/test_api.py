from fastapi.testclient import TestClient

from app.api.deps import tiger_service
from app.main import app


client = TestClient(app)


def _create_simulation(transport_type: str = "scooter", has_insurance: bool = False) -> str:
    payload = {
        "player_profile": {
            "cash_on_hand": 500,
            "has_insurance": has_insurance,
            "housing_type": "apartment",
            "transport_type": transport_type,
            "household_size": 2,
            "needs_refrigerated_medication": False,
        }
    }
    response = client.post("/api/simulations", json=payload)
    assert response.status_code == 201
    return response.json()["simulation_id"]


def _submit_current_event(simulation_id: str, choice_id: str):
    event_response = client.get(f"/api/simulations/{simulation_id}/event")
    assert event_response.status_code == 200
    event = event_response.json()
    decision = client.post(
        f"/api/simulations/{simulation_id}/decisions",
        json={"event_id": event["event_id"], "choice_id": choice_id},
    )
    return event, decision


def test_health_check() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_simulation_and_first_event() -> None:
    simulation_id = _create_simulation()
    event_response = client.get(f"/api/simulations/{simulation_id}/event")
    payload = event_response.json()
    assert event_response.status_code == 200
    assert payload["event_id"] == "supply_run"
    assert payload["stage"] == "T_MINUS_120"


def test_stage_advances_once_after_valid_decision() -> None:
    simulation_id = _create_simulation()
    first_event = client.get(f"/api/simulations/{simulation_id}/event").json()

    decision = client.post(
        f"/api/simulations/{simulation_id}/decisions",
        json={"event_id": first_event["event_id"], "choice_id": "buy_partial_supplies"},
    )
    assert decision.status_code == 200
    assert decision.json()["state"]["stage"] == "T_MINUS_96"

    same_event = client.get(f"/api/simulations/{simulation_id}/event").json()
    assert same_event["stage"] == "T_MINUS_96"


def test_invalid_event_rejected() -> None:
    simulation_id = _create_simulation()
    response = client.post(
        f"/api/simulations/{simulation_id}/decisions",
        json={"event_id": "wrong_event", "choice_id": "buy_partial_supplies"},
    )
    assert response.status_code == 400


def test_invalid_choice_rejected() -> None:
    simulation_id = _create_simulation()
    current = client.get(f"/api/simulations/{simulation_id}/event").json()
    response = client.post(
        f"/api/simulations/{simulation_id}/decisions",
        json={"event_id": current["event_id"], "choice_id": "bad_choice"},
    )
    assert response.status_code == 400


def test_incompatible_event_filtered_for_non_scooter() -> None:
    simulation_id = _create_simulation(transport_type="car")
    _submit_current_event(simulation_id, "buy_partial_supplies")
    event = client.get(f"/api/simulations/{simulation_id}/event").json()
    assert event["event_id"] == "home_protection"


def test_scooter_damage_applies_only_when_unprotected() -> None:
    unprotected = _create_simulation(transport_type="scooter")
    _submit_current_event(unprotected, "buy_partial_supplies")
    _submit_current_event(unprotected, "do_nothing")
    _submit_current_event(unprotected, "skip_shift_prepare")
    _submit_current_event(unprotected, "skip_verification")
    _submit_current_event(unprotected, "stay_put")
    _submit_current_event(unprotected, "panic_actions")
    final_unprotected = _submit_current_event(unprotected, "delay_recovery_actions")[1].json()

    protected = _create_simulation(transport_type="scooter")
    _submit_current_event(protected, "buy_partial_supplies")
    _submit_current_event(protected, "protect_scooter_and_docs")
    _submit_current_event(protected, "skip_shift_prepare")
    _submit_current_event(protected, "skip_verification")
    _submit_current_event(protected, "stay_put")
    _submit_current_event(protected, "panic_actions")
    final_protected = _submit_current_event(protected, "delay_recovery_actions")[1].json()

    assert final_unprotected["state"]["financial_loss"] > final_protected["state"]["financial_loss"]


def test_safety_can_drop_for_non_evacuation() -> None:
    simulation_id = _create_simulation()
    _submit_current_event(simulation_id, "delay_shopping")
    _submit_current_event(simulation_id, "do_nothing")
    _submit_current_event(simulation_id, "work_shift")
    _submit_current_event(simulation_id, "skip_verification")
    _submit_current_event(simulation_id, "stay_put")
    _submit_current_event(simulation_id, "panic_actions")
    final_response = _submit_current_event(simulation_id, "delay_recovery_actions")[1]
    payload = final_response.json()
    assert payload["state"]["scores"]["safety"] < 40
    assert payload["final_report"]["outcome"] == "Critical Vulnerability"


def test_scores_stay_bounded() -> None:
    simulation_id = _create_simulation()
    for preferred in [
        "buy_early_supplies",
        "protect_scooter_and_docs",
        "skip_shift_prepare",
        "verify_insurance",
        "evacuate_early",
        "strict_protocol",
        "document_damage_and_plan",
    ]:
        event = client.get(f"/api/simulations/{simulation_id}/event").json()
        response = client.post(
            f"/api/simulations/{simulation_id}/decisions",
            json={"event_id": event["event_id"], "choice_id": preferred},
        )
        assert response.status_code == 200
    scores = response.json()["state"]["scores"]
    for value in scores.values():
        assert 0 <= value <= 100


def test_completed_run_rejects_new_decisions_and_report_available() -> None:
    simulation_id = _create_simulation()
    for preferred in [
        "buy_early_supplies",
        "protect_scooter_and_docs",
        "skip_shift_prepare",
        "verify_insurance",
        "evacuate_early",
        "strict_protocol",
        "document_damage_and_plan",
    ]:
        event = client.get(f"/api/simulations/{simulation_id}/event").json()
        done = client.post(
            f"/api/simulations/{simulation_id}/decisions",
            json={"event_id": event["event_id"], "choice_id": preferred},
        )

    assert done.json()["status"] == "completed"
    report = client.get(f"/api/simulations/{simulation_id}/report")
    assert report.status_code == 200

    final_event = client.get(f"/api/simulations/{simulation_id}/event").json()
    assert final_event["simulation_complete"] is True

    rejected = client.post(
        f"/api/simulations/{simulation_id}/decisions",
        json={"event_id": "recovery_decision", "choice_id": "document_damage_and_plan"},
    )
    assert rejected.status_code == 409


def test_deterministic_run_same_inputs_same_outputs() -> None:
    def run() -> dict:
        simulation_id = _create_simulation(transport_type="car", has_insurance=True)
        for choice in [
            "buy_partial_supplies",
            "reinforce_home",
            "work_shift",
            "verify_insurance",
            "shelter_locally",
            "strict_protocol",
            "document_damage_and_plan",
        ]:
            event = client.get(f"/api/simulations/{simulation_id}/event").json()
            response = client.post(
                f"/api/simulations/{simulation_id}/decisions",
                json={"event_id": event["event_id"], "choice_id": choice},
            )
        return response.json()["final_report"]

    first = run()
    second = run()
    assert first["outcome"] == second["outcome"]
    assert first["scores"] == second["scores"]
    assert first["financial_summary"] == second["financial_summary"]

def test_timeline_persists_rows_for_each_valid_decision() -> None:
    if not tiger_service.enabled:
        return

    simulation_id = _create_simulation()
    for choice in [
        "buy_early_supplies",
        "protect_scooter_and_docs",
        "skip_shift_prepare",
        "verify_insurance",
        "evacuate_early",
        "strict_protocol",
        "document_damage_and_plan",
    ]:
        event = client.get(f"/api/simulations/{simulation_id}/event").json()
        response = client.post(
            f"/api/simulations/{simulation_id}/decisions",
            json={"event_id": event["event_id"], "choice_id": choice},
        )
        assert response.status_code == 200

    timeline = client.get(f"/api/simulations/{simulation_id}/timeline")
    assert timeline.status_code == 200

    rows = timeline.json()
    assert len(rows) == 7
    assert rows[0]["event_id"] == "supply_run"
    assert rows[-1]["event_id"] == "recovery_decision"
    assert all(row["simulation_id"] == simulation_id for row in rows)


