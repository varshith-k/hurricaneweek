from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import audio_service, get_simulation_engine
from app.schemas.decision import DecisionRequest, DecisionResponse
from app.schemas.report import FinalReport
from app.schemas.simulation import SimulationCreateRequest, SimulationCreateResponse, SimulationTelemetryRow
from app.services.simulation_engine import SimulationEngine

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("", response_model=SimulationCreateResponse, status_code=201)
def create_simulation(
    payload: SimulationCreateRequest,
    engine: SimulationEngine = Depends(get_simulation_engine),
) -> SimulationCreateResponse:
    state = engine.create_simulation(payload.player_profile)
    return SimulationCreateResponse(simulation_id=state["simulation_id"], state=engine.get_state(state["simulation_id"]))


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
    request: Request,
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
            final_report=engine.build_final_report(simulation_id, base_url=str(request.base_url)),
        )

    return DecisionResponse(
        simulation_id=simulation_id,
        status="in_progress",
        outcome=outcome,
        state=state,
        next_event=engine.get_current_event(simulation_id),
    )


@router.get("/{simulation_id}/report", response_model=FinalReport)
def get_final_report(
    simulation_id: UUID,
    request: Request,
    engine: SimulationEngine = Depends(get_simulation_engine),
) -> FinalReport:
    return engine.build_final_report(simulation_id, base_url=str(request.base_url))


@router.get("/{simulation_id}/audio")
def get_final_report_audio(simulation_id: UUID) -> Response:
    audio_bytes = audio_service.get_cached_narration(simulation_id)
    if audio_bytes is None:
        raise HTTPException(status_code=404, detail="Narration audio not available for this simulation")
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.get("/{simulation_id}/timeline", response_model=list[SimulationTelemetryRow])
def get_simulation_timeline(
    simulation_id: UUID,
    engine: SimulationEngine = Depends(get_simulation_engine),
):
    return engine.get_timeline(simulation_id)

