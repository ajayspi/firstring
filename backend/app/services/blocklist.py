"""Blocklist gate (§C.8): blocked callers never reach the pipeline.

In-memory for the pilot; staging backs it with the `blocklist` table.
"""

_entries: dict = {}


def block(e164: str, reason: str) -> None:
    _entries[e164] = {"e164": e164, "reason": reason}


def unblock(e164: str) -> None:
    _entries.pop(e164, None)


def is_blocked(e164: str) -> bool:
    return e164 in _entries


def gate_call(e164: str) -> str:
    """Admission decision: 'blocked' ends the call before ASR starts."""
    return "blocked" if is_blocked(e164) else "allow"
