from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class EventChoice(BaseModel):
    choice_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    cost: int = Field(ge=0)


class EventResponse(BaseModel):
    simulation_id: UUID
    event_id: str
    day_index: int = Field(ge=0, le=5)
    title: str
    description: str
    choices: list[EventChoice]
    simulation_complete: bool = False

