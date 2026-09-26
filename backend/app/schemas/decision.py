from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.event import EventResponse
from app.schemas.report import FinalReport
from app.schemas.simulation import SimulationState


class DecisionRequest(BaseModel):
    event_id: str = Field(min_length=1)
    choice_id: str = Field(min_length=1)


class DecisionOutcome(BaseModel):
    consequence: str
    preparedness_delta: int
    timing_delta: int
    cash_delta: int


DecisionStatus = Literal["in_progress", "completed"]


class DecisionResponse(BaseModel):
    simulation_id: UUID
    status: DecisionStatus
    outcome: DecisionOutcome
    state: SimulationState
    next_event: EventResponse | None
    final_report: FinalReport | None = None
