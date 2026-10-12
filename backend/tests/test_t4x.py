"""T4.x DB-free slices: blocklist gate, prompt compile, usage metering,
hashed-contacts match. Staging backs these with BlocklistEntry /
prompt_versions / billing tables; logic is identical.

Run: python -m pytest backend/tests/test_t4x.py -q
"""
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.services import blocklist, prompts, billing, contacts


class TestBlocklist(unittest.TestCase):
    def setUp(self):
        blocklist._entries.clear()

    def test_blocked_caller_never_reaches_pipeline(self):
        blocklist.block("+911204567890", "spam")
        self.assertTrue(blocklist.is_blocked("+911204567890"))
        self.assertEqual(blocklist.gate_call("+911204567890"), "blocked")
        self.assertEqual(blocklist.gate_call("+919999999999"), "allow")

    def test_unblock_restores(self):
        blocklist.block("+911204567890", "spam")
        blocklist.unblock("+911204567890")
        self.assertFalse(blocklist.is_blocked("+911204567890"))


class TestPrompts(unittest.TestCase):
    def test_compile_embeds_pinned_version(self):
        v = prompts.compile_instructions("Be brief.")
        self.assertIn("[prompt_version:", v["system"])
        self.assertIn("Be brief.", v["system"])

    def test_same_body_same_version(self):
        self.assertEqual(
            prompts.compile_instructions("Be brief.")["id"],
            prompts.compile_instructions("Be brief.")["id"],
        )

    def test_empty_and_too_long_rejected(self):
        with self.assertRaises(prompts.EmptyInstruction):
            prompts.compile_instructions("   ")
        with self.assertRaises(prompts.InstructionTooLong):
            prompts.compile_instructions("x" * 4001)


class TestMetering(unittest.TestCase):
    def test_free_blocks_at_cap_paid_goes_overage(self):
        m = billing.Meter()
        m.add_minutes("free", 20)
        self.assertEqual(m.check("free"), "blocked")
        m2 = billing.Meter()
        m2.add_minutes("solo", 80)
        self.assertEqual(m2.check("solo"), "overage")
        self.assertEqual(m2.usage("solo")["minutes_included"], 80)

    def test_overage_paise_accrues(self):
        m = billing.Meter(overage_paise_per_min=500)
        m.add_minutes("pro", 195)
        self.assertEqual(m.usage("pro")["overage_paise"], 5 * 500)


class TestContacts(unittest.TestCase):
    def test_match_without_raw_numbers(self):
        h1 = "a" * 64
        owner = {h1}
        out = contacts.match([h1, "b" * 64], owner)
        self.assertEqual(out, {"matched": [h1], "unknown": ["b" * 64]})

    def test_raw_number_rejected(self):
        with self.assertRaises(ValueError):
            contacts.match(["+919876543210"], set())


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
