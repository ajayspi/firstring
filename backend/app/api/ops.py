"""Ops endpoints (§C.12): liveness, readiness, metrics.

- /healthz: process up. Never checks dependencies (a DB blip must not restart pods).
- /readyz: TCP probes for postgres/redis (connect ≤0.5s, §D.1) + telephony
  vendor config presence. 200 when all ok, else 503 with the same shape.
- /metrics: Prometheus exposition (process + medicall_ready gauge).

Probes are module-level names so tests can substitute them; defaults are
real TCP/config checks, stdlib only (no driver imports — sqlalchemy/redis
may be absent and readiness must report, not crash).
"""
import os
import socket
from urllib.parse import urlparse

from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, REGISTRY, generate_latest

router = APIRouter()

_ready_gauge = Gauge("medicall_ready", "1 when /readyz passes, else 0")

# ponytail: TCP reachability, not SELECT 1 — LB membership needs cheap+fast;
# deep dependency health belongs on /internal/health/{dependency} (§C.11, T2.x).
_CONNECT_TIMEOUT_S = 0.5

_VENDOR_KEYS = (
    "EXOTEL_SID",
    "KNOWLARITY_API_KEY",
    "TWILIO_ACCOUNT_SID",
    "LIVEKIT_API_KEY",
)


def _tcp_check(url: str, default_host: str, default_port: int) -> dict:
    try:
        parts = urlparse(url or "")
        host = parts.hostname or default_host
        port = parts.port or default_port
        with socket.create_connection((host, port), timeout=_CONNECT_TIMEOUT_S):
            return {"ok": True, "detail": "tcp"}
    except Exception as e:  # noqa: BLE001 — readiness reports, never raises
        return {"ok": False, "detail": f"{type(e).__name__}"}


def _tcp_probe_postgres() -> dict:
    return _tcp_check(os.getenv("DATABASE_URL", ""), "localhost", 5432)


def _tcp_probe_redis() -> dict:
    return _tcp_check(os.getenv("REDIS_URL", ""), "localhost", 6379)


def _config_probe_vendor() -> dict:
    # Ruling: config presence now; live vendor HTTP probe lands in T3.3
    # (needs real keys and costs money per ping). Cost if wrong: readyz
    # passes with a dead vendor — caught by T2.5 ladder drills instead.
    set_keys = [
        k for k in _VENDOR_KEYS
        if os.getenv(k) and not os.getenv(k, "").startswith("your-")
    ]
    if set_keys:
        return {"ok": True, "detail": f"configured:{set_keys[0]}"}
    return {"ok": False, "detail": "no telephony vendor key set"}


probe_postgres = _tcp_probe_postgres
probe_redis = _tcp_probe_redis
probe_vendor = _config_probe_vendor


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "medicall-api"}


@router.get("/readyz")
def readyz() -> JSONResponse:
    checks = {
        "postgres": probe_postgres(),
        "redis": probe_redis(),
        "vendor": probe_vendor(),
    }
    ready = all(c["ok"] for c in checks.values())
    _ready_gauge.set(1 if ready else 0)
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"ready": ready, "checks": checks},
    )


@router.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
