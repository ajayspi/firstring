"""Signed webhook ingress (§B.3): verify, dedupe, enqueue, retry→DLQ.

Pilot cuts (ledgered): HMAC-SHA256 convention instead of provider-native
schemes; in-memory dedupe/queue instead of webhook_events + Redis stream.
"""
import hashlib
import hmac
import os
from collections.abc import Callable

MAX_ATTEMPTS = 3
BACKOFF_S = [1, 5, 25]
# Initial try + 3 retries = 4 handler calls; a sleep precedes each retry.

# ponytail: module-level set/list — one pilot process. Staging uses
# webhook_events' UNIQUE(provider, event_id) + a Redis stream instead.
_seen: set = set()
_queue: list = []


def verify_signature(provider: str, raw_body: bytes, header: str) -> bool:
    """HMAC-SHA256 over raw bytes; constant-time compare."""
    secret = os.getenv(f"{provider.upper()}_WEBHOOK_SECRET", "")
    if not secret or not header.startswith("sha256="):
        return False
    expect = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expect, header)


def dedupe(provider: str, event_id: str) -> bool:
    """True when this (provider, event_id) is seen for the first time."""
    key = (provider, event_id)
    if key in _seen:
        return False
    _seen.add(key)
    return True


def enqueue(event: dict) -> None:
    _queue.append(event)


def process_with_retry(
    event: dict, handler: Callable[[dict], None], sleeper: Callable[[int], None]
) -> None:
    """Run handler; initial try + 3 retries, then dead_letter (§D.2, §D.5)."""
    max_tries = 1 + len(BACKOFF_S)
    while event.get("attempts", 0) < max_tries:
        try:
            handler(event)
            return
        except Exception:  # noqa: BLE001 — every failure retries, then DLQs
            event["attempts"] = event.get("attempts", 0) + 1
            if event["attempts"] >= max_tries:
                event["status"] = "dead_letter"
                return
            sleeper(BACKOFF_S[event["attempts"] - 1])
