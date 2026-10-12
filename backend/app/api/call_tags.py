"""Call tagging (T7.3 pilot slice): GET, PUT per call.

In-memory per-owner-per-call tags for feedback (interested, spam, follow_up, etc).
Staging: persist to call_tags table or call_notes field.
"""
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services import auth as auth_svc

router = APIRouter()

_tags: dict = {}


def reset() -> None:
    _tags.clear()


def _user(authorization: str) -> str | None:
    if not authorization.startswith("Bearer "):
        return None
    sub = auth_svc.verify_access(authorization[7:])
    return sub if isinstance(sub, str) else None


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


class TagsIn(BaseModel):
    tags: list[str]


@router.get("/calls/{call_id}/tags")
def get_tags(call_id: str, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    owner_tags = _tags.setdefault(user, {})
    return {"tags": owner_tags.get(call_id, [])}


@router.put("/calls/{call_id}/tags")
def put_tags(call_id: str, body: TagsIn, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    owner_tags = _tags.setdefault(user, {})
    owner_tags[call_id] = body.tags
    return {"tags": body.tags}
