"""T0.4 ops endpoints (§C.12): /healthz, /readyz, /metrics.

Run: python -m pytest backend/tests/test_ops.py -q
"""
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import ops


def make_client() -> TestClient:
    app = FastAPI()
    app.include_router(ops.router)
    return TestClient(app, raise_server_exceptions=False)


class TestHealthz(unittest.TestCase):
    def test_healthz_200_with_no_deps_configured(self):
        # No DATABASE_URL / REDIS_URL in env: liveness must not check deps.
        c = make_client()
        r = c.get("/healthz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")


class TestReadyz(unittest.TestCase):
    def test_readyz_503_when_postgres_and_redis_down(self):
        # This env runs no PG/Redis: real TCP probes must report down, not crash.
        c = make_client()
        r = c.get("/readyz")
        self.assertEqual(r.status_code, 503)
        body = r.json()
        self.assertFalse(body["ready"])
        self.assertIn("postgres", body["checks"])
        self.assertIn("redis", body["checks"])
        self.assertIn("vendor", body["checks"])
        self.assertFalse(body["checks"]["postgres"]["ok"])
        self.assertFalse(body["checks"]["redis"]["ok"])

    def test_readyz_200_when_all_probes_healthy(self):
        ops.probe_postgres = lambda: {"ok": True, "detail": "tcp"}
        ops.probe_redis = lambda: {"ok": True, "detail": "tcp"}
        ops.probe_vendor = lambda: {"ok": True, "detail": "configured"}
        try:
            c = make_client()
            r = c.get("/readyz")
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.json()["ready"])
        finally:
            ops.probe_postgres = ops._tcp_probe_postgres
            ops.probe_redis = ops._tcp_probe_redis
            ops.probe_vendor = ops._config_probe_vendor


class TestMetrics(unittest.TestCase):
    def test_metrics_exposition(self):
        c = make_client()
        r = c.get("/metrics")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/plain", r.headers["content-type"])
        self.assertIn("medicall_ready", r.text)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
