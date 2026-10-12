"""Phone-OTP auth (§C.1). Secrets from env, read per operation.

Rotation needs no restart: nothing caches JWT_SECRET. OTP store is
in-memory single-process (pilot runs one process; move to Redis at scale).
"""
import hashlib
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

ALGORITHM = "HS256"
OTP_TTL = timedelta(minutes=5)
OTP_WINDOW = timedelta(minutes=10)
OTP_MAX_PER_WINDOW = 3
OTP_MAX_ATTEMPTS = 5
ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=30)

_E164 = re.compile(r"^\+[1-9]\d{7,14}$")


class OtpInvalid(Exception):
    pass


class OtpExpired(Exception):
    pass


class OtpRateLimited(Exception):
    pass


class TokenInvalid(Exception):
    pass


# ponytail: module dicts, not Redis — one pilot process. Move when workers scale.
_store: dict = {}
_requests: dict = {}
_refresh: dict = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _secret() -> str:
    s = os.getenv("JWT_SECRET")
    if not s:
        raise RuntimeError("JWT_SECRET not set")
    return s


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def request_otp(phone: str, sender, now: datetime | None = None) -> tuple[str, int]:
    """Send an OTP; returns (otp_id, expires_in_seconds)."""
    if not _E164.match(phone):
        raise ValueError("phone_e164 must be E.164")
    now = now or _now()
    recent = [t for t in _requests.get(phone, []) if now - t < OTP_WINDOW]
    if len(recent) >= OTP_MAX_PER_WINDOW:
        raise OtpRateLimited()
    recent.append(now)
    _requests[phone] = recent
    code = f"{secrets.randbelow(10**6):06d}"
    otp_id = uuid.uuid4().hex
    _store[otp_id] = {
        "phone": phone,
        "code_hash": _hash(code),
        "expires_at": now + OTP_TTL,
        "attempts": 0,
    }
    sender(phone, code)
    return otp_id, int(OTP_TTL.total_seconds())


def _mint(sub: str, now: datetime) -> tuple[str, str]:
    secret = _secret()
    access = jwt.encode(
        {"sub": sub, "type": "access", "exp": now + ACCESS_TTL},
        secret,
        algorithm=ALGORITHM,
    )
    jti = uuid.uuid4().hex
    refresh = jwt.encode(
        {"sub": sub, "type": "refresh", "jti": jti, "exp": now + REFRESH_TTL},
        secret,
        algorithm=ALGORITHM,
    )
    _refresh[jti] = {"sub": sub, "expires_at": now + REFRESH_TTL}
    return access, refresh


def verify_otp(
    otp_id: str, code: str, now: datetime | None = None
) -> tuple[str, str, str]:
    """Returns (access_token, refresh_token, phone)."""
    now = now or _now()
    entry = _store.get(otp_id)
    if entry is None:
        raise OtpInvalid()
    if now >= entry["expires_at"]:
        _store.pop(otp_id, None)
        raise OtpExpired()
    entry["attempts"] += 1
    if entry["attempts"] > OTP_MAX_ATTEMPTS or _hash(code) != entry["code_hash"]:
        if entry["attempts"] > OTP_MAX_ATTEMPTS:
            _store.pop(otp_id, None)
        raise OtpInvalid()
    _store.pop(otp_id, None)
    access, refresh = _mint(entry["phone"], now)
    return access, refresh, entry["phone"]


def verify_access(token: str):
    """Returns the subject phone, or False when invalid/expired/rotated."""
    try:
        claims = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except (JWTError, RuntimeError):
        return False
    if claims.get("type") != "access":
        return False
    return claims.get("sub", False)


def refresh_tokens(token: str, now: datetime | None = None) -> str:
    """Exchange a live refresh token for a fresh access token."""
    now = now or _now()
    try:
        claims = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except (JWTError, RuntimeError):
        raise TokenInvalid()
    if claims.get("type") != "refresh":
        raise TokenInvalid()
    live = _refresh.get(claims.get("jti", ""))
    if live is None or now >= live["expires_at"]:
        _refresh.pop(claims.get("jti", ""), None)
        raise TokenInvalid()
    return jwt.encode(
        {"sub": live["sub"], "type": "access", "exp": now + ACCESS_TTL},
        _secret(),
        algorithm=ALGORITHM,
    )


def logout(token: str) -> bool:
    """Revoke a refresh token. Idempotent — never raises."""
    try:
        claims = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
    except (JWTError, RuntimeError):
        return True
    _refresh.pop(claims.get("jti", ""), None)
    return True
