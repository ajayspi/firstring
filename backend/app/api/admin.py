"""Admin dashboard API (T8.1 pilot slice): calls view, clinic metrics, system health.

In-memory aggregates for pilot. Staging: query real calls/clinics tables with rollups.
Auth: Bearer token from admin users list (hardcoded in pilot).
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services import auth as auth_svc

router = APIRouter(prefix="/admin", tags=["admin"])

# Admin user list (pilot: hardcoded)
_admin_users = {
    "admin@firstring.com": "admin-token-12345",
    "founder@firstring.com": "founder-token-67890",
}

# In-memory clinic + call aggregates
_clinic_metrics: dict = {}
_call_log: list = []


def reset() -> None:
    _clinic_metrics.clear()
    _call_log.clear()


def _verify_admin(authorization: str) -> str | None:
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    for email, admin_token in _admin_users.items():
        if token == admin_token:
            return email
    return None


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


@router.get("/health")
def admin_health(authorization: str = Header(default="")):
    """System health check for admin dashboard."""
    admin = _verify_admin(authorization)
    if admin is None:
        return _err(401, "unauthorized", "invalid admin token")
    
    now = datetime.now(timezone.utc)
    total_calls = len(_call_log)
    today_calls = sum(1 for c in _call_log if c["started_at"].date() == now.date())
    total_clinics = len(_clinic_metrics)
    avg_booking_rate = (
        sum(m.get("bookings", 0) for m in _clinic_metrics.values()) / max(total_clinics, 1)
    )

    return {
        "status": "healthy",
        "timestamp": now.isoformat(),
        "system": {
            "total_calls": total_calls,
            "calls_today": today_calls,
            "total_clinics": total_clinics,
            "avg_booking_rate": round(avg_booking_rate, 2),
        },
    }


@router.get("/calls")
def list_admin_calls(authorization: str = Header(default=""), limit: int = 50):
    """View recent calls across all clinics."""
    admin = _verify_admin(authorization)
    if admin is None:
        return _err(401, "unauthorized", "invalid admin token")
    
    # Return latest calls, reverse chronological
    recent = sorted(_call_log, key=lambda c: c["started_at"], reverse=True)[:limit]
    return {
        "items": recent,
        "total": len(_call_log),
    }


@router.get("/calls/{call_id}")
def get_admin_call(call_id: str, authorization: str = Header(default="")):
    """View details of a specific call."""
    admin = _verify_admin(authorization)
    if admin is None:
        return _err(401, "unauthorized", "invalid admin token")
    
    for call in _call_log:
        if call["id"] == call_id:
            return call
    
    return _err(404, "not_found", f"call {call_id} not found")


@router.get("/clinics")
def list_clinics(authorization: str = Header(default="")):
    """View all clinics and their metrics."""
    admin = _verify_admin(authorization)
    if admin is None:
        return _err(401, "unauthorized", "invalid admin token")
    
    items = [
        {
            "phone": phone,
            "plan": metrics.get("plan", "free"),
            "calls": metrics.get("calls", 0),
            "bookings": metrics.get("bookings", 0),
            "booking_rate": round(
                metrics.get("bookings", 0) / max(metrics.get("calls", 1), 1), 3
            ),
            "last_call": metrics.get("last_call"),
            "status": metrics.get("status", "active"),
        }
        for phone, metrics in _clinic_metrics.items()
    ]
    
    return {
        "items": sorted(items, key=lambda x: x["calls"], reverse=True),
        "total": len(_clinic_metrics),
    }


@router.get("/clinics/{phone}")
def get_clinic(phone: str, authorization: str = Header(default="")):
    """View detailed metrics for a specific clinic."""
    admin = _verify_admin(authorization)
    if admin is None:
        return _err(401, "unauthorized", "invalid admin token")
    
    if phone not in _clinic_metrics:
        return _err(404, "not_found", f"clinic {phone} not found")
    
    metrics = _clinic_metrics[phone]
    clinic_calls = [c for c in _call_log if c["owner_phone"] == phone]
    
    return {
        "phone": phone,
        "plan": metrics.get("plan", "free"),
        "created_at": metrics.get("created_at"),
        "stats": {
            "total_calls": len(clinic_calls),
            "bookings": metrics.get("bookings", 0),
            "booking_rate": round(
                metrics.get("bookings", 0) / max(len(clinic_calls), 1), 3
            ),
            "avg_call_duration_sec": round(
                sum(c.get("duration_sec", 0) for c in clinic_calls) / max(len(clinic_calls), 1), 1
            ),
        },
        "recent_calls": clinic_calls[-5:],  # Last 5
    }


@router.get("/analytics")
def get_analytics(authorization: str = Header(default=""), days: int = 7):
    """High-level analytics dashboard."""
    admin = _verify_admin(authorization)
    if admin is None:
        return _err(401, "unauthorized", "invalid admin token")
    
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    
    recent_calls = [c for c in _call_log if c["started_at"] >= cutoff]
    
    by_day = {}
    for call in recent_calls:
        day = call["started_at"].date().isoformat()
        if day not in by_day:
            by_day[day] = {"calls": 0, "bookings": 0}
        by_day[day]["calls"] += 1
        if call.get("outcome") == "booking":
            by_day[day]["bookings"] += 1
    
    return {
        "period_days": days,
        "summary": {
            "total_calls": len(recent_calls),
            "total_bookings": sum(1 for c in recent_calls if c.get("outcome") == "booking"),
            "booking_rate": round(
                sum(1 for c in recent_calls if c.get("outcome") == "booking") / max(len(recent_calls), 1),
                3,
            ),
            "avg_call_duration_sec": round(
                sum(c.get("duration_sec", 0) for c in recent_calls) / max(len(recent_calls), 1), 1
            ),
        },
        "by_day": sorted(by_day.items()),
    }


@router.post("/clinics/{phone}/simulate-call")
def simulate_call(phone: str, body: dict, authorization: str = Header(default="")):
    """[TEST ONLY] Simulate a call for a clinic to populate dashboard."""
    admin = _verify_admin(authorization)
    if admin is None:
        return _err(401, "unauthorized", "invalid admin token")
    
    if phone not in _clinic_metrics:
        _clinic_metrics[phone] = {"plan": "free", "calls": 0, "bookings": 0}
    
    call_id = f"call-test-{len(_call_log)}"
    now = datetime.now(timezone.utc)
    
    is_booking = body.get("outcome") == "booking"
    
    _call_log.append({
        "id": call_id,
        "owner_phone": phone,
        "caller_phone": body.get("caller_phone", "+919000000001"),
        "started_at": now,
        "ended_at": now + timedelta(minutes=body.get("duration_min", 2)),
        "duration_sec": body.get("duration_min", 2) * 60,
        "state": "COMPLETE",
        "outcome": body.get("outcome", "voicemail"),
        "transcript": [{"role": "ai", "text": "Thank you for calling"}],
    })
    
    _clinic_metrics[phone]["calls"] += 1
    if is_booking:
        _clinic_metrics[phone]["bookings"] += 1
    _clinic_metrics[phone]["last_call"] = now.isoformat()
    
    return {"call_id": call_id, "status": "simulated"}


# Helper to populate clinic from owner routes
def register_clinic(phone: str, plan: str = "free"):
    """Register a new clinic (called when owner creates account)."""
    if phone not in _clinic_metrics:
        _clinic_metrics[phone] = {
            "phone": phone,
            "plan": plan,
            "calls": 0,
            "bookings": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
