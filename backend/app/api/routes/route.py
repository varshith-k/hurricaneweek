from uuid import UUID

from fastapi import APIRouter

from app.api.deps import route_service, simulation_store
from app.schemas.route import EvacuationRoute

router = APIRouter(tags=["route"])


@router.get("/simulations/{simulation_id}/evacuation-route", response_model=EvacuationRoute)
def get_evacuation_route(simulation_id: UUID) -> dict:
    state = simulation_store.get(simulation_id)
    transport_type = state["player_profile"]["transport_type"]
    flood_risk = state["storm"]["flood_risk"]
    return route_service.evacuation_route(transport_type=transport_type, flood_risk=flood_risk)
