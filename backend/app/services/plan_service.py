import json
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

    def generate_coach_summary(
        self,
        outcome: str,
        overall_score: int,
        preparedness_gaps: list[str],
        strengths: list[str],
        decision_history: list[dict],
    ) -> dict | None:
        if not self.enabled:
            return None

        history_lines = "\n".join(
            f"- {item['stage']}: chose to {item['choice_id'].replace('_', ' ')} -> {item['consequence']}"
            for item in decision_history
        )
        gaps_text = ", ".join(preparedness_gaps) if preparedness_gaps else "none identified"
        strengths_text = ", ".join(strengths) if strengths else "none identified"

        prompt = (
            "You are a calm, practical hurricane-preparedness coach reviewing one player's run of a "
            "hurricane-week decision simulation game. Based on their actual choices below, identify: "
            "the single decision that hurt them most, the single decision that helped them most, and "
            "one concrete change for next time. Be specific to their actual choices, not generic advice. "
            "Second person, one sentence each, no headers or markdown.\n\n"
            f"Outcome: {outcome}\n"
            f"Overall readiness score: {overall_score}/100\n"
            f"Preparedness gaps identified: {gaps_text}\n"
            f"Strengths identified: {strengths_text}\n"
            f"Decisions made during the simulation:\n{history_lines}\n\n"
            "Respond with ONLY a JSON object with exactly these keys: "
            '"biggest_mistake", "best_decision", "what_to_change". No other text.'
        )

        try:
            response = httpx.post(
                GENERATE_URL_TEMPLATE.format(model=self.model),
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json"},
                },
                timeout=20.0,
            )
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            parsed = json.loads(text)
            summary = {
                "biggest_mistake": str(parsed["biggest_mistake"]).strip(),
                "best_decision": str(parsed["best_decision"]).strip(),
                "what_to_change": str(parsed["what_to_change"]).strip(),
            }
            if not all(summary.values()):
                return None
            return summary
        except httpx.HTTPStatusError as exc:
            logger.warning("Gemini coach summary failed: %s - %s", exc.response.status_code, exc.response.text)
            return None
        except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.warning("Gemini coach summary failed: %s", exc)
            return None
