"""Owner routes (pilot slice of §C): auth gate, /me, /instructions,
/blocklist, /billing/usage, /contacts/sync.

In-memory per-user state until staging PG lands. Envelope errors follow
§C.13: {"error": {"code", "message"}}.
"""
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app.services import auth as auth_svc
from app.services import blocklist, billing, contacts, prompts

router = APIRouter()

# ponytail: per-user dicts — one pilot process. Staging moves these to
# prompt_versions / blocklist / usage tables behind the same handlers.
# _patients: sha256 digests of known patients — staging fills from appointments.
_instructions: dict = {}
_versions: dict = {}
_meters: dict = {}
_patients: dict = {}


def reset() -> None:
    _instructions.clear()
    _versions.clear()
    _meters.clear()
    _patients.clear()


def _user(authorization: str) -> str | None:
    if not authorization.startswith("Bearer "):
        return None
    sub = auth_svc.verify_access(authorization[7:])
    return sub if isinstance(sub, str) else None


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"error": {"code": code, "message": message}}
    )


def _gate(authorization: str):
    user = _user(authorization)
    if user is None:
        return None, _err(401, "unauthorized", "missing or invalid token")
    return user, None


class InstructionBody(BaseModel):
    body: str


class BlockIn(BaseModel):
    e164: str
    reason: str = ""


class SyncIn(BaseModel):
    hashes: list[str]


@router.get("/me")
def me(authorization: str = Header(default="")):
    user, err = _gate(authorization)
    if err:
        return err
    return {"phone": user, "plan": "free"}


@router.get("/instructions")
def get_instructions(authorization: str = Header(default="")):
    user, err = _gate(authorization)
    if err:
        return err
    return {"body": _instructions.get(user, "")}


@router.put("/instructions")
def put_instructions(body: InstructionBody, authorization: str = Header(default="")):
    user, err = _gate(authorization)
    if err:
        return err
    try:
        prompts.compile_instructions(body.body)
    except prompts.EmptyInstruction:
        return _err(422, "validation_error", "instruction empty")
    except prompts.InstructionTooLong:
        return _err(422, "instruction_too_long", "max 4000 chars")
    _instructions[user] = body.body
    return {"body": body.body}


@router.post("/instructions/compile")
def compile_instruction(authorization: str = Header(default="")):
    user, err = _gate(authorization)
    if err:
        return err
    try:
        compiled = prompts.compile_instructions(_instructions.get(user, ""))
    except prompts.EmptyInstruction:
        return _err(422, "instruction_empty", "set instructions first")
    version = compiled["id"]
    _versions.setdefault(user, {})[version] = compiled["system"]
    return {"prompt_version_id": version, "preview": compiled["system"]}


@router.get("/blocklist")
def get_blocklist(authorization: str = Header(default="")):
    user, err = _gate(authorization)
    if err:
        return err
    return {"items": list(blocklist._entries.values())}


@router.post("/blocklist", status_code=201)
def post_blocklist(body: BlockIn, authorization: str = Header(default="")):
    user, err = _gate(authorization)
    if err:
        return err
    if blocklist.is_blocked(body.e164):
        return _err(409, "already_blocked", "number already blocked")
    blocklist.block(body.e164, body.reason)
    return {"e164": body.e164, "reason": body.reason}


@router.delete("/blocklist/{e164}", status_code=204)
def delete_blocklist(e164: str, authorization: str = Header(default="")):
    user, err = _gate(authorization)
    if err:
        return err
    if not blocklist.is_blocked(e164):
        return _err(404, "not_found", "not blocked")
    blocklist.unblock(e164)
    return Response(status_code=204)


@router.get("/billing/usage")
def billing_usage(authorization: str = Header(default="")):
    user, err = _gate(authorization)
    if err:
        return err
    meter = _meters.setdefault(user, billing.Meter())
    return {"plan": "free", **meter.usage("free")}


@router.post("/contacts/sync")
def contacts_sync(body: SyncIn, authorization: str = Header(default="")):
    user, err = _gate(authorization)
    if err:
        return err
    try:
        return contacts.match(body.hashes, _patients.get(user, set()))
    except ValueError:
        return _err(422, "validation_error", "hashes must be sha256 digests")
