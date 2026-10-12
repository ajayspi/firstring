"""Usage metering + tier caps (§7.3, T4.5).

Free blocks at cap; paid tiers bill overage. `free` is the only blocking
tier — the pilot must never silently bill a clinic that never agreed.
"""

CAPS_MINUTES = {"free": 20, "solo": 80, "pro": 190, "gold": 500}
BLOCKING_PLANS = frozenset({"free"})
DEFAULT_OVERAGE_PAISE_PER_MIN = 500  # ₹5/min — planning estimate, replaced by T3.4


class Meter:
    def __init__(self, overage_paise_per_min: int = DEFAULT_OVERAGE_PAISE_PER_MIN):
        self._used: dict = {}
        self.overage_paise_per_min = overage_paise_per_min

    def add_minutes(self, plan: str, minutes: int) -> None:
        self._used[plan] = self._used.get(plan, 0) + minutes

    def check(self, plan: str) -> str:
        """'ok' | 'overage' | 'blocked' — checked before each call is accepted."""
        cap = CAPS_MINUTES[plan]
        used = self._used.get(plan, 0)
        if used < cap:
            return "ok"
        return "blocked" if plan in BLOCKING_PLANS else "overage"

    def usage(self, plan: str) -> dict:
        cap = CAPS_MINUTES[plan]
        used = self._used.get(plan, 0)
        over = max(0, used - cap)
        return {
            "minutes_used": used,
            "minutes_included": cap,
            "overage_paise": over * self.overage_paise_per_min,
        }
