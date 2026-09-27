from fastapi import APIRouter, HTTPException, Response

from app.api.deps import audio_service

router = APIRouter(tags=["media"])


@router.get("/ambient-sound")
def get_ambient_sound() -> Response:
    audio_bytes = audio_service.get_ambient_sound()
    if audio_bytes is None:
        raise HTTPException(status_code=404, detail="Ambient sound not available")
    return Response(content=audio_bytes, media_type="audio/mpeg")
