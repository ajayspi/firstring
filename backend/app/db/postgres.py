"""Async PostgreSQL + pgvector database client for MediCall AI.

Local PostgreSQL with pgvector for the Medical Call Center domain:
voice-first calls, multi-language STT/TTS (hi/en/ta/te/bn), Indian
payment gateways (Razorpay/PhonePe/Cashfree), Indian telephony
(Exotel/Knowlarity/Twilio India).

Conventions: asyncpg driver, pgvector for embeddings (similar-call
search, symptom clustering), UTC tz-aware timestamps, SQLAlchemy 2.0
typed models mirroring backend/postgres_schema.sql.
"""

import os
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional

from app.models.call import CallState, TriageSeverity
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

# ─── Environment & Configuration ──────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://medicall:medicall@localhost:5432/medicall",
)

POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "30"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
SQL_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"


# ─── Engine Factory ────────────────────────────────────────────────────────


def get_engine() -> AsyncEngine:
    """Create async SQLAlchemy engine with pgvector support."""
    if os.getenv("DB_ENV") == "test":
        return create_async_engine(
            DATABASE_URL,
            echo=SQL_ECHO,
            poolclass=NullPool,
        )
    return create_async_engine(
        DATABASE_URL,
        echo=SQL_ECHO,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
    )


engine: AsyncEngine = get_engine()
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


# ─── Base & Helpers ────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


def now_tz() -> datetime:
    """Current UTC datetime with timezone."""
    return datetime.now(timezone.utc)


# ─── Enums (canonical definitions live in app.models.call) ────────────────

# Supported caller/patient languages: Hindi, English, Tamil, Telugu, Bengali.
SUPPORTED_LANGUAGES = ("hi", "en", "ta", "te", "bn")


# ─── Database Models ───────────────────────────────────────────────────────


class Clinic(Base):
    """Clinic/facility entity."""

    __tablename__ = "clinics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[Optional[str]] = mapped_column(String(10))
    latitude: Mapped[Optional[float]] = mapped_column()
    longitude: Mapped[Optional[float]] = mapped_column()
    closing_time: Mapped[str] = mapped_column(String(5), default="22:00")
    ai_instructions: Mapped[str] = mapped_column(Text, default="")
    # starter, growth, enterprise
    plan: Mapped[str] = mapped_column(String(50), default="starter")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz, onupdate=now_tz
    )

    def __repr__(self) -> str:
        return f"<Clinic id={self.id} name={self.name} city={self.city}>"


class ClinicUser(Base):
    """Multi-tenant clinic staff/users."""

    __tablename__ = "clinic_users"
    __table_args__ = (UniqueConstraint("clinic_id", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    # owner, staff, readonly, triage_agent
    role: Mapped[str] = mapped_column(String(20), default="staff")
    # hi, en, ta, te, bn
    language_pref: Mapped[str] = mapped_column(String(5), default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<ClinicUser clinic={self.clinic_id} role={self.role}>"


class Call(Base):
    """Core: voice-first medical call record."""

    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
    )
    caller_number: Mapped[str] = mapped_column(String(30), nullable=False)
    # hi, en, ta, te, bn
    caller_language: Mapped[str] = mapped_column(String(5), default="en")
    # GREETING, TRIAGE, APPOINTMENT, PRESCRIPTION, COMPLETE, ESCALATED, DROPPED
    state: Mapped[str] = mapped_column(String(20), default="GREETING")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # Multi-language transcript:
    # [{"role": "caller", "text": "...", "language": "hi"}, ...]
    transcript: Mapped[list] = mapped_column(JSONB, default=list)
    stt_confidence: Mapped[float] = mapped_column(default=0.0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    # green, amber, red, critical (from AI triage)
    triage_severity: Mapped[Optional[str]] = mapped_column(String(20))
    # SNOMED CT code list
    diagnosed_conditions: Mapped[list] = mapped_column(JSONB, default=list)
    prescription_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    appointment_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True
    )
    escalated_to_human: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz, onupdate=now_tz
    )

    embedding_rel: Mapped[Optional["CallEmbedding"]] = relationship(
        back_populates="call", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<Call id={self.id} clinic={self.clinic_id} "
            f"state={self.state} lang={self.caller_language}>"
        )


class Appointment(Base):
    """Appointment derived from call triage + scheduling."""

    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_phone: Mapped[Optional[str]] = mapped_column(String(30))
    patient_language: Mapped[str] = mapped_column(String(5), default="en")
    caller_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), nullable=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # pending, confirmed, completed, cancelled, no_show
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # chief complaint summary
    reason: Mapped[Optional[str]] = mapped_column(Text)
    doctor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    # clinic address or telemedicine link
    location: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz, onupdate=now_tz
    )

    def __repr__(self) -> str:
        return (
            f"<Appointment id={self.id} clinic={self.clinic_id} "
            f"status={self.status}>"
        )


class Prescription(Base):
    """Prescription from call triage + doctor review."""

    __tablename__ = "prescriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_name: Mapped[Optional[str]] = mapped_column(String(255))
    patient_phone: Mapped[Optional[str]] = mapped_column(String(30))
    patient_language: Mapped[str] = mapped_column(String(5), default="en")
    caller_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id"), nullable=True
    )
    medication: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String(100))
    frequency: Mapped[Optional[str]] = mapped_column(String(50))
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    doctor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    # pending, approved, sent_pharmacy, dispensed
    status: Mapped[str] = mapped_column(String(20), default="pending")
    pharmacy_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz, onupdate=now_tz
    )

    def __repr__(self) -> str:
        return (
            f"<Prescription id={self.id} med={self.medication} "
            f"clinic={self.clinic_id}>"
        )


class CallEmbedding(Base):
    """pgvector embedding for similar-call search and triage patterns."""

    __tablename__ = "call_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    # 1536-dim pgvector embedding
    embedding: Mapped[list] = mapped_column(Vector(1536), nullable=False)
    # call_analysis, triage_summary, prescription_summary, speaker_embedding
    embedding_type: Mapped[str] = mapped_column(
        String(30), default="call_analysis"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    call: Mapped["Call"] = relationship(back_populates="embedding_rel")

    def __repr__(self) -> str:
        return f"<CallEmbedding id={self.id} type={self.embedding_type}>"


class LanguageCode(Base):
    """Indian languages reference — STT/TTS model mapping."""

    __tablename__ = "language_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # hi, en, ta, te, bn
    code: Mapped[str] = mapped_column(String(5), unique=True)
    script: Mapped[str] = mapped_column(String(30))
    # Deepgram model name/identifier
    deepgram_model: Mapped[str] = mapped_column(String(50), default="nova-3")
    elevenlabs_voice_id: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<LanguageCode code={self.code} script={self.script}>"


class CallSession(Base):
    """LiveKit room mapping for active calls."""

    __tablename__ = "call_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    clinic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=True
    )
    livekit_room: Mapped[Optional[str]] = mapped_column(String(255))
    livekit_participant_id: Mapped[Optional[str]] = mapped_column(String(255))
    # idle, recording, in_progress, completed, failed
    status: Mapped[str] = mapped_column(String(20), default="idle")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<CallSession call={self.call_id} status={self.status}>"


# ─── Plan §1 tables (voice pipeline, prompts, eval, ops) ────────────────────


class WebhookEvent(Base):
    """Inbound provider webhook, idempotent on (provider, event_id) — §B.3."""

    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("provider", "event_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # received, processing, done, dead_letter
    status: Mapped[str] = mapped_column(String(20), default="received")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<WebhookEvent {self.provider}:{self.event_id} {self.status}>"


class CallEvent(Base):
    """Append-only per-call state transitions — invariant A.2."""

    __tablename__ = "call_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<CallEvent call={self.call_id} idx={self.idx} {self.type}>"


class PromptVersion(Base):
    """Versioned compiled system prompt, pinned per call — §C.5."""

    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<PromptVersion id={self.id} active={self.active}>"


class VoiceConfig(Base):
    """Per-language pipeline config: turn policy + vendor set — §2.11, §C.5."""

    __tablename__ = "voice_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    turn_policy: Mapped[dict] = mapped_column(JSONB, default=dict)
    vendor_set: Mapped[dict] = mapped_column(JSONB, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<VoiceConfig {self.language} active={self.active}>"


class EvalCase(Base):
    """Caller-turn script + assertions for one eval scenario — T3.1."""

    __tablename__ = "eval_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    script: Mapped[dict] = mapped_column(JSONB, default=dict)
    assertions: Mapped[dict] = mapped_column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<EvalCase {self.name} {self.language}>"


class EvalRun(Base):
    """One harness run: vendor set + measured metrics — T3.2."""

    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    vendor_set: Mapped[dict] = mapped_column(JSONB, default=dict)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<EvalRun id={self.id}>"


class Notification(Base):
    """Owner notifications (summary/missed/action) — §C.3, via outbox."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<Notification {self.kind} clinic={self.clinic_id}>"


class BlocklistEntry(Base):
    """Blocked caller numbers — blocked callers never reach the pipeline."""

    __tablename__ = "blocklist"

    e164: Mapped[str] = mapped_column(String(20), primary_key=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<BlocklistEntry {self.e164}>"


class OutboxEntry(Base):
    """Transactional outbox for side effects — invariant D.4."""

    __tablename__ = "outbox"
    __table_args__ = (UniqueConstraint("dedupe_key"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    topic: Mapped[str] = mapped_column(String(50), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )

    def __repr__(self) -> str:
        return f"<OutboxEntry {self.topic} {self.dedupe_key}>"


# ─── Session Management ────────────────────────────────────────────────────


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session (use as FastAPI dependency)."""
    async with SessionFactory() as session:
        yield session


def get_engine_fresh() -> AsyncEngine:
    """Get a fresh engine instance (useful for testing)."""
    return get_engine()


# ─── CRUD operations for the MediCall AI workflow ──────────────────────────


async def create_clinic(
    name: str,
    phone_number: str,
    city: str,
    state: str,
    **kwargs: Any,
) -> Clinic:
    """Create a new clinic."""
    async with SessionFactory() as session:
        stmt = (
            insert(Clinic)
            .values(
                name=name,
                phone_number=phone_number,
                city=city,
                state=state,
                **kwargs,
            )
            .returning(Clinic)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one()


async def get_clinic(clinic_id: uuid.UUID) -> Optional[Clinic]:
    """Get clinic by ID."""
    async with SessionFactory() as session:
        return await session.get(Clinic, clinic_id)


async def list_clinic_calls(
    clinic_id: uuid.UUID,
    state: Optional[str] = None,
    language: Optional[str] = None,
) -> list[Call]:
    """List calls for a clinic, optionally filtered by state or language."""
    async with SessionFactory() as session:
        query = select(Call).where(Call.clinic_id == clinic_id)
        if state:
            query = query.where(Call.state == state)
        if language:
            query = query.where(Call.caller_language == language)
        query = query.order_by(Call.started_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())


async def create_call(
    clinic_id: uuid.UUID,
    caller_number: str,
    caller_language: str = "en",
    state: str = CallState.GREETING.value,
    **kwargs: Any,
) -> Call:
    """Create a new call record."""
    async with SessionFactory() as session:
        stmt = (
            insert(Call)
            .values(
                clinic_id=clinic_id,
                caller_number=caller_number,
                caller_language=caller_language,
                state=state,
                **kwargs,
            )
            .returning(Call)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one()


async def update_call_state(call_id: uuid.UUID, new_state: str) -> bool:
    """Update call state in the state machine."""
    async with SessionFactory() as session:
        stmt = (
            update(Call)
            .where(Call.id == call_id)
            .values(state=new_state, updated_at=now_tz())
            .returning(Call.state)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one() is not None


async def create_appointment(
    clinic_id: uuid.UUID,
    patient_name: str,
    patient_phone: str,
    patient_language: str = "en",
    caller_id: Optional[uuid.UUID] = None,
    scheduled_at: Optional[datetime] = None,
    **kwargs: Any,
) -> Appointment:
    """Create a new appointment."""
    async with SessionFactory() as session:
        stmt = (
            insert(Appointment)
            .values(
                clinic_id=clinic_id,
                patient_name=patient_name,
                patient_phone=patient_phone,
                patient_language=patient_language,
                caller_id=caller_id,
                scheduled_at=scheduled_at,
                **kwargs,
            )
            .returning(Appointment)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one()


async def create_prescription(
    clinic_id: uuid.UUID,
    patient_name: str,
    patient_phone: str,
    medication: str,
    dosage: str = "",
    frequency: str = "",
    instructions: str = "",
    caller_id: Optional[uuid.UUID] = None,
    **kwargs: Any,
) -> Prescription:
    """Create a new prescription."""
    async with SessionFactory() as session:
        stmt = (
            insert(Prescription)
            .values(
                clinic_id=clinic_id,
                patient_name=patient_name,
                patient_phone=patient_phone,
                medication=medication,
                dosage=dosage,
                frequency=frequency,
                instructions=instructions,
                caller_id=caller_id,
                **kwargs,
            )
            .returning(Prescription)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one()


async def log_call_embedding(
    call_id: uuid.UUID,
    embedding: list,
    embedding_type: str = "call_analysis",
) -> CallEmbedding:
    """Insert or update a call embedding (call_id is UNIQUE)."""
    async with SessionFactory() as session:
        existing = (
            await session.execute(
                select(CallEmbedding).where(CallEmbedding.call_id == call_id)
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.embedding = embedding
            existing.embedding_type = embedding_type
            await session.commit()
            return existing
        stmt = (
            insert(CallEmbedding)
            .values(
                call_id=call_id,
                embedding=embedding,
                embedding_type=embedding_type,
            )
            .returning(CallEmbedding)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one()


async def get_call_embedding(call_id: uuid.UUID) -> Optional[CallEmbedding]:
    """Retrieve call embedding by call_id."""
    async with SessionFactory() as session:
        return (
            await session.execute(
                select(CallEmbedding).where(CallEmbedding.call_id == call_id)
            )
        ).scalar_one_or_none()


async def list_language_codes(active_only: bool = True) -> list[LanguageCode]:
    """List language codes, optionally active-only."""
    async with SessionFactory() as session:
        query = select(LanguageCode)
        if active_only:
            query = query.where(LanguageCode.is_active.is_(True))
        query = query.order_by(LanguageCode.code)
        result = await session.execute(query)
        return list(result.scalars().all())


# ─── Migration Entrypoint ──────────────────────────────────────────────────


async def init_db() -> None:
    """Create all tables (dev/test). Prod uses postgres_schema.sql + Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))


# ─── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio

    async def _self_check() -> None:
        tables = sorted(Base.metadata.tables.keys())
        print("MediCall AI Async PostgreSQL Client")
        print(f"Database URL: {DATABASE_URL}")
        print(f"Tables: {', '.join(tables)}")

    asyncio.run(_self_check())
