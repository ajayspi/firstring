"""Telephony-leg state machine (SM-1) + call_events builder (invariant A.2)."""


class InvalidTransition(Exception):
    pass


# state -> {event: next_state}
TRANSITIONS = {
    "ringing": {"answered": "live"},
    "live": {"take_over": "take_over", "voicemail": "voicemail", "ended": "ended"},
    "take_over": {"ended": "ended"},
    "voicemail": {"ended": "ended"},
    "ended": {},
}


def transition(state: str, event: str) -> str:
    """Next state, or raise InvalidTransition (illegal jumps never write)."""
    try:
        return TRANSITIONS[state][event]
    except KeyError:
        raise InvalidTransition(f"{state} + {event}")


def append_event(events: list, call_id: str, type: str, state: str, payload: dict | None = None) -> dict:
    """Build the call_events row with the next sequential idx."""
    row = {
        "call_id": call_id,
        "idx": len(events),
        "type": type,
        "state": state,
        "payload": payload or {},
    }
    events.append(row)
    return row
