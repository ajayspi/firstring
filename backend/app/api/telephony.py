"""Telephony webhooks (§C.10 PUBLIC): verify → dedupe → enqueue → 200.

No business logic inline — the receiver's only job is to durably enqueue.
"""
import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.services import webhooks as wh

router = APIRouter()


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


async def _receive(provider: str, kind: str, request: Request) -> JSONResponse:
    raw = await request.body()
    if not wh.verify_signature(provider, raw, request.headers.get("x-webhook-signature", "")):
        return _err(401, "signature_invalid", "bad webhook signature")
    try:
        body = json.loads(raw or b"{}")
        event_id = body["event_id"]
    except (ValueError, KeyError):
        return _err(422, "validation_error", "body needs event_id")
    if not wh.dedupe(provider, event_id):
        return JSONResponse(status_code=200, content={"status": "duplicate"})
    wh.enqueue(
        {"provider": provider, "kind": kind, "event_id": event_id,
         "status": "received", "attempts": 0, "payload": body}
    )
    return JSONResponse(status_code=200, content={"status": "received"})


@router.post("/webhooks/telephony/{provider}/call")
async def telephony_call(provider: str, request: Request):
    return await _receive(provider, "call", request)


@router.post("/webhooks/telephony/{provider}/status")
async def telephony_status(provider: str, request: Request):
    return await _receive(provider, "status", request)


@router.post("/webhooks/telephony/{provider}/recording")
async def telephony_recording(provider: str, request: Request):
    return await _receive(provider, "recording", request)
