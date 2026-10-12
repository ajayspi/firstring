"""T2.4 turn controller (§2.11): backchannel guard, barge-in, end-of-turn,
5 s silence → prompt → voicemail. Pure logic, durations passed directly —
no clock, fully deterministic.

Policy: silence 600 ms · min-speech 200 ms · backchannel 400 ms ·
barge-in cancels TTS · 5 s silence → "Are you there?" → +5 s → voicemail.

Run: python -m pytest backend/tests/test_t24.py -q
"""
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.voice import turn


class TestBackchannel(unittest.TestCase):
    def test_short_non_sentence_speech_never_cancels(self):
        c = turn.TurnController()
        c.tts_started()
        self.assertEqual(c.caller_speech(300, is_sentence=False), [])
        self.assertTrue(c.tts_playing)

    def test_below_min_speech_ignored(self):
        c = turn.TurnController()
        c.tts_started()
        self.assertEqual(c.caller_speech(150, is_sentence=True), [])
        self.assertTrue(c.tts_playing)


class TestBargeIn(unittest.TestCase):
    def test_long_speech_cancels_tts(self):
        c = turn.TurnController()
        c.tts_started()
        self.assertEqual(c.caller_speech(1500, is_sentence=True), [("cancel_tts",)])
        self.assertFalse(c.tts_playing)

    def test_no_cancel_when_tts_idle(self):
        c = turn.TurnController()
        self.assertEqual(c.caller_speech(1500, is_sentence=True), [])


class TestEndOfTurn(unittest.TestCase):
    def test_silence_after_final_ends_turn(self):
        c = turn.TurnController()
        c.asr_final("mujhe bukhar hai")
        self.assertEqual(c.caller_silence(500), [])
        self.assertEqual(c.caller_silence(700), [("end_turn", "mujhe bukhar hai")])

    def test_silence_without_pending_is_not_end_turn(self):
        c = turn.TurnController()
        self.assertNotIn("end_turn", str(c.caller_silence(700)))


class TestCallerSilence(unittest.TestCase):
    def test_five_seconds_prompts_then_voicemail(self):
        c = turn.TurnController()
        self.assertEqual(c.caller_silence(5000), [("prompt", "Are you there?")])
        self.assertEqual(c.caller_silence(10000), [("voicemail",)])

    def test_speech_resets_prompt_ladder(self):
        c = turn.TurnController()
        c.caller_silence(5000)
        c.caller_speech(800, is_sentence=True)
        self.assertEqual(c.caller_silence(5000), [("prompt", "Are you there?")])


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
