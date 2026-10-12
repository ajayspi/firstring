"""T2.5 fallback ladder (§7.5): filler → secondary → canned → voicemail.

Ordering guarantees (unit-tested): filler is always first when the primary
is dead (never >2 s of dead air starts the ladder); voicemail is always
last (the caller always hears something); a working primary short-circuits.
Gap timing (<2 s between actions) is a staging measurement, not asserted here.

Run: python -m pytest backend/tests/test_t25.py -q
"""
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.voice import ladder


class TestLadder(unittest.TestCase):
    def test_primary_ok_short_circuits(self):
        meter = []
        self.assertEqual(
            ladder.run({"primary": "ok", "secondary": "dead"}, meter.append),
            ["result"],
        )
        self.assertEqual(meter, ["result"])

    def test_dead_primary_filler_first_then_secondary(self):
        meter = []
        actions = ladder.run({"primary": "dead", "secondary": "ok"}, meter.append)
        self.assertEqual(actions, ["filler", "result"])
        self.assertEqual(meter, actions)

    def test_all_dead_ends_in_voicemail(self):
        meter = []
        actions = ladder.run({"primary": "dead", "secondary": "dead"}, meter.append)
        self.assertEqual(actions, ["filler", "canned", "voicemail"])
        self.assertEqual(actions[0], "filler")
        self.assertEqual(actions[-1], "voicemail")
        self.assertEqual(meter, actions)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
