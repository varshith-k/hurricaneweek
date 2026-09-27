from pydantic import BaseModel


class RunSummary(BaseModel):
    outcome: str
    overall_score: int
    scores: dict[str, int]
    decision_history: list[dict]
    financial_summary: dict


class CompareRunsRequest(BaseModel):
    previous: RunSummary
    current: RunSummary


class CompareRunsResponse(BaseModel):
    explanation: str | None = None
