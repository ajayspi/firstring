"""Deterministic eval scorer (T3.2 core). Compares a run log against the
case expectation; summarize aggregates a run for the gate report."""


def score(run: dict, case: dict) -> dict:
    """run: {intent, entities, cost_paise} → {intent_ok, task_ok, cost_paise}."""
    expect = case["expect"]
    intent_ok = run.get("intent") == expect["intent"]
    entities_ok = all(
        run.get("entities", {}).get(k) == v for k, v in expect.get("entities", {}).items()
    )
    return {
        "intent_ok": intent_ok,
        "task_ok": intent_ok and entities_ok,
        "cost_paise": run.get("cost_paise", 0),
    }


def summarize(results: list) -> dict:
    n = len(results)
    task_ok = sum(1 for r in results if r["task_ok"])
    return {
        "n": n,
        "task_ok_rate": (task_ok / n) if n else 0.0,
        "total_cost_paise": sum(r.get("cost_paise", 0) for r in results),
    }
