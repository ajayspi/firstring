"""Hashed-contacts match (§C.3): client-hashed numbers only, never raw.

The device hashes; we only ever compare digests, so no raw number reaches
the server (§7.6 minimisation).
"""
import re

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def match(given_hashes: list, owner_hashes: set) -> dict:
    """Split client hashes into matched/unknown; reject anything not a digest."""
    matched, unknown = [], []
    for h in given_hashes:
        if not isinstance(h, str) or not _SHA256_HEX.match(h):
            raise ValueError("contacts must be sha256 hex digests, never raw numbers")
        (matched if h in owner_hashes else unknown).append(h)
    return {"matched": matched, "unknown": unknown}
