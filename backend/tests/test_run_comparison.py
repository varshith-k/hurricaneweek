from fastapi.testclient import TestClient

import app.services.plan_service as plan_service_module
from app.main import app
from app.services.plan_service import PlanService

client = TestClient(app)

PREVIOUS = {
    "outcome": "High Vulnerability",
    "overall_score": 55,
    "scores": {"safety": 50, "financial": 60, "preparedness": 55, "timing": 50},
    "decision_history": [{"stage": "T_MINUS_120", "event_id": "supply_run", "choice_id": "delay_shopping", "consequence": "You risk shortages later."}],
    "financial_summary": {"starting_cash": 400, "ending_cash": 100, "damage": 300},
}
CURRENT = {
    "outcome": "Well Prepared",
    "overall_score": 82,
    "scores": {"safety": 90, "financial": 80, "preparedness": 85, "timing": 75},
    "decision_history": [{"stage": "T_MINUS_120", "event_id": "supply_run", "choice_id": "buy_early_supplies", "consequence": "You secure food and water before shelves thin out."}],
    "financial_summary": {"starting_cash": 400, "ending_cash": 250, "damage": 60},
}


class FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"candidates": [{"content": {"parts": [{"text": self._body}]}}]}


def test_disabled_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    service = PlanService()
    assert service.generate_run_comparison(PREVIOUS, CURRENT) is None


def test_valid_response_is_parsed(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    service = PlanService()
    body = '{"explanation": "You bought supplies early this time instead of delaying, which raised your preparedness and safety scores."}'
    monkeypatch.setattr(plan_service_module.httpx, "post", lambda *a, **k: FakeResponse(body))

    result = service.generate_run_comparison(PREVIOUS, CURRENT)
    assert result == "You bought supplies early this time instead of delaying, which raised your preparedness and safety scores."


def test_malformed_response_degrades_to_none(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    service = PlanService()
    monkeypatch.setattr(plan_service_module.httpx, "post", lambda *a, **k: FakeResponse("not json"))
    assert service.generate_run_comparison(PREVIOUS, CURRENT) is None


def test_compare_runs_endpoint_returns_valid_shape(monkeypatch) -> None:
    from app.api import deps

    monkeypatch.setattr(deps.plan_service, "generate_run_comparison", lambda previous, current: "You improved by evacuating earlier.")

    response = client.post("/api/coach/compare-runs", json={"previous": PREVIOUS, "current": CURRENT})
    assert response.status_code == 200
    assert response.json() == {"explanation": "You improved by evacuating earlier."}


def test_compare_runs_endpoint_handles_no_explanation(monkeypatch) -> None:
    from app.api import deps

    monkeypatch.setattr(deps.plan_service, "generate_run_comparison", lambda previous, current: None)

    response = client.post("/api/coach/compare-runs", json={"previous": PREVIOUS, "current": CURRENT})
    assert response.status_code == 200
    assert response.json() == {"explanation": None}
