from uuid import UUID

from fastapi import APIRouter

from app.api.deps import assistant_service
from app.schemas.assistant import AskRequest, AskResponse, ContextRefreshResponse, IntroResponse

router = APIRouter(tags=["assistant"])


@router.get("/assistant/intro", response_model=IntroResponse)
def assistant_intro(simulation_id: UUID | None = None) -> dict:
    return assistant_service.intro(simulation_id)


@router.post("/assistant/ask", response_model=AskResponse)
def assistant_ask(payload: AskRequest) -> dict:
    return assistant_service.ask(
        question=payload.question,
        question_id=payload.question_id,
        simulation_id=payload.simulation_id,
        history=[turn.model_dump() for turn in payload.history],
    )


@router.post("/context/refresh", response_model=ContextRefreshResponse)
def refresh_context() -> dict:
    return assistant_service.refresh_context()
