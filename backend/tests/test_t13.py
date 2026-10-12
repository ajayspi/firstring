"""T1.3 forwarding setup: USSD codes per carrier condition + verify record.

Codes per the brief: *61* no-answer, *62* unreachable, *67* busy, *21* all;
read-back *#61# etc. Live test-call verification happens on staging.

Run: python -m pytest backend/tests/test_t13.py -q
"""
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.services import forwarding as fw

DID = "+911204567890"


class TestCodes(unittest.TestCase):
    def test_setup_codes_embed_did(self):
        codes = fw.setup_codes(DID)
        self.assertEqual(codes["no_answer"], f"*61*{DID}#")
        self.assertEqual(codes["unreachable"], f"*62*{DID}#")
        self.assertEqual(codes["busy"], f"*67*{DID}#")
        self.assertEqual(codes["all"], f"*21*{DID}#")

    def test_readback_codes(self):
        self.assertEqual(
            fw.readback_codes(),
            {"no_answer": "*#61#", "unreachable": "*#62#", "busy": "*#67#", "all": "*#21#"},
        )

    def test_verify_marks_observed(self):
        rec = fw.new_record(DID)
        self.assertFalse(rec["verified"])
        fw.mark_observed(rec, "2026-10-12T07:00:00Z")
        self.assertTrue(rec["verified"])
        self.assertEqual(rec["observed_at"], "2026-10-12T07:00:00Z")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
