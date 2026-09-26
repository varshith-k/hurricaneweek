from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class EventChoice(BaseModel):
    choice_id: str = Field(min_length=1)
    label: str = Field(min_length=1)


class EventResponse(BaseModel):
    simulation_id: UUID
    event_id: str
    stage: str
    title: str
    description: str
    choices: list[EventChoice]
    simulation_complete: bool = False
