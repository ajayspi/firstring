"""T7.2 notification preferences: GET, PUT.

In-memory per-owner settings. Staging: persist to notification_preferences table.

Run: python -m pytest backend/tests/test_t72.py -q
"""
import os
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services import auth as auth_svc
from app.api import notifications

PHONE = "+919876543210"


def make_client() -> tuple:
    box = []

    def sender(phone, code):
        box.append(code)

    otp_id, _ = auth_svc.request_otp(PHONE, sender)
    access, _refresh, _phone = auth_svc.verify_otp(otp_id, box[0])
    app = FastAPI()
    app.include_router(notifications.router)
    return TestClient(app, raise_server_exceptions=False), access


class NotificationsCase(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET"] = "test-secret-1"
        auth_svc._store.clear()
        auth_svc._requests.clear()
        auth_svc._refresh.clear()
        notifications.reset()
        self.client, self.token = make_client()
        self.auth = {"Authorization": f"Bearer {self.token}"}


class TestNotificationsGet(NotificationsCase):
    def test_get_defaults(self):
        r = self.client.get("/notifications/preferences", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        prefs = r.json()
        self.assertTrue(prefs.get("whatsapp"))
        self.assertFalse(prefs.get("email"))
        self.assertFalse(prefs.get("sms"))
        self.assertFalse(prefs.get("push"))


class TestNotificationsUpdate(NotificationsCase):
    def test_update_200(self):
        r = self.client.put(
            "/notifications/preferences",
            headers=self.auth,
            json={"whatsapp": True, "email": True, "sms": False, "push": True},
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["whatsapp"])
        self.assertTrue(r.json()["email"])
        self.assertFalse(r.json()["sms"])
        self.assertTrue(r.json()["push"])

    def test_get_after_update(self):
        self.client.put(
            "/notifications/preferences",
            headers=self.auth,
            json={"whatsapp": True, "email": True, "sms": False, "push": True},
        )
        r = self.client.get("/notifications/preferences", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["email"])


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
