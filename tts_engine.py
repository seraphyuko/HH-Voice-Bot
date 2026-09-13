import io
import asyncio
import edge_tts

# Define two different voice models for Myanmar
VOICE_CLASSIC = "my-MM-NilarNeural"  # Standard Female Voice
VOICE_CLONE = "my-MM-ThihaNeural"    # Premium / Alternative Male Voice

async def generate_myanmar_speech(text: str, engine_type: str = "classic") -> io.BytesIO:
    """Converts Myanmar text into audio bytes using different neural voices."""
    
    # Pick the voice target based on selected engine
    selected_voice = VOICE_CLONE if engine_type == "clone" else VOICE_CLASSIC

    communicate = edge_tts.Communicate(text, selected_voice)
    audio_bytes = io.BytesIO()

    # Stream audio chunks into memory buffer
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes.write(chunk["data"])

    audio_bytes.seek(0)
    audio_bytes.name = "voice.ogg"
    return audio_bytes