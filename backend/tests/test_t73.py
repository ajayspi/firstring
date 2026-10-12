"""T7.3 call tagging: GET, PUT per call.

In-memory per-owner-per-call tags. Staging: persist to call_tags table or call_notes field.

Run: python -m pytest backend/tests/test_t73.py -q
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
from app.api import call_tags

PHONE = "+919876543210"
CALL_ID = "call-001"


def make_client() -> tuple:
    box = []

    def sender(phone, code):
        box.append(code)

    otp_id, _ = auth_svc.request_otp(PHONE, sender)
    access, _refresh, _phone = auth_svc.verify_otp(otp_id, box[0])
    app = FastAPI()
    app.include_router(call_tags.router)
    return TestClient(app, raise_server_exceptions=False), access


class CallTagsCase(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET"] = "test-secret-1"
        auth_svc._store.clear()
        auth_svc._requests.clear()
        auth_svc._refresh.clear()
        call_tags.reset()
        self.client, self.token = make_client()
        self.auth = {"Authorization": f"Bearer {self.token}"}


class TestCallTagsGet(CallTagsCase):
    def test_get_empty(self):
        r = self.client.get(f"/calls/{CALL_ID}/tags", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["tags"], [])


class TestCallTagsUpdate(CallTagsCase):
    def test_put_tags_200(self):
        r = self.client.put(
            f"/calls/{CALL_ID}/tags",
            headers=self.auth,
            json={"tags": ["interested", "follow_up"]},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.json()["tags"]), {"interested", "follow_up"})

    def test_get_after_put(self):
        self.client.put(
            f"/calls/{CALL_ID}/tags",
            headers=self.auth,
            json={"tags": ["spam", "block"]},
        )
        r = self.client.get(f"/calls/{CALL_ID}/tags", headers=self.auth)
        self.assertEqual(set(r.json()["tags"]), {"spam", "block"})

    def test_put_empty_200(self):
        self.client.put(
            f"/calls/{CALL_ID}/tags",
            headers=self.auth,
            json={"tags": ["test"]},
        )
        r = self.client.put(
            f"/calls/{CALL_ID}/tags",
            headers=self.auth,
            json={"tags": []},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["tags"], [])


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
