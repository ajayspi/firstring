"""ASR seam (§2.8): stream_pcm() → partial/final segments + speech_final.

Real vendor behind this interface on staging; StubAsr replays a script for
T2.4/T2.5 tests.
"""
from dataclasses import dataclass


@dataclass
class Segment:
    kind: str  # "partial" | "final"
    text: str

    @property
    def speech_final(self) -> bool:
        return self.kind == "final"

    @staticmethod
    def partial(text: str) -> "Segment":
        return Segment("partial", text)

    @staticmethod
    def final(text: str) -> "Segment":
        return Segment("final", text)


class StubAsr:
    """Deterministic replay for pipeline tests (no audio, no vendor)."""

    def __init__(self, script: list):
        self._script = list(script)

    def stream_pcm(self, pcm_iter):
        yield from self._script
