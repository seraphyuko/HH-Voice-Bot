import io
from gtts import gTTS

def generate_myanmar_speech(text: str) -> io.BytesIO:
    """Converts Myanmar text into a voice audio byte buffer."""
    tts = gTTS(text=text, lang='my')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    audio_bytes.name = "voice.ogg"
    return audio_bytes