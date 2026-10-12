"""Notification preferences (T7.2 pilot slice): GET, PUT.

In-memory per-owner settings. Staging: persist to notification_preferences table.
Default: WhatsApp only (required for after-hours). Owner can opt into email/SMS/push.
"""
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services import auth as auth_svc

router = APIRouter()

_preferences: dict = {}


def reset() -> None:
    _preferences.clear()


def _user(authorization: str) -> str | None:
    if not authorization.startswith("Bearer "):
        return None
    sub = auth_svc.verify_access(authorization[7:])
    return sub if isinstance(sub, str) else None


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


def _defaults():
    return {"whatsapp": True, "email": False, "sms": False, "push": False}


class PreferencesIn(BaseModel):
    whatsapp: bool
    email: bool
    sms: bool
    push: bool


@router.get("/notifications/preferences")
def get_preferences(authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    return _preferences.get(user, _defaults())


@router.put("/notifications/preferences")
def put_preferences(body: PreferencesIn, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    prefs = {
        "whatsapp": body.whatsapp,
        "email": body.email,
        "sms": body.sms,
        "push": body.push,
    }
    _preferences[user] = prefs
    return prefs
