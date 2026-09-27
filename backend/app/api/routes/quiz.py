import json
from pathlib import Path

from fastapi import APIRouter

from app.schemas.quiz import QuizResponse

router = APIRouter(tags=["quiz"])

QUIZ_PATH = Path(__file__).resolve().parents[3] / "app" / "data" / "auto_insurance_quiz.json"
_questions = json.loads(QUIZ_PATH.read_text(encoding="utf-8"))


@router.get("/quiz/auto-insurance", response_model=QuizResponse)
def auto_insurance_quiz() -> dict:
    return {
        "title": "Auto Insurance Readiness Quiz",
        "disclaimer": "General education, not coverage advice - check your own policy for exact terms.",
        "questions": _questions,
    }
