"""T7.1 device pairing routes: register, list, revoke.

In-memory per-owner device registry. Staging: persist to devices table.

Run: python -m pytest backend/tests/test_t71.py -q
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
from app.api import devices

PHONE = "+919876543210"
DEVICE_ID = "device-12345"


def make_client() -> tuple:
    box = []

    def sender(phone, code):
        box.append(code)

    otp_id, _ = auth_svc.request_otp(PHONE, sender)
    access, _refresh, _phone = auth_svc.verify_otp(otp_id, box[0])
    app = FastAPI()
    app.include_router(devices.router)
    return TestClient(app, raise_server_exceptions=False), access


class DevicesCase(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET"] = "test-secret-1"
        auth_svc._store.clear()
        auth_svc._requests.clear()
        auth_svc._refresh.clear()
        devices.reset()
        self.client, self.token = make_client()
        self.auth = {"Authorization": f"Bearer {self.token}"}


class TestDevicesRegister(DevicesCase):
    def test_register_201(self):
        r = self.client.post(
            "/devices",
            headers=self.auth,
            json={"device_id": DEVICE_ID, "name": "Clinic iPad"},
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["device_id"], DEVICE_ID)
        self.assertEqual(r.json()["name"], "Clinic iPad")
        self.assertIn("registered_at", r.json())

    def test_duplicate_409(self):
        self.client.post(
            "/devices",
            headers=self.auth,
            json={"device_id": DEVICE_ID, "name": "Device 1"},
        )
        r = self.client.post(
            "/devices",
            headers=self.auth,
            json={"device_id": DEVICE_ID, "name": "Device 2"},
        )
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()["error"]["code"], "already_registered")


class TestDevicesList(DevicesCase):
    def test_empty_list(self):
        r = self.client.get("/devices", headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["items"], [])

    def test_list_after_register(self):
        self.client.post(
            "/devices",
            headers=self.auth,
            json={"device_id": DEVICE_ID, "name": "iPad"},
        )
        r = self.client.get("/devices", headers=self.auth)
        self.assertEqual(len(r.json()["items"]), 1)
        self.assertEqual(r.json()["items"][0]["device_id"], DEVICE_ID)


class TestDevicesRevoke(DevicesCase):
    def test_revoke_204(self):
        self.client.post(
            "/devices",
            headers=self.auth,
            json={"device_id": DEVICE_ID, "name": "iPad"},
        )
        r = self.client.delete(f"/devices/{DEVICE_ID}", headers=self.auth)
        self.assertEqual(r.status_code, 204)
        r = self.client.get("/devices", headers=self.auth)
        self.assertEqual(len(r.json()["items"]), 0)

    def test_revoke_nonexistent_404(self):
        r = self.client.delete("/devices/nope", headers=self.auth)
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
