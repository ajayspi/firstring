"""T4.1 owner routes pilot slice: auth gate, /me, /instructions, /blocklist,
/billing/usage, /contacts/sync — all in-memory until staging PG lands.

Run: python -m pytest backend/tests/test_t41.py -q
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
from app.api import owner

PHONE = "+919876543210"


def make_client() -> tuple:
    box = []

    def sender(phone, code):
        box.append(code)

    otp_id, _ = auth_svc.request_otp(PHONE, sender)
    access, _refresh, _phone = auth_svc.verify_otp(otp_id, box[0])
    app = FastAPI()
    app.include_router(owner.router)
    return TestClient(app, raise_server_exceptions=False), access


class OwnerCase(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET"] = "test-secret-1"
        auth_svc._store.clear()
        auth_svc._requests.clear()
        auth_svc._refresh.clear()
        owner.reset()
        self.client, self.token = make_client()
        self.auth = {"Authorization": f"Bearer {self.token}"}


class TestAuthGate(OwnerCase):
    def test_no_token_401(self):
        r = self.client.get("/me")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"]["code"], "unauthorized")

    def test_bad_token_401(self):
        r = self.client.get("/me", headers={"Authorization": "Bearer nope"})
        self.assertEqual(r.status_code, 401)


class TestMe(OwnerCase):
    def test_me_shape(self):
        r = self.client.get("/me", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["phone"], PHONE)
        self.assertEqual(r.json()["plan"], "free")


class TestInstructions(OwnerCase):
    def test_round_trip_and_compile(self):
        h = self.auth
        self.assertEqual(self.client.get("/instructions", headers=h).json()["body"], "")
        r = self.client.put("/instructions", headers=h, json={"body": "Book only before 8pm."})
        self.assertEqual(r.status_code, 200)
        r = self.client.post("/instructions/compile", headers=h)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["prompt_version_id"].startswith("pv-"))

    def test_empty_422_too_long_422(self):
        h = self.auth
        self.assertEqual(self.client.put("/instructions", headers=h, json={"body": "   "}).status_code, 422)
        self.assertEqual(
            self.client.put("/instructions", headers=h, json={"body": "x" * 4001}).status_code, 422
        )


class TestBlocklist(OwnerCase):
    def test_crud(self):
        h = self.auth
        r = self.client.post("/blocklist", headers=h, json={"e164": "+911204567890", "reason": "spam"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/blocklist", headers=h, json={"e164": "+911204567890"})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "already_blocked")
        self.assertEqual(len(self.client.get("/blocklist", headers=h).json()["items"]), 1)
        self.assertEqual(self.client.delete("/blocklist/+911204567890", headers=h).status_code, 204)
        self.assertEqual(self.client.delete("/blocklist/+911204567890", headers=h).status_code, 404)


class TestBillingUsage(OwnerCase):
    def test_usage_shape(self):
        r = self.client.get("/billing/usage", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["plan"], "free")
        self.assertEqual(body["minutes_included"], 20)
        self.assertEqual(body["minutes_used"], 0)


class TestContactsSync(OwnerCase):
    def test_hashes_match(self):
        owner._patients[PHONE] = {"a" * 64}
        r = self.client.post(
            "/contacts/sync",
            headers=self.auth,
            json={"hashes": ["a" * 64, "b" * 64]},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"matched": ["a" * 64], "unknown": ["b" * 64]})

    def test_raw_number_rejected(self):
        r = self.client.post(
            "/contacts/sync", headers=self.auth, json={"hashes": ["+919876543210"]}
        )
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
