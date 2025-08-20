from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import base64
import logging

from ..services.ttsService import TTSService
from ..utils.timeUtils import TimeUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["tts"])

tts_service = TTSService()

audio_cache: Dict[str, Dict[str, Any]] = {}

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: Optional[str] = Field(None)
    speed: Optional[str] = Field("normal", description="'normal' or 'slow'")
    voice: Optional[str] = Field(None, description="Reserved for future multi-voice support")

@router.post("/")
async def synthesize_speech(request: TTSRequest):
    try:
        slow = True if (request.speed or "normal").lower() == "slow" else False
        result = await tts_service.convert_text_to_speech(
            text=request.text,
            language=request.language,
            slow=slow
        )
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "TTS failed"))
        audio_b64 = base64.b64encode(result["audio_data"]).decode("utf-8")
        audio_id = f"audio_{TimeUtils().get_current_timestamp()}"
        audio_payload = {
            "audio_id": audio_id,
            "audio_data": audio_b64,
            "format": result.get("format", "mp3"),
            "duration": result.get("estimated_duration_seconds", None),
            "file_size": result.get("audio_size", len(result["audio_data"]))
        }
        audio_cache[audio_id] = audio_payload
        return audio_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS synthesis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("")
async def synthesize_speech_root(request: TTSRequest):
    return await synthesize_speech(request)

@router.get("/languages")
async def list_languages():
    res = await tts_service.get_available_languages()
    return res

@router.get("/health")
async def health():
    res = await tts_service.health_check()
    return res

@router.get("/audio/{audio_id}")
async def get_audio(audio_id: str):
    item = audio_cache.get(audio_id)
    if not item:
        raise HTTPException(status_code=404, detail="Audio not found")
    return item
