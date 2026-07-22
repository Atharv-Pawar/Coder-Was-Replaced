"""Achievement system — Phase 9."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Achievement:
    aid:         str
    title:       str
    description: str
    xp_required:  int = 0   # bonus XP awarded on unlock


ACHIEVEMENTS: list[Achievement] = [
    Achievement("first_steps",    "First Steps",      "Move the robot for the first time",          5),
    Achievement("bug_squasher",   "Bug Squasher",     "Fix your first bug",                        10),
    Achievement("coffee_addict",  "Coffee Addict",    "Drink 10 cups of coffee",                   15),
    Achievement("git_pusher",     "Git Pusher",       "Make your first commit",                    10),
    Achievement("ship_it",        "Ship It!",         "Deploy to production for the first time",   20),
    Achievement("exterminator",   "Exterminator",     "Fix 50 bugs total",                         50),
    Achievement("team_player",    "Team Player",      "Hire your first employee",                  25),
    Achievement("office_politics","Office Politics",  "Have 3 employees active at once",           40),
    Achievement("floor_climber",  "Floor Climber",    "Advance to Floor 2",                        30),
    Achievement("speed_demon",    "Speed Demon",      "Complete a timed mission",                  35),
    Achievement("millionaire",    "Millionaire",      "Earn $1,000 total salary",                  60),
    Achievement("fully_loaded",   "Fully Loaded",     "Own all four shop upgrades",                80),
]

_AID_MAP = {a.aid: a for a in ACHIEVEMENTS}

DISPLAY_SECONDS = 4.5
FADE_SECONDS    = 0.4


@dataclass
class AchievementPopup:
    achievement: Achievement
    elapsed: float = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt

    @property
    def done(self) -> bool:
        return self.elapsed >= DISPLAY_SECONDS

    @property
    def alpha(self) -> float:
        if self.elapsed < FADE_SECONDS:
            return self.elapsed / FADE_SECONDS
        tail = DISPLAY_SECONDS - FADE_SECONDS
        if self.elapsed > tail:
            return max(0.0, (DISPLAY_SECONDS - self.elapsed) / FADE_SECONDS)
        return 1.0


class AchievementSystem:
    """
    Checks game state every frame against simple unlock conditions.
    Fires a popup (and optional sound) the first time each is met.
    """

    def __init__(self, progression, economy, event_bus):
        self._progression = progression
        self._economy     = economy
        self._event_bus   = event_bus

        self.unlocked: set[str]           = set()
        self.popups:   list[AchievementPopup] = []

        # Stats fed from game.py each frame
        self.total_moves:          int = 0
        self.bugs_fixed:           int = 0
        self.coffees_drunk:        int = 0
        self.commits_made:         int = 0
        self.deploys_made:         int = 0
        self.employees_hired:      int = 0
        self.employees_active:     int = 0
        self.max_floor:            int = 0
        self.timed_missions_done:  int = 0
        self.total_salary_earned:  int = 0
        self.shop_upgrades_owned:  int = 0

        # Sound callback (set by Game after sound_manager is ready)
        self.on_unlock = None   # callable(aid: str) | None

    def update(self, dt: float) -> None:
        self._check_all()
        for p in self.popups:
            p.update(dt)
        self.popups = [p for p in self.popups if not p.done]

    def unlock_from_save(self, aids: list[str]) -> None:
        """Restore previously unlocked achievements without triggering popups."""
        self.unlocked.update(aids)

    # ── Conditions ────────────────────────────────────────────────────────────
    def _check_all(self) -> None:
        c = self
        self._try("first_steps",    c.total_moves >= 1)
        self._try("bug_squasher",   c.bugs_fixed >= 1)
        self._try("coffee_addict",  c.coffees_drunk >= 10)
        self._try("git_pusher",     c.commits_made >= 1)
        self._try("ship_it",        c.deploys_made >= 1)
        self._try("exterminator",   c.bugs_fixed >= 50)
        self._try("team_player",    c.employees_hired >= 1)
        self._try("office_politics",c.employees_active >= 3)
        self._try("floor_climber",  c.max_floor >= 2)
        self._try("speed_demon",    c.timed_missions_done >= 1)
        self._try("millionaire",    c.total_salary_earned >= 1_000)
        self._try("fully_loaded",   c.shop_upgrades_owned >= 4)

    def _try(self, aid: str, condition: bool) -> None:
        if aid in self.unlocked or not condition:
            return
        self.unlocked.add(aid)
        ach = _AID_MAP[aid]
        self._event_bus.notify(f"Achievement: {ach.title}!", duration=4.5)
        if ach.xp_required:
            self._progression.add_xp(ach.xp_required, self._event_bus)
        self.popups.append(AchievementPopup(ach))
        if self.on_unlock:
            self.on_unlock(aid)
