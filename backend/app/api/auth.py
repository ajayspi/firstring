"""Auth routes (§C.1 PUBLIC): OTP request/verify, refresh, logout."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.services import auth as svc

router = APIRouter()


def _default_sender(phone: str, code: str) -> None:
    # Staging replaces this with the DLT-registered sender. Never log the code.
    print(f"OTP requested for {phone}")


# Overridden in tests; wired to the DLT sender in staging.
_sender = _default_sender


class OtpRequest(BaseModel):
    phone_e164: str


class OtpVerify(BaseModel):
    otp_id: str
    code: str


class RefreshIn(BaseModel):
    refresh_token: str


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


@router.post("/auth/otp/request", status_code=202)
def otp_request(body: OtpRequest):
    try:
        otp_id, expires_in = svc.request_otp(body.phone_e164, _sender)
    except ValueError:
        return _err(422, "validation_error", "phone_e164 must be E.164")
    except svc.OtpRateLimited:
        return _err(429, "otp_rate_limited", "too many OTP requests")
    return {"otp_id": otp_id, "expires_in": expires_in}


@router.post("/auth/otp/verify")
def otp_verify(body: OtpVerify):
    try:
        access, refresh, phone = svc.verify_otp(body.otp_id, body.code)
    except svc.OtpInvalid:
        return _err(401, "otp_invalid", "wrong code")
    except svc.OtpExpired:
        return _err(410, "otp_expired", "code expired")
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": {"phone": phone},
    }


@router.post("/auth/refresh")
def auth_refresh(body: RefreshIn):
    try:
        return {"access_token": svc.refresh_tokens(body.refresh_token)}
    except svc.TokenInvalid:
        return _err(401, "token_invalid", "refresh rejected")


@router.post("/auth/logout", status_code=204)
def auth_logout(body: RefreshIn):
    svc.logout(body.refresh_token)
    return Response(status_code=204)
