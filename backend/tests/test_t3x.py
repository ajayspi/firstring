"""T3.1–T3.2 eval core: pilot scenarios + deterministic scorer.

Scenarios are Hindi + English variants of the pilot's two jobs (book, take
a message) plus the two guardrails (blocked caller, injection refusal).
The scorer compares a run log against expectations — no vendor needed.

Run: python -m pytest backend/tests/test_t3x.py -q
"""
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.eval import cases, metrics


class TestScenarios(unittest.TestCase):
    def test_hindi_and_english_booking_exist(self):
        names = {(c["name"], c["language"]) for c in cases.SCENARIOS}
        self.assertIn(("booking", "hi"), names)
        self.assertIn(("booking", "en"), names)

    def test_every_case_has_expectation(self):
        for c in cases.SCENARIOS:
            self.assertIn("intent", c["expect"])
            self.assertIn("turns", c)
            self.assertTrue(c["turns"])


class TestScorer(unittest.TestCase):
    def test_perfect_run_scores_full(self):
        case = cases.by_name("booking", "hi")
        run = {"intent": "booking", "entities": {"slot": "tomorrow 10am"}, "cost_paise": 180}
        s = metrics.score(run, case)
        self.assertTrue(s["intent_ok"])
        self.assertTrue(s["task_ok"])

    def test_wrong_intent_fails_task(self):
        case = cases.by_name("booking", "en")
        run = {"intent": "message", "entities": {}, "cost_paise": 150}
        s = metrics.score(run, case)
        self.assertFalse(s["intent_ok"])
        self.assertFalse(s["task_ok"])

    def test_summarize_rates_and_cost(self):
        results = [
            {"intent_ok": True, "task_ok": True, "cost_paise": 100},
            {"intent_ok": True, "task_ok": False, "cost_paise": 200},
        ]
        summary = metrics.summarize(results)
        self.assertEqual(summary["n"], 2)
        self.assertEqual(summary["task_ok_rate"], 0.5)
        self.assertEqual(summary["total_cost_paise"], 300)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
