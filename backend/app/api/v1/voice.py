"""
Voice API router — live conversation (STT + TTS + dialogue).

* POST /voice/stt      audio upload  → transcript (Groq Whisper)
* POST /voice/tts      text + lang   → MP3 audio (Edge TTS)
* POST /voice/converse one dialogue turn → reply + updated profile/phase

All routes sit behind the existing API-key + rate-limit middleware.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from backend.app.core.logging_config import get_logger
from backend.app.core.security import require_api_key
from backend.app.models.dtos import ConverseRequest, ConverseResponse, TTSRequest
from backend.app.services import speech
from backend.app.services.providers import get_conversation_engine

logger = get_logger("api.voice")

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/voice/stt")
async def stt(
    file: UploadFile = File(...),
    language: str = Form("English"),
):
    """Transcribe an uploaded audio clip to text."""
    audio = await file.read()
    if not audio:
        raise HTTPException(status_code=400, detail="Empty audio upload")
    try:
        text = speech.transcribe(
            audio, filename=file.filename or "audio.webm", language=language
        )
    except Exception as e:
        logger.error(f"STT failed: {e}")
        raise HTTPException(status_code=500, detail=f"STT failed: {e}")
    return {"text": text}


@router.post("/voice/tts")
async def tts(req: TTSRequest):
    """Synthesize text to speech and return MP3 audio."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    try:
        audio = await speech.synthesize(req.text, req.language)
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")
    return Response(content=audio, media_type="audio/mpeg")


@router.post("/voice/converse", response_model=ConverseResponse)
async def converse(req: ConverseRequest):
    """Advance the live conversation by one turn."""
    engine = get_conversation_engine()
    try:
        result = engine.converse(
            user_message=req.message,
            profile=req.profile,
            history=req.history,
            phase=req.phase,
            language=req.language,
        )
    except Exception as e:
        logger.error(f"converse failed: {e}")
        raise HTTPException(status_code=500, detail=f"converse failed: {e}")
    return ConverseResponse(**result)
