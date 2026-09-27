from fastapi import APIRouter

from app.api.deps import plan_service
from app.schemas.comparison import CompareRunsRequest, CompareRunsResponse

router = APIRouter(tags=["comparison"])


@router.post("/coach/compare-runs", response_model=CompareRunsResponse)
def compare_runs(payload: CompareRunsRequest) -> dict:
    explanation = plan_service.generate_run_comparison(
        previous=payload.previous.model_dump(),
        current=payload.current.model_dump(),
    )
    return {"explanation": explanation}
