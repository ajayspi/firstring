"""Calls routes (§C.6 pilot slice): list, get, transcript, recording redirect.

In-memory call store — staging wires calls table populated by T1.2 webhook.
Recording URLs are S3 redirects (302).
"""
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse, RedirectResponse

from app.services import auth as auth_svc

router = APIRouter()

# ponytail: per-user call history. Staging: query calls table by owner_id.
_calls: dict = {}


def reset() -> None:
    _calls.clear()


def _user(authorization: str) -> str | None:
    if not authorization.startswith("Bearer "):
        return None
    sub = auth_svc.verify_access(authorization[7:])
    return sub if isinstance(sub, str) else None


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


@router.get("/calls")
def list_calls(authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    items = _calls.get(user, [])
    return {"items": items}


@router.get("/calls/{call_id}")
def get_call(call_id: str, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    for call in _calls.get(user, []):
        if call.get("id") == call_id:
            return call
    return _err(404, "not_found", f"call {call_id} not found")


@router.get("/calls/{call_id}/transcript")
def get_transcript(call_id: str, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    for call in _calls.get(user, []):
        if call.get("id") == call_id:
            return {"segments": call.get("transcript", [])}
    return _err(404, "not_found", f"call {call_id} not found")


@router.get("/calls/{call_id}/recording")
def recording_redirect(call_id: str, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    for call in _calls.get(user, []):
        if call.get("id") == call_id:
            url = f"s3://firstring-recordings/{user}/{call_id}.wav"
            return RedirectResponse(url=url, status_code=302)
    return _err(404, "not_found", f"call {call_id} not found")
