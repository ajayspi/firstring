"""MediCall AI call state machine — single source of truth.

Medical voice-first flow (stdlib only, no infra deps so the validator can
be imported anywhere, including the DB layer and agent workers):
GREETING -> TRIAGE -> APPOINTMENT / PRESCRIPTION -> COMPLETE,
with ESCALATED / DROPPED exits and a PAYMENT_SENT / PAYMENT_EXPIRED loop.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


class CallState(str, Enum):
    GREETING = "GREETING"
    TRIAGE = "TRIAGE"
    APPOINTMENT = "APPOINTMENT"
    PRESCRIPTION = "PRESCRIPTION"
    COMPLETE = "COMPLETE"
    ESCALATED = "ESCALATED"
    DROPPED = "DROPPED"
    PAYMENT_SENT = "PAYMENT_SENT"
    PAYMENT_EXPIRED = "PAYMENT_EXPIRED"


class TriageSeverity(str, Enum):
    GREEN = "green"  # Routine follow-up
    AMBER = "amber"  # Urgent but not emergency
    RED = "red"  # Emergency, immediate attention
    CRITICAL = "critical"  # Life-critical, EMS activated


STATE_TRANSITIONS = {
    CallState.GREETING: [
        CallState.TRIAGE,
        CallState.ESCALATED,
        CallState.DROPPED,
    ],
    CallState.TRIAGE: [
        CallState.APPOINTMENT,
        CallState.PRESCRIPTION,
        CallState.ESCALATED,
        CallState.DROPPED,
    ],
    CallState.APPOINTMENT: [
        CallState.PRESCRIPTION,
        CallState.PAYMENT_SENT,
        CallState.COMPLETE,
        CallState.ESCALATED,
        CallState.DROPPED,
    ],
    CallState.PRESCRIPTION: [
        CallState.PAYMENT_SENT,
        CallState.COMPLETE,
        CallState.ESCALATED,
        CallState.DROPPED,
    ],
    CallState.PAYMENT_SENT: [
        CallState.COMPLETE,
        CallState.PAYMENT_EXPIRED,
        CallState.DROPPED,
    ],
    CallState.PAYMENT_EXPIRED: [
        CallState.APPOINTMENT,
        CallState.ESCALATED,
        CallState.DROPPED,
    ],
    CallState.COMPLETE: [],
    CallState.ESCALATED: [],
    CallState.DROPPED: [],
}


@dataclass
class Call:
    id: str
    clinic_id: str
    caller_number: str
    state: CallState
    started_at: Optional[datetime] = None
    caller_language: str = "en"  # hi, en, ta, te, bn
    ended_at: Optional[datetime] = None
    transcript: List[Dict] = field(default_factory=list)
    stt_confidence: float = 0.0
    triage_severity: Optional[str] = None
    escalated_to_human: bool = False

    def can_transition(self, new_state: CallState) -> bool:
        return new_state in STATE_TRANSITIONS.get(self.state, [])

    def transition(self, new_state: CallState) -> bool:
        if self.can_transition(new_state):
            self.state = new_state
            return True
        return False
