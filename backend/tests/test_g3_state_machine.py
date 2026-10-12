"""G3 acceptance tests: single medical state machine (stdlib only).

RED before fix: models/call.py is restaurant flow (TAKING_ORDER,
restaurant_id, order_items); postgres.py defines a duplicate CallState;
schema comment describes the old chain.
GREEN after fix: models/call.py is the canonical medical state machine,
postgres.py imports CallState from it, schema comment fixed.

Run: python3 tests/test_g3_state_machine.py  (exit 0 = green)
"""
import ast
import importlib.util
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
MODELS_CALL = BACKEND / "app" / "models" / "call.py"
POSTGRES_PY = BACKEND / "app" / "db" / "postgres.py"
SCHEMA_SQL = BACKEND / "postgres_schema.sql"

MEDICAL_STATES = {
    "GREETING",
    "TRIAGE",
    "APPOINTMENT",
    "PRESCRIPTION",
    "COMPLETE",
    "ESCALATED",
    "DROPPED",
    "PAYMENT_SENT",
    "PAYMENT_EXPIRED",
}
RESTAURANT_STATES = {
    "TAKING_ORDER",
    "CONFIRMING",
    "CONFIRMED",
    "TRANSFER_TO_HUMAN",
    "POS_FAILED",
    "CALL_DROPPED",
}


def parse_source(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def load_models_call():
    spec = importlib.util.spec_from_file_location(
        "g3_models_call", str(MODELS_CALL)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCanonicalStateMachine(unittest.TestCase):
    def test_models_call_parses(self):
        parse_source(MODELS_CALL)

    def test_medical_states_present(self):
        src = MODELS_CALL.read_text(encoding="utf-8")
        for state in MEDICAL_STATES:
            self.assertIn(state, src, f"missing medical state {state}")

    def test_no_restaurant_states_or_fields(self):
        src = MODELS_CALL.read_text(encoding="utf-8")
        for leftover in (
            *RESTAURANT_STATES,
            "restaurant_id",
            "order_items",
            "rag_menu",
        ):
            self.assertNotIn(leftover, src, f"restaurant leftover: {leftover}")

    def test_transitions_valid(self):
        m = load_models_call()
        CallState = m.CallState
        call = m.Call(
            id="c1",
            clinic_id="k1",
            caller_number="+911234567890",
            state=CallState.GREETING,
            started_at=None,
        )
        self.assertTrue(call.can_transition(CallState.TRIAGE))
        self.assertTrue(call.transition(CallState.TRIAGE))
        self.assertEqual(call.state, CallState.TRIAGE)

    def test_transitions_invalid_rejected(self):
        m = load_models_call()
        CallState = m.CallState
        call = m.Call(
            id="c1",
            clinic_id="k1",
            caller_number="+911234567890",
            state=CallState.GREETING,
            started_at=None,
        )
        self.assertFalse(call.can_transition(CallState.COMPLETE))
        self.assertFalse(call.transition(CallState.COMPLETE))
        self.assertEqual(call.state, CallState.GREETING)

    def test_terminal_states_have_no_exits(self):
        m = load_models_call()
        CallState = m.CallState
        for terminal in (
            CallState.COMPLETE,
            CallState.ESCALATED,
            CallState.DROPPED,
        ):
            call = m.Call(
                id="c1",
                clinic_id="k1",
                caller_number="+911234567890",
                state=terminal,
                started_at=None,
            )
            for target in CallState:
                self.assertFalse(
                    call.can_transition(target),
                    f"{terminal} should be terminal but allows {target}",
                )


class TestSingleSourceOfTruth(unittest.TestCase):
    def test_postgres_does_not_redefine_callstate(self):
        tree = parse_source(POSTGRES_PY)
        classes = {
            n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
        }
        self.assertNotIn(
            "CallState", classes, "postgres.py must not define its own CallState"
        )

    def test_postgres_imports_callstate_from_models(self):
        tree = parse_source(POSTGRES_PY)
        found = False
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module == "app.models.call"
                and any(a.name == "CallState" for a in node.names)
            ):
                found = True
        self.assertTrue(
            found, "postgres.py must import CallState from app.models.call"
        )

    def test_schema_comment_is_medical(self):
        src = SCHEMA_SQL.read_text(encoding="utf-8")
        self.assertNotIn("TAKING_ORDER", src)
        self.assertIn("TRIAGE", src)


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=1)
    sys.exit(0 if result.result.wasSuccessful() else 1)
