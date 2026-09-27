from pydantic import BaseModel


class EvacuationRoute(BaseModel):
    available: bool
    origin_label: str | None = None
    shelter_name: str | None = None
    shelter_area: str | None = None
    transport_mode: str | None = None
    distance_km: float | None = None
    duration_min: float | None = None
    feasibility: str | None = None
    warning: str | None = None
    note: str
