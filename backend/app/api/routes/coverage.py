import json
from pathlib import Path

from fastapi import APIRouter

from app.schemas.coverage import CoverageResponse

router = APIRouter(tags=["coverage"])

COVERAGE_PATH = Path(__file__).resolve().parents[3] / "app" / "data" / "coverage_lookup.json"
_entries = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))


@router.get("/coverage-check", response_model=CoverageResponse)
def coverage_check() -> dict:
    return {
        "disclaimer": "General education based on typical policy language, not a coverage determination for your specific policy - always confirm exact terms with your insurer or agent.",
        "entries": _entries,
    }
