from contextlib import contextmanager
from uuid import uuid4

import app.services.tiger_service as tiger_service_module
from app.services.tiger_service import TigerService


def _make_enabled_service() -> TigerService:
    service = TigerService.__new__(TigerService)
    service.enabled = True
    return service


def test_telemetry_insert_failure_does_not_raise(monkeypatch) -> None:
    """A Tiger Data blip must never fail the decision it's logging - telemetry
    is decoration, not the gameplay itself."""

    @contextmanager
    def broken_connection():
        raise tiger_service_module.Error("simulated outage")
        yield  # pragma: no cover - unreachable, keeps this a generator

    monkeypatch.setattr(tiger_service_module, "get_db_connection", broken_connection)

    service = _make_enabled_service()
    service.log_simulation_state(
        simulation_id=uuid4(),
        stage="T_MINUS_120",
        event_id="supply_run",
        choice_id="buy_partial_supplies",
        state={"cash": 400, "preparedness_points": 0, "timing_points": 0},
        scores={"safety": 100, "financial": 100, "preparedness": 100, "timing": 100, "overall": 100},
        payload={},
    )


def test_disabled_service_skips_telemetry_without_touching_the_db(monkeypatch) -> None:
    def fail_if_called():
        raise AssertionError("get_db_connection should not be called when disabled")

    monkeypatch.setattr(tiger_service_module, "get_db_connection", fail_if_called)

    service = TigerService.__new__(TigerService)
    service.enabled = False
    service.log_simulation_state(
        simulation_id=uuid4(),
        stage="T_MINUS_120",
        event_id="supply_run",
        choice_id="buy_partial_supplies",
        state={"cash": 400, "preparedness_points": 0, "timing_points": 0},
        scores={"safety": 100, "financial": 100, "preparedness": 100, "timing": 100, "overall": 100},
        payload={},
    )
    assert service.get_simulation_timeline(uuid4()) == []
    assert service.get_hourly_summary() == []
