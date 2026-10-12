"""Device pairing (T7.1 pilot slice): register, list, revoke.

In-memory per-owner device registry. Staging: persist to devices table.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.services import auth as auth_svc

router = APIRouter()

_devices: dict = {}


def reset() -> None:
    _devices.clear()


def _user(authorization: str) -> str | None:
    if not authorization.startswith("Bearer "):
        return None
    sub = auth_svc.verify_access(authorization[7:])
    return sub if isinstance(sub, str) else None


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


class DeviceIn(BaseModel):
    device_id: str
    name: str


@router.post("/devices", status_code=201)
def register_device(body: DeviceIn, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    owner_devices = _devices.setdefault(user, {})
    if body.device_id in owner_devices:
        return _err(409, "already_registered", f"device {body.device_id} already registered")
    now = datetime.now(timezone.utc).isoformat()
    owner_devices[body.device_id] = {
        "device_id": body.device_id,
        "name": body.name,
        "registered_at": now,
    }
    return owner_devices[body.device_id]


@router.get("/devices")
def list_devices(authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    items = list(_devices.get(user, {}).values())
    return {"items": items}


@router.delete("/devices/{device_id}", status_code=204)
def revoke_device(device_id: str, authorization: str = Header(default="")):
    user = _user(authorization)
    if user is None:
        return _err(401, "unauthorized", "missing or invalid token")
    owner_devices = _devices.get(user, {})
    if device_id not in owner_devices:
        return _err(404, "not_found", f"device {device_id} not registered")
    del owner_devices[device_id]
    return Response(status_code=204)
