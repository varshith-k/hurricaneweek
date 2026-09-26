from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


HousingType = Literal["apartment", "house", "mobile_home"]
TransportType = Literal["car", "scooter", "public_transit"]


class PlayerProfile(BaseModel):
    cash_on_hand: int = Field(ge=0, le=100_000)
    has_insurance: bool = False
    housing_type: HousingType
    transport_type: TransportType
    household_size: int = Field(default=1, ge=1, le=10)


class SimulationCreateRequest(BaseModel):
    player_profile: PlayerProfile


class ScoreState(BaseModel):
    safety: int = Field(ge=0, le=100)
    financial: int = Field(ge=0, le=100)
    preparedness: int = Field(ge=0, le=100)
    timing: int = Field(ge=0, le=100)


class SimulationState(BaseModel):
    day_index: int = Field(ge=0, le=5)
    simulation_complete: bool
    cash_remaining: int = Field(ge=0)
    preparedness_points: int = Field(ge=0)
    risk_points: int = Field(ge=0)
    scores: ScoreState


class SimulationCreateResponse(BaseModel):
    simulation_id: UUID
    state: SimulationState

