"""Deepgram Flux WebSocket STT"""
import json
import asyncio
import websockets
import os
from typing import AsyncGenerator

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen?model=flux&language=en-AU&punctuate=true&interim_results=true&encoding=linear16&sample_rate=16000"


async def stt_stream(audio_queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Stream audio to Deepgram and yield transcripts"""
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}

    async with websockets.connect(DEEPGRAM_URL, extra_headers=headers) as ws:
        async def sender():
            while True:
                chunk = await audio_queue.get()
                if chunk is None:
                    break
                await ws.send(chunk)
            await ws.send(json.dumps({"type": "CloseStream"}))

        async def receiver():
            async for msg in ws:
                data = json.loads(msg)
                if "channel" in data:
                    transcript = data["channel"]["alternatives"][0]["transcript"]
                    if transcript:
                        yield transcript

        # Run sender and receiver concurrently
        sender_task = asyncio.create_task(sender())
        async for transcript in receiver():
            yield transcript
        await sender_task