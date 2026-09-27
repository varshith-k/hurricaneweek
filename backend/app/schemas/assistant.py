from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class AskRequest(BaseModel):
    question: str | None = Field(default=None, max_length=500)
    question_id: str | None = Field(default=None, max_length=100)
    simulation_id: UUID | None = None
    history: list[ChatTurn] = Field(default_factory=list, max_length=8)


class RetrievedChunk(BaseModel):
    id: str
    source: str
    score: float


class AiMeta(BaseModel):
    provider: Literal["snowflake-cortex-rag", "snowflake-cortex", "gemini"]
    model: str
    embed_model: str | None = None
    retrieved: list[RetrievedChunk] = Field(default_factory=list)
    latency_ms: int
    sql_statement: str | None = None
    number_check: Literal["passed", "failed"]


class AskResponse(BaseModel):
    kind: Literal["emergency", "verified", "ai", "fallback", "greeting"]
    answer: str
    question_id: str | None = None
    sources: list[str]
    note: str | None = None
    ai_meta: AiMeta | None = None


class Fact(BaseModel):
    id: str
    label: str
    value_num: float | None
    unit: str | None = None
    source: str | None = None
    note: str | None = None


class PoweredBy(BaseModel):
    snowflake_configured: bool
    cortex_model: str | None
    embed_model: str | None
    rag_enabled: bool
    vector_search: bool
    facts_count: int
    data_credit: str
    gemini_backup: bool


class SuggestedQuestion(BaseModel):
    id: str
    question: str


class LastRun(BaseModel):
    simulation_id: UUID
    status: Literal["active", "completed"]
    stage: str
    outcome: str | None = None
    overall_score: int
    preparedness_gaps: list[str] = Field(default_factory=list)
    action_identifiers: list[str] = Field(default_factory=list)


class IntroResponse(BaseModel):
    emergency_notice: str
    powered_by: PoweredBy
    location_label: str
    area_notes: list[str]
    facts: list[Fact]
    facts_updated_at: str | None
    facts_source: Literal["snowflake-live", "cache", "none"]
    last_run: LastRun | None
    suggested_questions: list[SuggestedQuestion]


class ContextRefreshResponse(BaseModel):
    source: Literal["snowflake-live", "cache", "none"]
    facts_count: int
    facts: list[Fact]
    updated_at: str | None
    error: str | None = None
