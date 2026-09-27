from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.simulation import ScoreState


class FinancialSummary(BaseModel):
    starting_cash: int = Field(ge=0)
    ending_cash: int = Field(ge=0)
    damage: int = Field(ge=0)


class CoachSummary(BaseModel):
    biggest_mistake: str
    best_decision: str
    what_to_change: str


class FinalReport(BaseModel):
    simulation_id: UUID
    outcome: str
    scores: ScoreState
    financial_summary: FinancialSummary
    strengths: list[str]
    preparedness_gaps: list[str]
    action_identifiers: list[str]
    decision_history: list[dict[str, str]]
    audio_url: str | None = None
    coach_summary: CoachSummary | None = None
    solana_tx_url: str | None = None
    real_world_context: list[dict] = Field(default_factory=list)

