"""Caller profiles (T6.1 pilot slice): GET, POST, PUT.

In-memory per-owner caller notes. Staging: persist to profiles table.
"""
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services import auth as auth_svc

router = APIRouter()

_profiles: dict = {}


def reset() -> None:
    _profiles.clear()


def _user(authorization: str) -> str | None:
    if not authorization.startswith("Bearer "):
        return None
    sub = auth_svc.verify_access(authorization[7:])
    return sub if isinstance(sub, str) else None


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


class ProfileIn(BaseModel):
    phone: str
    notes: str = ""


class ProfileOut(BaseModel):
    phone: str
    notes: str
    call_count: int = 0


@router.get("/profiles")
def list_profiles(authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    items = _profiles.get(user, {})
    return {"items": [{"phone": k, **v} for k, v in items.items()]}


@router.post("/profiles", status_code=201)
def create_profile(body: ProfileIn, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    owner_profiles = _profiles.setdefault(user, {})
    if body.phone in owner_profiles:
        return _err(409, "already_exists", f"profile for {body.phone} exists")
    owner_profiles[body.phone] = {"notes": body.notes, "call_count": 0}
    return {"phone": body.phone, "notes": body.notes, "call_count": 0}


@router.put("/profiles/{phone}")
def update_profile(phone: str, body: ProfileIn, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    owner_profiles = _profiles.setdefault(user, {})
    if phone not in owner_profiles:
        return _err(404, "not_found", f"no profile for {phone}")
    owner_profiles[phone]["notes"] = body.notes
    return {"phone": phone, **owner_profiles[phone]}
