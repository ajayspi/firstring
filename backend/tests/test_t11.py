"""T1.1 webhook receiver (§B.3, §C.10): HMAC verify, dedupe, enqueue-only ack.

Pilot convention: HMAC-SHA256 over the raw body, secret per provider from
env (<PROVIDER>_WEBHOOK_SECRET), header X-Webhook-Signature "sha256=<hex>".
Provider-native schemes (Telnyx ed25519 etc.) land on staging.
Dedupe is in-memory here; staging uses webhook_events' UNIQUE(provider,
event_id). Retry worker: 3 attempts, backoff 1/5/25 s, then dead_letter.

Run: python -m pytest backend/tests/test_t11.py -q
"""
import hashlib
import hmac
import os
import sys
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.services import webhooks as wh

PROVIDER = "exotel"
BODY = b'{"event_id":"evt-1","type":"call.initiated"}'


def sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def make_client() -> TestClient:
    from app.api import telephony

    app = FastAPI()
    app.include_router(telephony.router)
    return TestClient(app, raise_server_exceptions=False)


class TestSignature(unittest.TestCase):
    def setUp(self):
        os.environ["EXOTEL_WEBHOOK_SECRET"] = "wh-secret"
        wh._seen.clear()
        wh._queue.clear()

    def test_bad_signature_401(self):
        c = make_client()
        r = c.post(
            f"/webhooks/telephony/{PROVIDER}/call",
            content=BODY,
            headers={"X-Webhook-Signature": "sha256=deadbeef", "Content-Type": "application/json"},
        )
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"]["code"], "signature_invalid")

    def test_good_signature_200_and_enqueued_not_handled(self):
        c = make_client()
        r = c.post(
            f"/webhooks/telephony/{PROVIDER}/call",
            content=BODY,
            headers={"X-Webhook-Signature": sign(BODY, "wh-secret"), "Content-Type": "application/json"},
        )
        self.assertEqual(r.status_code, 200)
        # §B.3: receiver enqueues only — handler runs zero times inline.
        self.assertEqual(len(wh._queue), 1)
        self.assertEqual(wh._queue[0]["event_id"], "evt-1")

    def test_duplicate_delivery_processed_once(self):
        c = make_client()
        hdr = {"X-Webhook-Signature": sign(BODY, "wh-secret"), "Content-Type": "application/json"}
        c.post(f"/webhooks/telephony/{PROVIDER}/call", content=BODY, headers=hdr)
        r = c.post(f"/webhooks/telephony/{PROVIDER}/call", content=BODY, headers=hdr)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(wh._queue), 1)


class TestRetryWorker(unittest.TestCase):
    def test_three_failures_then_dead_letter(self):
        sleeps = []
        calls = []

        def handler(event):
            calls.append(event["event_id"])
            raise RuntimeError("vendor down")

        event = {"provider": PROVIDER, "event_id": "evt-9", "status": "received", "attempts": 0}
        wh.process_with_retry(event, handler, sleeper=sleeps.append)
        self.assertEqual(event["status"], "dead_letter")
        self.assertEqual(event["attempts"], 4)  # initial try + 3 retries
        self.assertEqual(sleeps, [1, 5, 25])
        self.assertEqual(calls, ["evt-9"] * 4)

    def test_success_on_retry_stops_ladder(self):
        sleeps = []
        calls = []

        def handler(event):
            calls.append(1)
            if len(calls) < 2:
                raise RuntimeError("flaky")
            event["status"] = "done"

        event = {"provider": PROVIDER, "event_id": "evt-2", "status": "received", "attempts": 0}
        wh.process_with_retry(event, handler, sleeper=sleeps.append)
        self.assertEqual(event["status"], "done")
        self.assertEqual(event["attempts"], 1)
        self.assertEqual(sleeps, [1])


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
