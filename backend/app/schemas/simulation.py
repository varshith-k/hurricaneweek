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
    needs_refrigerated_medication: bool = False


class SimulationCreateRequest(BaseModel):
    player_profile: PlayerProfile


class ScoreState(BaseModel):
    safety: int = Field(ge=0, le=100)
    financial: int = Field(ge=0, le=100)
    preparedness: int = Field(ge=0, le=100)
    timing: int = Field(ge=0, le=100)
    overall: int = Field(ge=0, le=100)


class StormState(BaseModel):
    stage: str
    wind_mph: int = Field(ge=0)
    flood_risk: float = Field(ge=0, le=1)


class SimulationState(BaseModel):
    stage: str
    status: Literal["active", "completed"]
    simulation_complete: bool
    cash: int = Field(ge=0)
    food_days: int = Field(ge=0)
    water_days: int = Field(ge=0)
    evacuated: bool
    scooter_protected: bool
    documents_secured: bool
    insurance_verified: bool
    transport_available: bool
    preparedness_points: int = Field(ge=0)
    timing_points: int = Field(ge=0)
    financial_loss: int = Field(ge=0)
    completed_events: list[str]
    storm: StormState
    scores: ScoreState


class SimulationCreateResponse(BaseModel):
    simulation_id: UUID
    state: SimulationState
