"""G1+G2 acceptance tests (stdlib only — no third-party deps required).

RED before fix: main.py imports deleted modules + TalkByte branding;
postgres.py does not parse (`--` comments, wrong Vector import).
GREEN after fix: both files parse, imports reference on-disk modules only,
branding is MediCall AI, models match the medical domain.

Run: python3 tests/test_g1_g2.py  (exit 0 = green)
"""
import ast
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
MAIN_PY = BACKEND / "main.py"
POSTGRES_PY = BACKEND / "app" / "db" / "postgres.py"

DELETED_MODULES = [
    "app.api.orders",
    "app.api.restaurants",
    "app.api.payments",
    "app.api.admin",
    "app.db.supabase",
    "app.workers.celery_app",
]


def parse_source(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def imported_modules(tree: ast.Module) -> set:
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
        elif isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name)
    return mods


class TestG1MainPy(unittest.TestCase):
    def test_main_parses(self):
        parse_source(MAIN_PY)

    def test_main_does_not_import_deleted_modules(self):
        mods = imported_modules(parse_source(MAIN_PY))
        for dead in DELETED_MODULES:
            self.assertNotIn(
                dead, mods, f"main.py still imports deleted module {dead}"
            )

    def test_main_imports_resolve_to_files_on_disk(self):
        mods = imported_modules(parse_source(MAIN_PY))
        for mod in sorted(mods):
            if not mod.startswith("app."):
                continue
            rel = Path(*mod.split(".")).with_suffix(".py")
            pkg_init = Path(*mod.split(".")) / "__init__.py"
            pkg_dir = Path(*mod.split("."))
            self.assertTrue(
                (BACKEND / rel).exists()
                or (BACKEND / pkg_init).exists()
                or (BACKEND / pkg_dir).is_dir(),
                f"main.py imports {mod} but no such file exists on disk",
            )

    def test_main_branding_is_medicall(self):
        src = MAIN_PY.read_text(encoding="utf-8")
        self.assertNotIn("TalkByte", src)
        self.assertNotIn("Australian", src)
        self.assertNotIn("supabase", src.lower())
        self.assertIn("MediCall", src)

    def test_health_endpoint_is_medicall(self):
        src = MAIN_PY.read_text(encoding="utf-8")
        self.assertIn("medicall-api", src)
        self.assertNotIn("talkbyte-api", src)


class TestG2PostgresPy(unittest.TestCase):
    def test_postgres_parses(self):
        parse_source(POSTGRES_PY)

    def test_no_sql_style_comments(self):
        for i, line in enumerate(
            POSTGRES_PY.read_text(encoding="utf-8").splitlines(), 1
        ):
            stripped = line.strip()
            if stripped.startswith("--"):
                self.fail(f"postgres.py line {i} uses SQL '--' comment in Python")

    def test_vector_import_is_pgvector(self):
        mods = imported_modules(parse_source(POSTGRES_PY))
        self.assertIn(
            "pgvector.sqlalchemy", mods,
            "Vector must come from pgvector.sqlalchemy, not sqlalchemy",
        )

    def test_required_models_defined(self):
        tree = parse_source(POSTGRES_PY)
        classes = {
            n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
        }
        for cls in (
            "Clinic",
            "ClinicUser",
            "Call",
            "Appointment",
            "Prescription",
            "CallEmbedding",
            "LanguageCode",
        ):
            self.assertIn(cls, classes, f"missing model class {cls}")

    def test_medical_domain_no_restaurant_fields(self):
        src = POSTGRES_PY.read_text(encoding="utf-8")
        for leftover in ("restaurant_id", "order_items", "TAKING_ORDER", "POS_FAILED"):
            self.assertNotIn(leftover, src)

    def test_call_state_is_medical(self):
        src = POSTGRES_PY.read_text(encoding="utf-8")
        for state in ("TRIAGE", "APPOINTMENT", "PRESCRIPTION", "ESCALATED"):
            self.assertIn(state, src)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
