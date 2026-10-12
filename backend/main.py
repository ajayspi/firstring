"""MediCall AI — FastAPI Application Entry Point.

Indian Medical Call Center: voice-first, multi-language
(Hindi/English/Tamil/Telugu/Bengali), PostgreSQL + pgvector backend.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.api import voice
from app.api import ops
from app.api import auth
from app.api import telephony
from app.api import owner
from app.api import calls
from app.api import profiles
from app.api import devices
from app.api import notifications
from app.api import call_tags
from app.db.postgres import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("MediCall AI started")
    yield
    # Shutdown
    print("MediCall AI shutting down")


app = FastAPI(
    title="MediCall AI",
    description="Voice-first AI Medical Call Center for India",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes (voice-first; calls/appointments/prescriptions/payments land in G4+)
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(ops.router, tags=["ops"])
app.include_router(auth.router, tags=["auth"])
app.include_router(telephony.router, tags=["telephony"])
app.include_router(owner.router, tags=["owner"])
app.include_router(calls.router, tags=["calls"])
app.include_router(call_tags.router, tags=["call_tags"])
app.include_router(profiles.router, tags=["profiles"])
app.include_router(devices.router, tags=["devices"])
app.include_router(notifications.router, tags=["notifications"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "medicall-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
