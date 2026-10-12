"""Conditional-call-forwarding USSD codes (§C.4, T1.3). Pure data + record."""

_CONDITIONS = {
    "no_answer": ("*61*", "*#61#"),
    "unreachable": ("*62*", "*#62#"),
    "busy": ("*67*", "*#67#"),
    "all": ("*21*", "*#21#"),
}


def setup_codes(did_e164: str) -> dict:
    """Dial strings that forward each condition to the DID, e.g. *61*<DID>#."""
    return {k: f"{set_}{did_e164}#" for k, (set_, _) in _CONDITIONS.items()}


def readback_codes() -> dict:
    """Codes that read back the current forwarding state per condition."""
    return {k: read for k, (_, read) in _CONDITIONS.items()}


def new_record(did_e164: str) -> dict:
    return {"did": did_e164, "verified": False, "observed_at": None}


def mark_observed(record: dict, observed_at: str) -> dict:
    record["verified"] = True
    record["observed_at"] = observed_at
    return record
