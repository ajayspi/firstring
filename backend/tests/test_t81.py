"""T8.1 admin dashboard API: calls view, clinic metrics, analytics.

In-memory aggregates. Staging: real calls/clinics tables with rollups.

Run: python -m pytest backend/tests/test_t81.py -q
"""
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import admin

ADMIN_TOKEN = "Bearer admin-token-12345"
BAD_TOKEN = "Bearer nope"
CLINIC_PHONE = "+919876543210"


class AdminCase(unittest.TestCase):
    def setUp(self):
        admin.reset()
        app = FastAPI()
        app.include_router(admin.router)
        self.client = TestClient(app, raise_server_exceptions=False)
        
        # Register test clinic + simulate calls
        admin.register_clinic(CLINIC_PHONE, "free")
        for i in range(3):
            self.client.post(
                f"/admin/clinics/{CLINIC_PHONE}/simulate-call",
                headers={"Authorization": ADMIN_TOKEN},
                json={
                    "caller_phone": f"+9190000000{i:02d}",
                    "outcome": "booking" if i == 0 else "voicemail",
                    "duration_min": 2 + i,
                },
            )


class TestAdminAuth(AdminCase):
    def test_no_token_401(self):
        r = self.client.get("/admin/health")
        self.assertEqual(r.status_code, 401)

    def test_bad_token_401(self):
        r = self.client.get("/admin/health", headers={"Authorization": BAD_TOKEN})
        self.assertEqual(r.status_code, 401)

    def test_good_token_200(self):
        r = self.client.get("/admin/health", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 200)


class TestAdminHealth(AdminCase):
    def test_health_shape(self):
        r = self.client.get("/admin/health", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "healthy")
        self.assertIn("system", body)
        self.assertTrue(body["system"]["total_calls"] > 0)


class TestAdminCalls(AdminCase):
    def test_list_calls(self):
        r = self.client.get("/admin/calls", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 200)
        self.assertGreater(len(r.json()["items"]), 0)

    def test_get_call(self):
        r = self.client.get("/admin/calls", headers={"Authorization": ADMIN_TOKEN})
        call_id = r.json()["items"][0]["id"]
        
        r = self.client.get(f"/admin/calls/{call_id}", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], call_id)

    def test_get_nonexistent_call_404(self):
        r = self.client.get("/admin/calls/nope", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 404)


class TestAdminClinics(AdminCase):
    def test_list_clinics(self):
        r = self.client.get("/admin/clinics", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 200)
        items = r.json()["items"]
        self.assertGreater(len(items), 0)
        self.assertEqual(items[0]["phone"], CLINIC_PHONE)

    def test_clinic_shows_booking_rate(self):
        r = self.client.get("/admin/clinics", headers={"Authorization": ADMIN_TOKEN})
        clinic = r.json()["items"][0]
        self.assertIn("booking_rate", clinic)
        # 1 booking out of 3 calls = 0.333
        self.assertAlmostEqual(clinic["booking_rate"], 0.333, places=2)

    def test_get_clinic_detail(self):
        r = self.client.get(
            f"/admin/clinics/{CLINIC_PHONE}", headers={"Authorization": ADMIN_TOKEN}
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["phone"], CLINIC_PHONE)
        self.assertIn("stats", body)
        self.assertEqual(body["stats"]["bookings"], 1)

    def test_get_nonexistent_clinic_404(self):
        r = self.client.get("/admin/clinics/+919999999999", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 404)


class TestAdminAnalytics(AdminCase):
    def test_analytics_summary(self):
        r = self.client.get("/admin/analytics", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["period_days"], 7)
        self.assertGreater(body["summary"]["total_calls"], 0)
        self.assertGreater(body["summary"]["booking_rate"], 0)

    def test_analytics_by_day(self):
        r = self.client.get("/admin/analytics?days=30", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["period_days"], 30)
        self.assertIn("by_day", body)


class TestAdminConsoleContract(AdminCase):
    """The ops console (components/admin-hud.tsx) reads these exact fields.

    Pinned so a rename in the response can't silently blank the dashboard.
    """

    CONSOLE_CALL_FIELDS = {
        "id", "owner_phone", "caller_phone", "started_at", "duration_sec", "outcome",
    }
    CONSOLE_CLINIC_FIELDS = {"phone", "plan", "calls", "bookings", "booking_rate"}
    CONSOLE_OUTCOMES = {"booking", "message", "voicemail", "dropped"}

    def test_calls_expose_console_fields(self):
        r = self.client.get("/admin/calls", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 200)
        missing = self.CONSOLE_CALL_FIELDS - set(r.json()["items"][0])
        self.assertEqual(missing, set(), f"console fields missing from call: {missing}")

    def test_clinics_expose_console_fields(self):
        r = self.client.get("/admin/clinics", headers={"Authorization": ADMIN_TOKEN})
        self.assertEqual(r.status_code, 200)
        missing = self.CONSOLE_CLINIC_FIELDS - set(r.json()["items"][0])
        self.assertEqual(missing, set(), f"console fields missing from clinic: {missing}")

    def test_started_at_is_parseable_by_the_console(self):
        # the console does Date.parse(started_at) -> epoch ms
        r = self.client.get("/admin/calls", headers={"Authorization": ADMIN_TOKEN})
        raw = r.json()["items"][0]["started_at"]
        self.assertIsInstance(raw, str)
        datetime.fromisoformat(raw)

    def test_outcomes_stay_in_the_console_vocabulary(self):
        r = self.client.get("/admin/calls", headers={"Authorization": ADMIN_TOKEN})
        for call in r.json()["items"]:
            self.assertIn(call["outcome"], self.CONSOLE_OUTCOMES)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
