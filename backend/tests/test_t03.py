"""T0.3 secrets + auth (§C.1): OTP round-trip, JWT rotation without restart.

Sender is injectable (stub here; DLT sender on staging). Time is injectable
for expiry. Secret is read from env on every operation — rotation needs no
restart, and no key lives in code.

Run: python -m pytest backend/tests/test_t03.py -q
"""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services import auth as auth_svc

NOW = datetime(2026, 10, 12, tzinfo=timezone.utc)
PHONE = "+919876543210"


class SentBox:
    def __init__(self):
        self.msgs = []

    def __call__(self, phone: str, code: str) -> None:
        self.msgs.append((phone, code))


def make_client(sender) -> TestClient:
    from app.api import auth as auth_api

    auth_api._sender = sender
    app = FastAPI()
    app.include_router(auth_api.router)
    return TestClient(app, raise_server_exceptions=False)


class TestOtpRoundTrip(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET"] = "test-secret-1"
        auth_svc._store.clear()
        auth_svc._requests.clear()
        auth_svc._refresh.clear()

    def test_request_then_verify_round_trip(self):
        box = SentBox()
        c = make_client(box)
        r1 = c.post("/auth/otp/request", json={"phone_e164": PHONE})
        self.assertEqual(r1.status_code, 202)
        otp_id = r1.json()["otp_id"]
        self.assertEqual(len(box.msgs), 1)
        code = box.msgs[0][1]
        r2 = c.post("/auth/otp/verify", json={"otp_id": otp_id, "code": code})
        self.assertEqual(r2.status_code, 200)
        body = r2.json()
        self.assertIn("access_token", body)
        self.assertIn("refresh_token", body)

    def test_wrong_code_401(self):
        c = make_client(SentBox())
        otp_id = c.post("/auth/otp/request", json={"phone_e164": PHONE}).json()["otp_id"]
        r = c.post("/auth/otp/verify", json={"otp_id": otp_id, "code": "000000"})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"]["code"], "otp_invalid")

    def test_expired_code_410(self):
        box = SentBox()
        c = make_client(box)
        otp_id = c.post("/auth/otp/request", json={"phone_e164": PHONE}).json()["otp_id"]
        auth_svc._store[otp_id]["expires_at"] = datetime.now(timezone.utc) - timedelta(
            seconds=1
        )
        r = c.post("/auth/otp/verify", json={"otp_id": otp_id, "code": box.msgs[0][1]})
        self.assertEqual(r.status_code, 410)

    def test_fourth_request_in_10min_429(self):
        c = make_client(SentBox())
        for _ in range(3):
            self.assertEqual(
                c.post("/auth/otp/request", json={"phone_e164": PHONE}).status_code, 202
            )
        r = c.post("/auth/otp/request", json={"phone_e164": PHONE})
        self.assertEqual(r.status_code, 429)
        self.assertEqual(r.json()["error"]["code"], "otp_rate_limited")

    def test_bad_phone_422(self):
        c = make_client(SentBox())
        r = c.post("/auth/otp/request", json={"phone_e164": "98765"})
        self.assertEqual(r.status_code, 422)


class TestRotationWithoutRestart(unittest.TestCase):
    def setUp(self):
        auth_svc._store.clear()
        auth_svc._requests.clear()
        auth_svc._refresh.clear()

    def test_rotate_secret_kills_old_tokens_no_restart(self):
        os.environ["JWT_SECRET"] = "secret-A"
        box = SentBox()
        c = make_client(box)
        otp_id = c.post("/auth/otp/request", json={"phone_e164": PHONE}).json()["otp_id"]
        old_access = c.post(
            "/auth/otp/verify", json={"otp_id": otp_id, "code": box.msgs[0][1]}
        ).json()["access_token"]
        # Rotate: env change only, same process.
        os.environ["JWT_SECRET"] = "secret-B"
        r = c.post("/auth/refresh", json={"refresh_token": "bogus"})
        self.assertEqual(r.status_code, 401)
        self.assertFalse(auth_svc.verify_access(old_access))


class TestRefreshLogout(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET"] = "test-secret-1"
        auth_svc._store.clear()
        auth_svc._requests.clear()
        auth_svc._refresh.clear()

    def test_refresh_then_logout(self):
        box = SentBox()
        c = make_client(box)
        otp_id = c.post("/auth/otp/request", json={"phone_e164": PHONE}).json()["otp_id"]
        refresh = c.post(
            "/auth/otp/verify", json={"otp_id": otp_id, "code": box.msgs[0][1]}
        ).json()["refresh_token"]
        r1 = c.post("/auth/refresh", json={"refresh_token": refresh})
        self.assertEqual(r1.status_code, 200)
        self.assertIn("access_token", r1.json())
        self.assertEqual(c.post("/auth/logout", json={"refresh_token": refresh}).status_code, 204)
        r2 = c.post("/auth/refresh", json={"refresh_token": refresh})
        self.assertEqual(r2.status_code, 401)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
