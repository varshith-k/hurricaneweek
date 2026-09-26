from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_simulation_engine
from app.schemas.decision import DecisionRequest, DecisionResponse
from app.schemas.simulation import SimulationCreateRequest, SimulationCreateResponse
from app.services.simulation_engine import SimulationEngine

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("", response_model=SimulationCreateResponse, status_code=201)
def create_simulation(
    payload: SimulationCreateRequest,
    engine: SimulationEngine = Depends(get_simulation_engine),
) -> SimulationCreateResponse:
    record = engine.create_simulation(payload.player_profile)
    return SimulationCreateResponse(simulation_id=record.simulation_id, state=engine.get_state(record.simulation_id))


@router.get("/{simulation_id}/event")
def get_current_event(
    simulation_id: UUID,
    engine: SimulationEngine = Depends(get_simulation_engine),
):
    return engine.get_current_event(simulation_id)


@router.post("/{simulation_id}/decisions", response_model=DecisionResponse)
def submit_decision(
    simulation_id: UUID,
    payload: DecisionRequest,
    engine: SimulationEngine = Depends(get_simulation_engine),
) -> DecisionResponse:
    outcome, state = engine.apply_decision(
        simulation_id=simulation_id,
        event_id=payload.event_id,
        choice_id=payload.choice_id,
    )

    if state.simulation_complete:
        return DecisionResponse(
            simulation_id=simulation_id,
            status="completed",
            outcome=outcome,
            state=state,
            next_event=None,
        )

    return DecisionResponse(
        simulation_id=simulation_id,
        status="in_progress",
        outcome=outcome,
        state=state,
        next_event=engine.get_current_event(simulation_id),
    )

