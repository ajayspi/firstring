"""T0.2 datastore (§1, §7.6): missing tables + retention windows.

- Retention cutoffs are pure date math (stdlib only) — real behavior tests.
- New §1 tables must exist as models (postgres.py) and as prod DDL
  (postgres_schema.sql); structural tests (repo's AST/text style) guard both.
- Live-DB accepts (create_all smoke, migrate/rollback, dry-run on real rows)
  are deferred to staging with PG — see ledger.

Run: python -m pytest backend/tests/test_t02.py -q
"""
import ast
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

POSTGRES_PY = BACKEND / "app" / "db" / "postgres.py"
SCHEMA_SQL = BACKEND / "postgres_schema.sql"

NEW_TABLES = {
    "WebhookEvent": "webhook_events",
    "CallEvent": "call_events",
    "PromptVersion": "prompt_versions",
    "VoiceConfig": "voice_configs",
    "EvalCase": "eval_cases",
    "EvalRun": "eval_runs",
    "Notification": "notifications",
    "BlocklistEntry": "blocklist",
    "OutboxEntry": "outbox",
}

NOW = datetime(2026, 10, 12, tzinfo=timezone.utc)


class TestRetentionWindows(unittest.TestCase):
    def test_cutoffs_match_section_76(self):
        from app.workers.retention import cutoff
        self.assertEqual(cutoff("recordings", NOW), NOW - timedelta(days=90))
        self.assertEqual(cutoff("transcripts", NOW), NOW - timedelta(days=365))
        self.assertEqual(cutoff("embeddings", NOW), NOW - timedelta(days=365))
        self.assertEqual(cutoff("metadata", NOW), NOW - timedelta(days=730))

    def test_is_expired_boundary(self):
        from app.workers.retention import is_expired
        # Exactly at the cutoff is expired (delete only expired rows).
        self.assertTrue(is_expired("recordings", NOW - timedelta(days=90), NOW))
        self.assertFalse(
            is_expired("recordings", NOW - timedelta(days=90) + timedelta(seconds=1), NOW)
        )
        self.assertFalse(is_expired("metadata", NOW - timedelta(days=729), NOW))

    def test_unknown_kind_raises(self):
        from app.workers.retention import cutoff
        with self.assertRaises(KeyError):
            cutoff("nope", NOW)


class TestNewModels(unittest.TestCase):
    def test_model_classes_defined(self):
        tree = ast.parse(POSTGRES_PY.read_text(encoding="utf-8"))
        classes = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
        for cls in NEW_TABLES:
            self.assertIn(cls, classes, f"missing model class {cls}")

    def test_model_tablenames_match(self):
        src = POSTGRES_PY.read_text(encoding="utf-8")
        for table in NEW_TABLES.values():
            self.assertIn(f'__tablename__ = "{table}"', src)


class TestNewSchemaDDL(unittest.TestCase):
    def _blocks(self) -> dict:
        src = SCHEMA_SQL.read_text(encoding="utf-8")
        blocks = {}
        for chunk in src.split("CREATE TABLE"):
            if "(" not in chunk:
                continue
            name = chunk.split("(")[0].strip().strip('"').split()[-1]
            stmt = "CREATE TABLE" + chunk.split(";")[0] + ";"
            blocks[name] = stmt
        return blocks

    def test_all_new_tables_have_ddl(self):
        blocks = self._blocks()
        for table in NEW_TABLES.values():
            self.assertIn(table, blocks, f"missing DDL for {table}")

    def test_ddl_statements_balanced(self):
        for name, stmt in self._blocks().items():
            self.assertEqual(
                stmt.count("("), stmt.count(")"), f"unbalanced parens in {name}"
            )

    def test_webhook_dedupe_key(self):
        blocks = self._blocks()
        self.assertIn("event_id", blocks["webhook_events"])
        self.assertIn("UNIQUE", blocks["webhook_events"])

    def test_outbox_dedupe_key(self):
        blocks = self._blocks()
        self.assertIn("dedupe_key", blocks["outbox"])
        self.assertIn("UNIQUE", blocks["outbox"])


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
