from pydantic import BaseModel


class CoverageEntry(BaseModel):
    id: str
    label: str
    wind: str
    flood: str
    action: str
    source: str


class CoverageResponse(BaseModel):
    disclaimer: str
    entries: list[CoverageEntry]
