import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.5-flash-lite"  # fast, non-reasoning model - "flash-latest" defaults to extended thinking (5-10s+ per call)
GENERATE_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _history_lines(decision_history: list[dict]) -> str:
    return "\n".join(
        f"- {item['stage']}: chose to {str(item['choice_id']).replace('_', ' ')} -> {item.get('consequence', '')}"
        for item in decision_history
    )


class PlanService:
    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self.enabled = bool(self.api_key)

    def _call_gemini_json(self, prompt: str, log_label: str) -> dict | None:
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
            return json.loads(text)
        except httpx.HTTPStatusError as exc:
            logger.warning("%s failed: %s - %s", log_label, exc.response.status_code, exc.response.text)
            return None
        except (httpx.HTTPError, KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.warning("%s failed: %s", log_label, exc)
            return None

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
            f"Decisions made during the simulation:\n{_history_lines(decision_history)}\n\n"
            "Respond with ONLY a JSON object with exactly these keys: "
            '"biggest_mistake", "best_decision", "what_to_change". No other text.'
        )

        parsed = self._call_gemini_json(prompt, "Gemini coach summary")
        if parsed is None:
            return None
        try:
            summary = {
                "biggest_mistake": str(parsed["biggest_mistake"]).strip(),
                "best_decision": str(parsed["best_decision"]).strip(),
                "what_to_change": str(parsed["what_to_change"]).strip(),
            }
        except KeyError:
            return None
        return summary if all(summary.values()) else None

    def generate_run_comparison(self, previous: dict, current: dict) -> str | None:
        if not self.enabled:
            return None

        prompt = (
            "You are a calm, practical hurricane-preparedness coach. A player just completed a second "
            "run of a hurricane-week decision simulation game, having already played once before. "
            "Compare their previous run to their current run and explain, in 2-3 sentences, second "
            "person, no headers or markdown, which specific decisions changed and why that moved their "
            "score. If the score got worse, say so plainly - don't only praise improvement.\n\n"
            f"Previous run - outcome: {previous['outcome']}, overall score: {previous['overall_score']}/100\n"
            f"Previous decisions:\n{_history_lines(previous['decision_history'])}\n\n"
            f"Current run - outcome: {current['outcome']}, overall score: {current['overall_score']}/100\n"
            f"Current decisions:\n{_history_lines(current['decision_history'])}\n\n"
            'Respond with ONLY a JSON object with exactly this key: "explanation". No other text.'
        )

        parsed = self._call_gemini_json(prompt, "Gemini run comparison")
        if parsed is None:
            return None
        try:
            explanation = str(parsed["explanation"]).strip()
        except KeyError:
            return None
        return explanation or None
