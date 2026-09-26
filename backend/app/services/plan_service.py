import logging
import os

import httpx

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.5-flash-lite"  # fast, non-reasoning model - "flash-latest" defaults to extended thinking (5-10s+ per call)
GENERATE_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class PlanService:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self.enabled = bool(self.api_key)

    def generate_plan(
        self,
        outcome: str,
        overall_score: int,
        preparedness_gaps: list[str],
        decision_history: list[dict],
    ) -> str | None:
        if not self.enabled:
            return None

        history_lines = "\n".join(
            f"- {item['stage']}: chose to {item['choice_id'].replace('_', ' ')} -> {item['consequence']}"
            for item in decision_history
        )
        gaps_text = ", ".join(preparedness_gaps) if preparedness_gaps else "none identified"

        prompt = (
            "You are a calm, practical hurricane-preparedness coach. A player just finished a "
            "hurricane-week decision simulation game. Based on their choices below, write a short "
            "(3-4 sentences, second person, no headers or bullet points) action plan for what they "
            "should do differently before the next real storm season. Be concrete and specific to "
            "their actual choices, not generic advice.\n\n"
            f"Outcome: {outcome}\n"
            f"Overall readiness score: {overall_score}/100\n"
            f"Preparedness gaps identified: {gaps_text}\n"
            f"Decisions made during the simulation:\n{history_lines}\n"
        )

        try:
            response = httpx.post(
                GENERATE_URL_TEMPLATE.format(model=self.model),
                params={"key": self.api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=20.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except httpx.HTTPStatusError as exc:
            logger.warning("Gemini plan generation failed: %s - %s", exc.response.status_code, exc.response.text)
            return None
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            logger.warning("Gemini plan generation failed: %s", exc)
            return None
