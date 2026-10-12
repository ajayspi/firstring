"""Fallback ladder (§7.5). Every event is metered via the `meter` callable."""

CANNED_LINE = "Sorry, I'm having trouble hearing you. Please leave a message after the beep."


def run(components: dict, meter) -> list:
    """components: {"primary": ok|dead, "secondary": ok|dead} → action list."""
    if components.get("primary") == "ok":
        actions = ["result"]
    elif components.get("secondary") == "ok":
        actions = ["filler", "result"]
    else:
        actions = ["filler", "canned", "voicemail"]
    for a in actions:
        meter(a)
    return actions
