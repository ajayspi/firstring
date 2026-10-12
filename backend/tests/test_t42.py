"""T4.2 calls routes pilot slice: history list, get, transcript, recording redirect.

In-memory call store — staging wires the real calls table. Calls are
seeded as stubs; the real ones land from T1.2 webhook + state machine.

Run: python -m pytest backend/tests/test_t42.py -q
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

from app.services import auth as auth_svc
from app.api import calls

PHONE = "+919876543210"
NOW = datetime(2026, 10, 12, tzinfo=timezone.utc)


def make_client() -> tuple:
    box = []

    def sender(phone, code):
        box.append(code)

    otp_id, _ = auth_svc.request_otp(PHONE, sender)
    access, _refresh, _phone = auth_svc.verify_otp(otp_id, box[0])
    app = FastAPI()
    app.include_router(calls.router)
    return TestClient(app, raise_server_exceptions=False), access


class CallsCase(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET"] = "test-secret-1"
        auth_svc._store.clear()
        auth_svc._requests.clear()
        auth_svc._refresh.clear()
        calls.reset()
        self.client, self.token = make_client()
        self.auth = {"Authorization": f"Bearer {self.token}"}
        calls._calls[PHONE] = [
            {
                "id": "call-1",
                "started_at": NOW.isoformat(),
                "ended_at": (NOW.replace(minute=1)).isoformat(),
                "state": "COMPLETE",
                "outcome": "booking",
                "transcript": [{"role": "ai", "text": "when would you like?"}],
            }
        ]


class TestCallsHistory(CallsCase):
    def test_list_calls(self):
        r = self.client.get("/calls", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["items"]), 1)
        self.assertEqual(r.json()["items"][0]["id"], "call-1")

    def test_get_call(self):
        r = self.client.get("/calls/call-1", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], "call-1")

    def test_get_nonexistent_404(self):
        r = self.client.get("/calls/nope", headers=self.auth)
        self.assertEqual(r.status_code, 404)


class TestTranscript(CallsCase):
    def test_transcript(self):
        r = self.client.get("/calls/call-1/transcript", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["segments"]), 1)
        self.assertEqual(r.json()["segments"][0]["role"], "ai")


class TestRecording(CallsCase):
    def test_recording_302(self):
        r = self.client.get("/calls/call-1/recording", headers=self.auth, allow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers.get("location", "").startswith("s3://"))


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
