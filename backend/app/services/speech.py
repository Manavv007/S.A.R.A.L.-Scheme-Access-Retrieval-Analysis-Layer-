"""
Voice services for the live conversation feature.

* Speech-to-text via Groq's hosted ``whisper-large-v3`` (free tier, reuses the
  existing GROQ_API_KEY; strong on Indian languages + accents).
* Text-to-speech via Microsoft Edge's neural voices through the free
  ``edge-tts`` library (no API key; needs outbound network).

Both accept the backend language *name* ("Hindi", "Gujarati", …) to stay
consistent with ``UserProfile.language``.
"""

from backend.app.core.logging_config import get_logger

logger = get_logger("speech")

# Backend language name → ISO 639-1 code (used for Whisper hint + voice pick).
LANG_NAME_TO_CODE = {
    "English": "en",
    "Hindi": "hi",
    "Gujarati": "gu",
    "Telugu": "te",
    "Marathi": "mr",
    "Tamil": "ta",
}

# ISO code → Edge TTS neural voice (all India locales).
EDGE_VOICES = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural",
    "gu": "gu-IN-DhwaniNeural",
    "te": "te-IN-ShrutiNeural",
    "mr": "mr-IN-AarohiNeural",
    "ta": "ta-IN-PallaviNeural",
}

STT_MODEL = "whisper-large-v3"


def _code(language: str | None) -> str | None:
    """Map a backend language name to its ISO code, or None if unknown."""
    if not language:
        return None
    return LANG_NAME_TO_CODE.get(language.strip())


def transcribe(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    language: str | None = None,
) -> str:
    """Transcribe recorded audio to text via Groq Whisper.

    ``language`` is the backend language name (e.g. "Hindi"); when recognized
    it is passed as an ISO hint to improve accuracy, otherwise Whisper
    auto-detects.
    """
    from backend.app.services.providers import get_groq_client

    client = get_groq_client()
    kwargs: dict = {
        "file": (filename, audio_bytes),
        "model": STT_MODEL,
        "response_format": "text",
    }
    code = _code(language)
    if code:
        kwargs["language"] = code

    result = client.audio.transcriptions.create(**kwargs)
    # response_format="text" yields a plain string; be defensive anyway.
    if isinstance(result, str):
        return result.strip()
    return str(getattr(result, "text", result)).strip()


async def synthesize(text: str, language: str | None = None) -> bytes:
    """Synthesize ``text`` to MP3 audio bytes via Edge TTS neural voices."""
    import edge_tts

    code = _code(language) or "en"
    voice = EDGE_VOICES.get(code, EDGE_VOICES["en"])

    communicate = edge_tts.Communicate(text, voice)
    buffer = bytearray()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio" and chunk.get("data"):
            buffer.extend(chunk["data"])
    return bytes(buffer)
