from app.services.route_service import RouteService


def test_disabled_when_no_api_key(monkeypatch) -> None:
    monkeypatch.delenv("ORS_API_KEY", raising=False)
    service = RouteService()
    assert service.enabled is False
    result = service.evacuation_route(transport_type="car", flood_risk=0.1)
    assert result["available"] is False


def test_route_lookup_failure_degrades_gracefully(monkeypatch) -> None:
    monkeypatch.setenv("ORS_API_KEY", "fake-key-for-test")
    service = RouteService()
    assert service.enabled is True

    def broken_post(*args, **kwargs):
        raise RuntimeError("simulated network failure")

    import app.services.route_service as route_service_module

    monkeypatch.setattr(route_service_module.httpx, "post", broken_post)
    result = service.evacuation_route(transport_type="scooter", flood_risk=0.9)
    assert result["available"] is False


def test_scooter_with_high_flood_risk_is_flagged_compromised(monkeypatch) -> None:
    monkeypatch.setenv("ORS_API_KEY", "fake-key-for-test")
    service = RouteService()

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"routes": [{"summary": {"distance": 8100, "duration": 1632}}]}

    def fake_post(*args, **kwargs):
        return FakeResponse()

    import app.services.route_service as route_service_module

    monkeypatch.setattr(route_service_module.httpx, "post", fake_post)

    result = service.evacuation_route(transport_type="scooter", flood_risk=0.9)
    assert result["available"] is True
    assert result["feasibility"] == "compromised"
    assert result["warning"]

    calm_result = service.evacuation_route(transport_type="scooter", flood_risk=0.1)
    assert calm_result["feasibility"] == "clear"
    assert calm_result["warning"] is None

    car_result = service.evacuation_route(transport_type="car", flood_risk=0.9)
    assert car_result["feasibility"] == "clear"
