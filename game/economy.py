"""Economy system — Phase 5: currencies, passive income, shop upgrades."""
from __future__ import annotations
from dataclasses import dataclass
from engine import constants as c

_SALARY_BY_LEVEL = [1, 2, 4, 7, 12, 20, 35, 60, 100]

# Economy award dicts (imported by scripting engine)
AWARD_FIX_BUG      = dict(salary=5,  reputation=2)
AWARD_COFFEE       = dict(coffee_count=1)
AWARD_COMMIT       = dict(salary=3,  reputation=1, git_stars=1)
AWARD_DEPLOY       = dict(salary=20, reputation=10, git_stars=3, compute_credits=10)
AWARD_RUN_TESTS    = dict(salary=5,  reputation=3,  compute_credits=5)
AWARD_ANSWER_EMAIL = dict(salary=8,  reputation=5)
AWARD_REFACTOR     = dict(salary=10, reputation=4,  git_stars=1, compute_credits=3)


@dataclass
class ShopItem:
    item_id: str
    name: str
    cost_salary: int
    description: str
    effect_line: str


SHOP_ITEMS: list[ShopItem] = [
    ShopItem("better_coffee",  "Better Coffee Machine", 50,    "Upgraded grinder and beans.",      "+40 energy per coffee  (was +20)"),
    ShopItem("standing_desk",  "Standing Desk",         120,   "Ergonomic, height-adjustable.",    "Robot moves 25% faster between tiles"),
    ShopItem("mech_keyboard",  "Mechanical Keyboard",   250,   "Tactile switches. Very clicky.",   "Script executes 25% faster"),
    ShopItem("ai_assistant",   "AI Code Assistant",     600,   "Autocomplete for your brain.",     "look() sees two tiles ahead"),
    ShopItem("ci_cd",          "CI/CD Pipeline",        1_200, "Automated build and deploy.",      "Auto-run tests on commit (Phase 7)"),
    ShopItem("cloud_servers",  "Cloud Servers",         3_000, "Unlimited scale-out.",             "Doubles compute income (Phase 7)"),
]


class Economy:
    def __init__(self):
        self.salary: int          = 0
        self.reputation: int      = 0
        self.git_stars: int       = 0
        self.coffee_count: int    = 0
        self.compute_credits: int = 0
        self.upgrades: set[str]   = set()
        self.total_spent: int     = 0
        self._tick_timer: float   = 0.0
        self.tick_interval: float = c.ECONOMY_TICK_INTERVAL

    def update(self, dt: float, progression, event_bus=None) -> None:
        self._tick_timer += dt
        if self._tick_timer >= self.tick_interval:
            self._tick_timer -= self.tick_interval
            idx = min(progression.level_index, len(_SALARY_BY_LEVEL) - 1)
            amount = _SALARY_BY_LEVEL[idx]
            self.salary += amount
            if event_bus:
                event_bus.notify(f"+${amount} salary")

    def award(self, event_bus=None, **currencies) -> None:
        for key, amount in currencies.items():
            if hasattr(self, key) and amount:
                setattr(self, key, getattr(self, key) + amount)

    def buy(self, item_id: str, event_bus=None) -> tuple[bool, str]:
        item = self._item_for(item_id)
        if item is None:
            return False, "Unknown item."
        if item_id in self.upgrades:
            return False, f"Already owned: {item.name}"
        if self.salary < item.cost_salary:
            return False, f"Need ${item.cost_salary - self.salary} more."
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
        return item is not None and self.salary >= item.cost_salary and item_id not in self.upgrades

    def coffee_energy_restore(self) -> float:
        return 40.0 if self.has_upgrade("better_coffee") else c.COFFEE_ENERGY_RESTORE

    def move_duration_multiplier(self) -> float:
        return 0.75 if self.has_upgrade("standing_desk") else 1.0

    def script_speed_multiplier(self) -> float:
        return 0.75 if self.has_upgrade("mech_keyboard") else 1.0

    def look_range(self) -> int:
        return 2 if self.has_upgrade("ai_assistant") else 1

    @property
    def tick_progress(self) -> float:
        return min(1.0, self._tick_timer / self.tick_interval)

    @staticmethod
    def _item_for(item_id: str) -> ShopItem | None:
        for item in SHOP_ITEMS:
            if item.item_id == item_id:
                return item
        return None
