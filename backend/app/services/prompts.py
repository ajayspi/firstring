"""Instruction compile → versioned prompt (§1.5, §C.5).

The same body always compiles to the same version id, so a call's pinned
prompt reproduces exactly (T4.2 accept: replay shows the version diff).
"""
import hashlib

MAX_CHARS = 4000


class EmptyInstruction(Exception):
    pass


class InstructionTooLong(Exception):
    pass


def compile_instructions(body: str) -> dict:
    body = (body or "").strip()
    if not body:
        raise EmptyInstruction()
    if len(body) > MAX_CHARS:
        raise InstructionTooLong()
    version_id = "pv-" + hashlib.sha256(body.encode()).hexdigest()[:12]
    return {"id": version_id, "system": f"{body}\n[prompt_version: {version_id}]"}
