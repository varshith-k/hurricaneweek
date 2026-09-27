"""Readiness Assistant: emergency routing, verified answers, and Snowflake Cortex RAG.

Order of precedence for every question:
1. Emergency language -> fixed emergency guidance (never sent to an LLM).
2. A suggested question_id -> its verified answer.
3. Free text -> Snowflake Cortex RAG (or Gemini as a backup), accepted only if
   every number in the answer appears in the retrieved context.
4. Otherwise -> the closest verified answer, or a safe "can't answer" reply.
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

import httpx
from fastapi import HTTPException

from app.services.snowflake_service import (
    FactsRepository,
    SnowflakeClient,
    SnowflakeConfig,
    SnowflakeError,
    client_from_config,
    complete,
    display_sql,
    retrieve_chunks,
)

logger = logging.getLogger(__name__)

KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "data" / "assistant_knowledge.json"

LOCATION_LABEL = "Miami-Dade County, Florida"
AREA_NOTES = [
    "Low-lying and surrounded by water: storm surge and flooding drive most evacuation orders here.",
    "Evacuation zones are assigned by address; check Miami-Dade's Know Your Zone map before the season.",
    "Miami-Dade runs an Emergency and Evacuation Assistance Program for residents who need help leaving.",
]
EMERGENCY_NOTICE = (
    "If you or someone else is in danger right now, call 911. This assistant is for learning and planning; "
    "it cannot send help or give live storm information. For official updates, follow the National Hurricane "
    "Center and Miami-Dade County Emergency Management."
)
EMERGENCY_ANSWER = (
    "Call 911 now if you can. While you wait: if water is rising, move to the highest floor you can reach "
    "(not a closed attic; go to the roof only if you must) and signal for help with a light or bright cloth. "
    "Do not walk or drive into floodwater. If you smell gas or a generator is running indoors, get to fresh air "
    "immediately. This assistant cannot send help."
)
EMERGENCY_PATTERNS = [
    r"\btrapped\b",
    r"\bdrown",
    r"water (is )?(rising|coming in)",
    r"\bcan'?t breathe\b",
    r"\bunconscious\b",
    r"\bnot breathing\b",
    r"\bbleeding\b",
    r"\binjured\b",
    r"\bheart attack\b",
    r"\bchest pain\b",
    r"\bcarbon monoxide\b",
    r"\bon fire\b|\bfire in\b",
    r"\bcall 911\b",
    r"\bsos\b",
    r"\bhelp me\b",
    r"\bstuck (in|on) (the )?(water|roof|car|attic)\b",
]
SYSTEM_INSTRUCTIONS = (
    "You are the Hurricane Week Readiness Assistant for an educational hurricane-preparedness simulator set in "
    "Miami-Dade County, Florida. Answer the question using ONLY the numbered context below. If the context does "
    "not answer it, say you don't know and point to the National Hurricane Center, Miami-Dade County Emergency "
    "Management, or Ready.gov. Only use numbers that appear in the context. Never decide whether a specific "
    "insurance policy covers something; tell the person to check their policy. If someone may be in danger now, "
    "tell them to call 911. Reply in plain language in under 120 words, with no preamble."
)
MAX_HISTORY_TURNS = 4
ALWAYS_ALLOWED_NUMBERS = {"911"}
_NUMBER = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?%?")
_GREETING = re.compile(
    r"^\s*(h+i+|h+e+y+|h+e+l+l+o+|y+o+|howdy|good\s?(morning|afternoon|evening)|"
    r"thanks|thank you|o+k+(?:a+y+)?|c+o+o+l+)\s*[!.?]*\s*$",
    re.IGNORECASE,
)
GREETING_ANSWER = (
    "Hi! Ask me about hurricane prep for Miami-Dade - insurance, supplies, evacuation timing, and more. "
    "Try one of the suggested questions, or type your own."
)


def is_emergency(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in EMERGENCY_PATTERNS)


def is_greeting(text: str) -> bool:
    return bool(_GREETING.match(text))


def _numbers(text: str) -> set[str]:
    found = set()
    for match in _NUMBER.findall(text):
        cleaned = match.strip("$%").replace(",", "")
        try:
            value = float(cleaned)
        except ValueError:
            continue
        found.add(str(int(value)) if value.is_integer() else str(value))
    return found


def number_check(answer: str, context: str) -> bool:
    """Every number in the answer must appear in the context (rounded forms allowed)."""
    context_numbers = _numbers(context)
    rounded = {str(round(float(number))) for number in context_numbers}
    for number in _numbers(answer):
        if number in ALWAYS_ALLOWED_NUMBERS or number in context_numbers or number in rounded:
            continue
        return False
    return True


def _format_fact(fact: dict[str, Any]) -> str:
    value = fact.get("value_num")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{fact['label']}: {value} {fact.get('unit') or ''} (source: {fact.get('source')})".strip()


class AssistantService:
    def __init__(
        self,
        facts: FactsRepository | None = None,
        knowledge_path: Path = KNOWLEDGE_PATH,
        config_loader: Callable[[], SnowflakeConfig] = SnowflakeConfig.from_env,
        client_factory: Callable[[SnowflakeConfig], SnowflakeClient] = client_from_config,
        last_run_loader: Callable[[UUID], dict[str, Any] | None] | None = None,
    ) -> None:
        self.facts = facts or FactsRepository()
        self.knowledge = json.loads(knowledge_path.read_text(encoding="utf-8"))
        self._by_id = {entry["id"]: entry for entry in self.knowledge}
        self._config_loader = config_loader
        self._client_factory = client_factory
        self._last_run_loader = last_run_loader

    # --- context -----------------------------------------------------------------

    def _llm_mode(self) -> str:
        return os.getenv("ASSISTANT_LLM", "cortex").strip().lower()

    def powered_by(self, config: SnowflakeConfig, facts_count: int) -> dict[str, Any]:
        cortex_on = config.configured and self._llm_mode() == "cortex"
        return {
            "snowflake_configured": config.configured,
            "cortex_model": config.cortex_model if cortex_on else None,
            "embed_model": config.embed_model if cortex_on and config.rag_enabled else None,
            "rag_enabled": cortex_on and config.rag_enabled,
            "vector_search": cortex_on and config.rag_enabled,
            "facts_count": facts_count,
            "data_credit": "Snowflake Public Data · FEMA & NOAA",
            "gemini_backup": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        }

    def refresh_context(self) -> dict[str, Any]:
        config = self._config_loader()
        if not config.configured:
            cached = self.facts.load()
            return {**cached, "facts_count": len(cached["facts"]), "error": "Snowflake is not configured"}
        try:
            with self._client_factory(config) as client:
                live = self.facts.refresh(client, config.facts_table)
            return {**live, "facts_count": len(live["facts"]), "error": None}
        except SnowflakeError as exc:
            logger.warning("Snowflake facts refresh failed: %s", exc)
            cached = self.facts.load()
            return {**cached, "facts_count": len(cached["facts"]), "error": "Could not reach Snowflake; showing cached facts"}

    def real_world_context(self) -> list[dict[str, Any]]:
        return self.facts.load()["facts"]

    def _last_run(self, simulation_id: UUID | None) -> dict[str, Any] | None:
        if simulation_id is None or self._last_run_loader is None:
            return None
        try:
            return self._last_run_loader(simulation_id)
        except HTTPException:
            return None

    def _suggested(self, last_run: dict[str, Any] | None) -> list[dict[str, str]]:
        picks: list[dict[str, Any]] = []
        if last_run:
            actions = set(last_run.get("action_identifiers", []))
            picks = [entry for entry in self.knowledge if actions & set(entry.get("related_actions", []))]
        picks += [entry for entry in self.knowledge if entry.get("suggested") and entry not in picks]
        return [{"id": entry["id"], "question": entry["question"]} for entry in picks[:5]]

    def intro(self, simulation_id: UUID | None = None) -> dict[str, Any]:
        config = self._config_loader()
        facts = self.facts.load()
        last_run = self._last_run(simulation_id)
        return {
            "emergency_notice": EMERGENCY_NOTICE,
            "powered_by": self.powered_by(config, len(facts["facts"])),
            "location_label": LOCATION_LABEL,
            "area_notes": AREA_NOTES,
            "facts": facts["facts"],
            "facts_updated_at": facts["updated_at"],
            "facts_source": facts["source"],
            "last_run": last_run,
            "suggested_questions": self._suggested(last_run),
        }

    # --- answering -------------------------------------------------------------------

    def _verified(self, entry: dict[str, Any], note: str | None = None) -> dict[str, Any]:
        return {
            "kind": "verified",
            "answer": entry["answer"],
            "question_id": entry["id"],
            "sources": [entry["source"]],
            "note": note,
            "ai_meta": None,
        }

    def _keyword_match(self, question: str) -> dict[str, Any] | None:
        words = {word for word in re.findall(r"[a-z]{4,}", question.lower())}
        best, best_score = None, 0
        for entry in self.knowledge:
            entry_words = set(re.findall(r"[a-z]{4,}", f"{entry['question']} {entry['answer']}".lower()))
            score = len(words & entry_words)
            if score > best_score:
                best, best_score = entry, score
        return best if best_score >= 2 else None

    def _fallback(self, question: str, note: str) -> dict[str, Any]:
        entry = self._keyword_match(question)
        if entry:
            return self._verified(entry, note=note)
        return {
            "kind": "fallback",
            "answer": (
                "I can't answer that right now. Try one of the suggested questions, or check the National "
                "Hurricane Center, Miami-Dade County Emergency Management, or Ready.gov."
            ),
            "question_id": None,
            "sources": [],
            "note": note,
            "ai_meta": None,
        }

    def _prompt(self, question: str, chunks: list[dict[str, Any]], last_run: dict[str, Any] | None, history: list[dict[str, str]]) -> str:
        context = "\n".join(f"[{index}] ({chunk['source']}) {chunk['chunk']}" for index, chunk in enumerate(chunks, start=1))
        parts = [SYSTEM_INSTRUCTIONS, f"Context:\n{context or '(none)'}"]
        if last_run:
            parts.append(
                "Player's last simulated run (fictional, for personalizing advice): "
                f"outcome {last_run.get('outcome')}; gaps: {', '.join(last_run.get('preparedness_gaps', [])) or 'none'}."
            )
        if history:
            turns = "\n".join(f"{turn['role']}: {turn['content']}" for turn in history[-MAX_HISTORY_TURNS:])
            parts.append(f"Recent conversation (for context only):\n{turns}")
        parts.append(f"Question: {question}")
        return "\n\n".join(parts)

    def _local_chunks(self, question: str) -> list[dict[str, Any]]:
        """Keyword retrieval over verified content and cached facts (used by the Gemini backup)."""
        words = set(re.findall(r"[a-z]{4,}", question.lower()))
        candidates = [
            {"id": f"kb:{entry['id']}", "chunk": f"{entry['question']} {entry['answer']}", "source": f"Verified Hurricane Week content ({entry['status']})"}
            for entry in self.knowledge
        ] + [
            {"id": f"fact:{fact['id']}", "chunk": _format_fact(fact), "source": fact.get("source") or "Snowflake Public Data"}
            for fact in self.facts.load()["facts"]
        ]
        scored = []
        for candidate in candidates:
            overlap = len(words & set(re.findall(r"[a-z]{4,}", candidate["chunk"].lower())))
            if overlap:
                scored.append({**candidate, "score": float(overlap)})
        return sorted(scored, key=lambda chunk: chunk["score"], reverse=True)[:4]

    def _gemini(self, prompt: str) -> tuple[str, str]:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30.0,
        )
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        text = "".join(part.get("text", "") for part in candidates[0]["content"]["parts"]) if candidates else ""
        return text.strip(), model

    def _accept_or_fallback(self, question: str, answer: str, chunks: list[dict[str, Any]], meta: dict[str, Any]) -> dict[str, Any]:
        context = " ".join(chunk["chunk"] for chunk in chunks)
        passed = bool(answer) and number_check(answer, context)
        meta["number_check"] = "passed" if passed else "failed"
        if not passed:
            fallback = self._fallback(question, note="The AI answer included a number not found in the sources, so a verified answer is shown instead.")
            fallback["ai_meta"] = meta
            return fallback
        sources = list(dict.fromkeys(chunk["source"] for chunk in chunks))
        return {"kind": "ai", "answer": answer, "question_id": None, "sources": sources, "note": None, "ai_meta": meta}

    def ask(
        self,
        question: str | None = None,
        question_id: str | None = None,
        simulation_id: UUID | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        if question_id:
            entry = self._by_id.get(question_id)
            if entry is None:
                raise HTTPException(status_code=404, detail="Unknown question_id")
            return self._verified(entry)

        question = (question or "").strip()
        if not question:
            raise HTTPException(status_code=422, detail="Provide a question or question_id")
        if is_emergency(question):
            return {"kind": "emergency", "answer": EMERGENCY_ANSWER, "question_id": None, "sources": ["Emergency guidance: call 911"], "note": None, "ai_meta": None}
        if is_greeting(question):
            return {"kind": "greeting", "answer": GREETING_ANSWER, "question_id": None, "sources": [], "note": None, "ai_meta": None}

        history = (history or [])[-MAX_HISTORY_TURNS:]
        last_run = self._last_run(simulation_id)
        config = self._config_loader()
        mode = self._llm_mode()

        if mode == "cortex" and config.configured:
            started = time.monotonic()
            try:
                with self._client_factory(config) as client:
                    if config.rag_enabled:
                        chunks = retrieve_chunks(client, config, question)
                        provider = "snowflake-cortex-rag"
                    else:
                        chunks = self._local_chunks(question)
                        provider = "snowflake-cortex"
                    answer = complete(client, config.cortex_model, self._prompt(question, chunks, last_run, history))
                meta = {
                    "provider": provider,
                    "model": config.cortex_model,
                    "embed_model": config.embed_model if config.rag_enabled else None,
                    "retrieved": [{"id": chunk["id"], "source": chunk["source"], "score": chunk["score"]} for chunk in chunks],
                    "latency_ms": int((time.monotonic() - started) * 1000),
                    "sql_statement": display_sql(config),
                }
                return self._accept_or_fallback(question, answer, chunks, meta)
            except SnowflakeError as exc:
                logger.warning("Snowflake Cortex answer failed: %s", exc)

        if os.getenv("GEMINI_API_KEY", "").strip() and mode in {"cortex", "gemini"}:
            started = time.monotonic()
            chunks = self._local_chunks(question)
            try:
                answer, model = self._gemini(self._prompt(question, chunks, last_run, history))
                meta = {
                    "provider": "gemini",
                    "model": model,
                    "embed_model": None,
                    "retrieved": [{"id": chunk["id"], "source": chunk["source"], "score": chunk["score"]} for chunk in chunks],
                    "latency_ms": int((time.monotonic() - started) * 1000),
                    "sql_statement": None,
                }
                return self._accept_or_fallback(question, answer, chunks, meta)
            except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
                logger.warning("Gemini backup answer failed: %s", type(exc).__name__)

        return self._fallback(question, note="The AI assistant is unavailable, so the closest verified answer is shown.")
