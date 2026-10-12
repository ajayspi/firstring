"""Turn controller (§2.11). Tunables mirror voice_configs.turn_policy keys."""

DEFAULT_POLICY = {
    "silence_ms": 600,
    "min_speech_ms": 200,
    "backchannel_ms": 400,
    "silence_prompt_s": 5,
    "silence_voicemail_s": 10,  # cumulative silence reaching voicemail
}

PROMPT_LINE = "Are you there?"


class TurnController:
    def __init__(self, policy: dict | None = None):
        self.p = {**DEFAULT_POLICY, **(policy or {})}
        self.tts_playing = False
        self._pending: str | None = None
        self._prompted = False

    def tts_started(self) -> None:
        self.tts_playing = True

    def tts_ended(self) -> None:
        self.tts_playing = False

    def asr_final(self, text: str) -> None:
        self._pending = text

    def caller_speech(self, duration_ms: int, is_sentence: bool) -> list:
        """Caller audio during (or outside) TTS. Returns actions."""
        self._prompted = False
        if not self.tts_playing:
            return []
        if duration_ms < self.p["min_speech_ms"]:
            return []
        if duration_ms <= self.p["backchannel_ms"] and not is_sentence:
            return []  # backchannel ("haan", "ok") never interrupts
        self.tts_playing = False
        return [("cancel_tts",)]

    def caller_silence(self, silent_ms: int) -> list:
        """Silence durations; returns at most one action per call."""
        if self._pending is not None:
            if silent_ms >= self.p["silence_ms"]:
                text, self._pending = self._pending, None
                return [("end_turn", text)]
            return []
        prompt_at = self.p["silence_prompt_s"] * 1000
        voicemail_at = self.p["silence_voicemail_s"] * 1000
        if silent_ms >= voicemail_at and self._prompted:
            return [("voicemail",)]
        if silent_ms >= prompt_at and not self._prompted:
            self._prompted = True
            return [("prompt", PROMPT_LINE)]
        return []
