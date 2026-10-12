"""Retention windows (§7.6). Pure date math — no DB, no deps.

Windows: recordings 90 d · transcripts + embeddings 365 d · metadata 24 mo.
Months are approximated as 30.44 d only at the boundary definition below
(24 mo = 730 d); the nightly job deletes rows with ts <= cutoff(kind, now).
"""
from datetime import datetime, timedelta

# ponytail: flat days, not calendar months — the job needs a cutoff instant,
# not month arithmetic. 24 mo ≈ 730 d; revisit only if legal demands exactness.
_WINDOWS_DAYS = {
    "recordings": 90,
    "transcripts": 365,
    "embeddings": 365,
    "metadata": 730,
}


def cutoff(kind: str, now: datetime) -> datetime:
    """Latest instant still retained for `kind`; rows at or before it expire."""
    return now - timedelta(days=_WINDOWS_DAYS[kind])


def is_expired(kind: str, ts: datetime, now: datetime) -> bool:
    """True when the row's timestamp falls outside the retention window."""
    return ts <= cutoff(kind, now)
