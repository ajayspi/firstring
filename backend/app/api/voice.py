"""Voice API — Telnyx webhook + LiveKit call handler"""
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import httpx

router = APIRouter()


class TelnyxWebhook(BaseModel):
    event_type: str
    payload: dict


class LiveKitStart(BaseModel):
    restaurant_id: str
    call_sid: str
    caller_number: str


@router.post("/webhook")
async def telnyx_webhook(request: Request):
    """Handle incoming Telnyx webhooks"""
    body = await request.json()
    event_type = body.get("event_type")
    payload = body.get("payload", {})

    if event_type == "call.initiated":
        # Call started - create LiveKit room and dispatch agent
        call_sid = payload.get("call_control_id")
        caller_number = payload.get("from", {}).get("phone_number")
        # TODO: Create LiveKit room, dispatch agent
        return {"status": "ok"}

    elif event_type == "call.answered":
        # Call answered - agent should be connected
        return {"status": "ok"}

    elif event_type == "call.hangup":
        # Call ended - cleanup
        call_sid = payload.get("call_control_id")
        # TODO: Save call transcript, finalize order
        return {"status": "ok"}

    return {"status": "ignored"}


@router.post("/livekit-agent-start")
async def start_livekit_agent(data: LiveKitStart):
    """Start LiveKit agent for a call"""
    # TODO: Dispatch LiveKit agent to room
    return {"status": "agent_started", "room": f"call_{data.call_sid}"}


@router.post("/stt")
async def stt_stream():
    """WebSocket endpoint for Deepgram STT streaming"""
    # Handled by LiveKit agent
    pass