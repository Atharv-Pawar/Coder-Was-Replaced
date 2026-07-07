"""
Economy system — Phase 5.

Six currencies, a passive salary tick, and a shop with upgrades that
have real mechanical effects on gameplay.

Currency overview
-----------------
  salary          — primary spendable currency ($ icon)
  reputation      — quality-of-work score, shown as social proof
  git_stars       — impact metric from commits and deployments
  coffee_count    — cups of coffee consumed (energy management stat)
  compute_credits — infra currency from server/test/deploy work

XP is tracked in Progression (Phase 4) — not duplicated here.

Passive income
--------------
Every ECONOMY_TICK_INTERVAL seconds the robot earns a salary based on
its current level. Higher levels = more salary per tick.

Shop upgrades (Phase 5 — 4 items)
----------------------------------
  better_coffee   $50   Coffee restores 40 energy instead of 20
  standing_desk   $120  Robot moves 25% faster between tiles
  mech_keyboard   $250  Script executes 25% faster between steps
  ai_assistant    $600  look() returns two tiles ahead (teaser for Phase 7)

Phase 6+ will add: CI/CD, cloud servers, GPU cluster, quantum compiler.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from engine import constants as c


# ── Passive salary per tick, indexed by Progression.level_index ────────────
_SALARY_BY_LEVEL = [1, 2, 4, 7, 12, 20, 35, 60, 100]


# ── Currency award amounts (single source of truth) ─────────────────────────
AWARD_FIX_BUG      = dict(salary=5,  reputation=2)
AWARD_COFFEE       = dict(coffee_count=1)
AWARD_COMMIT       = dict(salary=3,  reputation=1, git_stars=1)
AWARD_DEPLOY       = dict(salary=20, reputation=10, git_stars=3, compute_credits=10)
AWARD_RUN_TESTS    = dict(salary=5,  reputation=3,  compute_credits=5)
AWARD_ANSWER_EMAIL = dict(salary=8,  reputation=5)
AWARD_REFACTOR     = dict(salary=10, reputation=4,  git_stars=1, compute_credits=3)


# ── Shop items ───────────────────────────────────────────────────────────────
@dataclass
class ShopItem:
    item_id: str
    name: str
    cost_salary: int
    description: str
    effect_line: str          # short one-liner shown in the shop
    phase_available: int = 5  # which phase introduced this item


SHOP_ITEMS: list[ShopItem] = [
    ShopItem(
        "better_coffee", "Better Coffee Machine", 50,
        "Upgraded grinder and beans.",
        "+40 energy per coffee  (was +20)",
    ),
    ShopItem(
        "standing_desk", "Standing Desk", 120,
        "Ergonomic, height-adjustable.",
        "Robot moves 25% faster between tiles",
    ),
    ShopItem(
        "mech_keyboard", "Mechanical Keyboard", 250,
        "Tactile switches. Very clicky.",
        "Script executes 25% faster",
    ),
    ShopItem(
        "ai_assistant", "AI Code Assistant", 600,
        "Autocomplete for your brain.",
        "look() sees two tiles ahead (Phase 7)",
    ),
    ShopItem(
        "ci_cd", "CI/CD Pipeline", 1_200,
        "Automated build and deploy.",
        "Auto-run tests on every commit (Phase 6)",
    ),
    ShopItem(
        "cloud_servers", "Cloud Servers", 3_000,
        "Unlimited scale-out.",
        "Doubles compute_credits income (Phase 6)",
    ),
]


class Economy:
    """
    Tracks all currencies, drives passive income, and manages upgrades.

    Usage:
      economy.update(dt, event_bus)        — call every frame
      economy.award(event_bus, **kwargs)   — give currencies after an action
      economy.buy(item_id)                 — attempt a shop purchase
      economy.has_upgrade(item_id)         — check if an upgrade is active
    """

    def __init__(self):
        # ── Currencies ──────────────────────────────────────────────────
        self.salary: int = 0
        self.reputation: int = 0
        self.git_stars: int = 0
        self.coffee_count: int = 0
        self.compute_credits: int = 0

        # ── Passive income ───────────────────────────────────────────────
        self._tick_timer: float = 0.0
        self.tick_interval: float = c.ECONOMY_TICK_INTERVAL

        # ── Upgrades ─────────────────────────────────────────────────────
        self.upgrades: set[str] = set()
        self.total_spent: int = 0

        # For the "recent income" sparkle in the HUD.
        self._last_tick_salary: int = 0

    # ── Frame update ────────────────────────────────────────────────────
    def update(self, dt: float, progression, event_bus=None) -> None:
        self._tick_timer += dt
        if self._tick_timer >= self.tick_interval:
            self._tick_timer -= self.tick_interval
            self._passive_tick(progression, event_bus)

    def _passive_tick(self, progression, event_bus) -> None:
        level_idx = min(progression.level_index, len(_SALARY_BY_LEVEL) - 1)
        amount = _SALARY_BY_LEVEL[level_idx]
        self.salary += amount
        self._last_tick_salary = amount
        if event_bus:
            event_bus.notify(f"+${amount} salary")

    # ── Currency award ───────────────────────────────────────────────────
    def award(self, event_bus=None, **currencies) -> None:
        """Give one or more currencies at once.

        Example: economy.award(event_bus, salary=5, reputation=2)
        """
        for key, amount in currencies.items():
            if hasattr(self, key) and amount:
                setattr(self, key, getattr(self, key) + amount)

    # ── Shop ─────────────────────────────────────────────────────────────
    def buy(self, item_id: str, event_bus=None) -> tuple[bool, str]:
        """Attempt to purchase an upgrade. Returns (success, message)."""
        item = self._item_for(item_id)
        if item is None:
            return False, "Unknown item."
        if item_id in self.upgrades:
            return False, f"Already owned: {item.name}"
        if self.salary < item.cost_salary:
            need = item.cost_salary - self.salary
            return False, f"Need ${need} more salary."
        self.salary -= item.cost_salary
        self.total_spent += item.cost_salary
        self.upgrades.add(item_id)
        if event_bus:
            event_bus.notify(f"Bought: {item.name}!")
        return True, f"Purchased {item.name}."

    def has_upgrade(self, item_id: str) -> bool:
        return item_id in self.upgrades

    def can_afford(self, item_id: str) -> bool:
        item = self._item_for(item_id)
        return item is not None and self.salary >= item.cost_salary

    # ── Upgrade effect values ────────────────────────────────────────────
    def coffee_energy_restore(self) -> float:
        return 40.0 if self.has_upgrade("better_coffee") else c.COFFEE_ENERGY_RESTORE

    def move_duration_multiplier(self) -> float:
        return 0.75 if self.has_upgrade("standing_desk") else 1.0

    def script_speed_multiplier(self) -> float:
        return 0.75 if self.has_upgrade("mech_keyboard") else 1.0

    def look_range(self) -> int:
        """Number of tiles look() can see ahead (ai_assistant = 2)."""
        return 2 if self.has_upgrade("ai_assistant") else 1

    # ── Helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _item_for(item_id: str) -> ShopItem | None:
        for item in SHOP_ITEMS:
            if item.item_id == item_id:
                return item
        return None

    @property
    def affordable_items(self) -> list[ShopItem]:
        return [i for i in SHOP_ITEMS if i.item_id not in self.upgrades]

    @property
    def tick_progress(self) -> float:
        """0.0–1.0: how far through the current salary tick we are."""
        return min(1.0, self._tick_timer / self.tick_interval)
