"""LLM seam (§2.8, §7.4): prompt compile, message build, tool allow-list.

Caller speech is data, never instructions: it lands only in the final user
message, never in the system slot. Tool calls are validated server-side —
the model never supplies a destination outside the owner's numbers.
"""
ALLOWLIST = frozenset({"take_message", "set_callback", "send_summary_sms", "add_note"})


class ToolRejected(Exception):
    pass


def compile_system(instructions: str, version_id: str) -> str:
    """Compile owner instructions + pinned version into the system prompt."""
    tools = ", ".join(sorted(ALLOWLIST))
    return f"{instructions}\n[tools: {tools}]\n[prompt_version: {version_id}]"


def build_messages(system: str, history: list, caller_text: str) -> list:
    """System first, history middle, caller text last — caller text is data."""
    return [{"role": "system", "content": system}] + list(history) + [
        {"role": "user", "content": caller_text}
    ]


def validate_tool_call(name: str, args: dict, allowed_numbers: set) -> bool:
    """True when the call is inside the allow-list; else raise ToolRejected."""
    if name not in ALLOWLIST:
        raise ToolRejected(f"tool not allowed: {name}")
    if name == "send_summary_sms" and args.get("to") not in allowed_numbers:
        raise ToolRejected("destination outside owner numbers")
    return True
