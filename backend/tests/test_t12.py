"""T1.2 call records + state machine (SM-1 telephony leg, invariant A.2).

The base's CallState enum is the consultation leg (GREETING→TRIAGE→…);
this module is the telephony leg (ringing→live→…) and does not touch it.
Every transition builds a call_events row (staging appends it in the same
write as the state change); idx sequencing is assigned here.

Run: python -m pytest backend/tests/test_t12.py -q
"""
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.services import call_state as cs


class TestWalk(unittest.TestCase):
    def test_full_walk_records_sequenced_events(self):
        events = []
        state = "ringing"
        for event in ("answered", "ended"):
            state = cs.transition(state, event)
            cs.append_event(events, "call-1", event, state)
        self.assertEqual(state, "ended")
        self.assertEqual([e["idx"] for e in events], [0, 1])
        self.assertEqual([e["type"] for e in events], ["answered", "ended"])
        self.assertTrue(all(e["call_id"] == "call-1" for e in events))

    def test_live_branches(self):
        self.assertEqual(cs.transition("live", "take_over"), "take_over")
        self.assertEqual(cs.transition("live", "voicemail"), "voicemail")
        self.assertEqual(cs.transition("take_over", "ended"), "ended")
        self.assertEqual(cs.transition("voicemail", "ended"), "ended")

    def test_illegal_transition_raises(self):
        with self.assertRaises(cs.InvalidTransition):
            cs.transition("ringing", "ended")
        with self.assertRaises(cs.InvalidTransition):
            cs.transition("ended", "answered")
        with self.assertRaises(cs.InvalidTransition):
            cs.transition("live", "answered")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
