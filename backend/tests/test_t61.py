"""T6.1 caller profiles: list, create, update.

In-memory per-owner profiles keyed by caller phone.

Run: python -m pytest backend/tests/test_t61.py -q
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
from app.api import profiles

PHONE = "+919876543210"
CALLER = "+911234567890"


def make_client() -> tuple:
    box = []

    def sender(phone, code):
        box.append(code)

    otp_id, _ = auth_svc.request_otp(PHONE, sender)
    access, _refresh, _phone = auth_svc.verify_otp(otp_id, box[0])
    app = FastAPI()
    app.include_router(profiles.router)
    return TestClient(app, raise_server_exceptions=False), access


class ProfilesCase(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET"] = "test-secret-1"
        auth_svc._store.clear()
        auth_svc._requests.clear()
        auth_svc._refresh.clear()
        profiles.reset()
        self.client, self.token = make_client()
        self.auth = {"Authorization": f"Bearer {self.token}"}


class TestProfilesList(ProfilesCase):
    def test_empty_list(self):
        r = self.client.get("/profiles", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["items"], [])

    def test_list_after_create(self):
        self.client.post("/profiles", headers=self.auth, json={"phone": CALLER, "notes": "VIP"})
        r = self.client.get("/profiles", headers=self.auth)
        self.assertEqual(len(r.json()["items"]), 1)
        self.assertEqual(r.json()["items"][0]["phone"], CALLER)


class TestProfilesCreate(ProfilesCase):
    def test_create_201(self):
        r = self.client.post("/profiles", headers=self.auth, json={"phone": CALLER, "notes": "Regular patient"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["phone"], CALLER)
        self.assertEqual(r.json()["notes"], "Regular patient")

    def test_duplicate_409(self):
        self.client.post("/profiles", headers=self.auth, json={"phone": CALLER})
        r = self.client.post("/profiles", headers=self.auth, json={"phone": CALLER})
        self.assertEqual(r.status_code, 409)


class TestProfilesUpdate(ProfilesCase):
    def test_update_nonexistent_404(self):
        r = self.client.put("/profiles/" + CALLER, headers=self.auth, json={"phone": CALLER, "notes": "test"})
        self.assertEqual(r.status_code, 404)

    def test_update_200(self):
        self.client.post("/profiles", headers=self.auth, json={"phone": CALLER, "notes": "initial"})
        r = self.client.put("/profiles/" + CALLER, headers=self.auth, json={"phone": CALLER, "notes": "updated"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["notes"], "updated")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
