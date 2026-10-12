"""TTS seam (§2.8): speak() → chunked audio + cancel token.

The cancel token is the barge-in path (T2.4): cancel stops the stream
within the barge-in budget. Real vendor behind this interface on staging.
"""
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str


class _Stream:
    def __init__(self, chunks: list):
        self._chunks = chunks
        self.cancelled = False

    def __iter__(self):
        return self

    def __next__(self) -> Chunk:
        if self.cancelled or not self._chunks:
            raise StopIteration
        return Chunk(self._chunks.pop(0))


class StubTts:
    """Deterministic chunk replay for pipeline tests."""

    def __init__(self, chunks: list):
        self._chunks = list(chunks)

    def speak(self, text: str, voice: str) -> _Stream:
        return _Stream(list(self._chunks))

    def cancel(self, stream: _Stream) -> None:
        stream.cancelled = True
