import logging
import os
from threading import Lock
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # "George" - warm storyteller tone, free-tier accessible
TTS_URL_TEMPLATE = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
SOUND_GENERATION_URL = "https://api.elevenlabs.io/v1/sound-generation"
AMBIENT_SOUND_PROMPT = "Ominous hurricane wind and heavy rain, looping ambient background sound, low rumble, no music"


class AudioService:
    def __init__(self) -> None:
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
        self.enabled = bool(self.api_key)
        self._cache: dict[UUID, bytes] = {}
        self._lock = Lock()
        self._ambient_sound_cache: bytes | None = None

    def get_cached_narration(self, simulation_id: UUID) -> bytes | None:
        with self._lock:
            return self._cache.get(simulation_id)

    def synthesize_narration(self, simulation_id: UUID, text: str) -> bytes | None:
        if not self.enabled:
            return None

        cached = self.get_cached_narration(simulation_id)
        if cached is not None:
            return cached

        try:
            response = httpx.post(
                TTS_URL_TEMPLATE.format(voice_id=self.voice_id),
                headers={"xi-api-key": self.api_key, "Accept": "audio/mpeg"},
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
                timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("ElevenLabs TTS request failed: %s - %s", exc.response.status_code, exc.response.text)
            return None
        except httpx.HTTPError as exc:
            logger.warning("ElevenLabs TTS request failed: %s", exc)
            return None

        audio_bytes = response.content
        with self._lock:
            self._cache[simulation_id] = audio_bytes
        return audio_bytes

    def get_ambient_sound(self) -> bytes | None:
        if not self.enabled:
            return None

        with self._lock:
            if self._ambient_sound_cache is not None:
                return self._ambient_sound_cache

        try:
            response = httpx.post(
                SOUND_GENERATION_URL,
                headers={"xi-api-key": self.api_key, "Accept": "audio/mpeg"},
                json={"text": AMBIENT_SOUND_PROMPT, "duration_seconds": 20},
                timeout=30.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("ElevenLabs sound generation failed: %s - %s", exc.response.status_code, exc.response.text)
            return None
        except httpx.HTTPError as exc:
            logger.warning("ElevenLabs sound generation failed: %s", exc)
            return None

        audio_bytes = response.content
        with self._lock:
            self._ambient_sound_cache = audio_bytes
        return audio_bytes


def compose_narration_text(outcome: str, overall_score: int, strengths: list[str], decision_count: int, ending_cash: int) -> str:
    strengths_text = " ".join(strengths[:2]) if strengths else "You made it through the storm."
    return (
        f"Hurricane Week debrief. Your outcome: {outcome}, with an overall readiness score of "
        f"{overall_score} out of 100. {strengths_text} You made {decision_count} decisions during "
        f"the storm and ended with {ending_cash} dollars on hand."
    )
