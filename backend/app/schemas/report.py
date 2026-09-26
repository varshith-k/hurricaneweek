from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.simulation import ScoreState


class FinancialSummary(BaseModel):
    starting_cash: int = Field(ge=0)
    ending_cash: int = Field(ge=0)
    damage: int = Field(ge=0)


class FinalReport(BaseModel):
    simulation_id: UUID
    outcome: str
    scores: ScoreState
    financial_summary: FinancialSummary
    strengths: list[str]
    preparedness_gaps: list[str]
    action_identifiers: list[str]
    decision_history: list[dict[str, str]]

