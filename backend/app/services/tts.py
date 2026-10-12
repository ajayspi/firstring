"""ElevenLabs TTS streaming"""
import httpx
import os
from typing import AsyncGenerator

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel
BASE_URL = "https://api.elevenlabs.io/v1"


async def tts_stream(text: str) -> AsyncGenerator[bytes, None]:
    """Stream TTS audio from ElevenLabs"""
    url = f"{BASE_URL}/text-to-speech/{VOICE_ID}/stream"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            async for chunk in response.aiter_bytes():
                yield chunk