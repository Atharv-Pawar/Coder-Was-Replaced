"""XP engine, level ladder, unlock registry — Phase 4."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Level:
    xp_required: int
    title: str

LEVELS: list[Level] = [
    Level(0,      "Intern"),
    Level(50,     "Junior Developer"),
    Level(200,    "Developer"),
    Level(500,    "Senior Dev"),
    Level(1_000,  "Tech Lead"),
    Level(2_000,  "Architect"),
    Level(4_000,  "Eng Manager"),
    Level(8_000,  "CTO"),
    Level(15_000, "Fully Automated"),
]


@dataclass(frozen=True)
class UnlockEntry:
    xp_required: int
    fn_name: str
    description: str

UNLOCKS: list[UnlockEntry] = [
    UnlockEntry(0,      "move",          "Move forward"),
    UnlockEntry(0,      "turn_left",     "Rotate left"),
    UnlockEntry(0,      "turn_right",    "Rotate right"),
    UnlockEntry(0,      "look",          "Sense ahead"),
    UnlockEntry(50,     "fix_bug",       "Fix a bug"),
    UnlockEntry(50,     "drink_coffee",  "Refuel energy"),
    UnlockEntry(200,    "commit",        "Git commit"),
    UnlockEntry(500,    "deploy",        "Deploy to server"),
    UnlockEntry(500,    "answer_email",  "Clear inbox"),
    UnlockEntry(1_000,  "run_tests",     "Run test suite"),
    UnlockEntry(1_000,  "build_project", "Build project"),
    UnlockEntry(2_000,  "refactor",      "Refactor code"),
    UnlockEntry(2_000,  "scan",          "Scan area"),
    UnlockEntry(4_000,  "spawn_worker",  "Hire a worker"),
    UnlockEntry(4_000,  "use_ai",        "Use AI assist"),
    UnlockEntry(8_000,  "docker_build",  "Docker build"),
    UnlockEntry(8_000,  "optimize",      "Optimize code"),
    UnlockEntry(15_000, "train_model",   "Train ML model"),
    UnlockEntry(15_000, "kubernetes_scale", "K8s scale"),
]

# XP per action
XP_MOVE_INTERVAL = 10
XP_FIX_BUG       = 10
XP_COFFEE         = 3
XP_COMMIT         = 20
XP_DEPLOY         = 40
XP_RUN_TESTS      = 30
XP_ANSWER_EMAIL   = 15
XP_REFACTOR       = 25


class Progression:
    def __init__(self):
        self.xp: int = 0
        self._move_counter: int = 0
        self._notified: set[str] = {u.fn_name for u in UNLOCKS if u.xp_required == 0}

    def add_xp(self, amount: int, event_bus=None) -> None:
        old = self.xp
        self.xp += amount
        self._check_new_unlocks(old, event_bus)

    def count_move(self, event_bus=None) -> None:
        self._move_counter += 1
        if self._move_counter % XP_MOVE_INTERVAL == 0:
            self.add_xp(1, event_bus)

    def is_unlocked(self, fn_name: str) -> bool:
        entry = self._entry_for(fn_name)
        return entry is None or self.xp >= entry.xp_required

    def unlock_error_msg(self, fn_name: str) -> str:
        entry = self._entry_for(fn_name)
        if entry is None:
            return f"{fn_name}() not found"
        return f"{fn_name}() is locked  (need {entry.xp_required} XP, you have {self.xp})"

    @property
    def level(self) -> Level:
        cur = LEVELS[0]
        for lv in LEVELS:
            if self.xp >= lv.xp_required:
                cur = lv
        return cur

    @property
    def level_index(self) -> int:
        idx = 0
        for i, lv in enumerate(LEVELS):
            if self.xp >= lv.xp_required:
                idx = i
        return idx

    @property
    def next_unlock(self) -> UnlockEntry | None:
        for u in UNLOCKS:
            if self.xp < u.xp_required:
                return u
        return None

    @property
    def xp_progress_ratio(self) -> float:
        nxt = self.next_unlock
        if nxt is None:
            return 1.0
        prev_xp = max((u.xp_required for u in UNLOCKS if u.xp_required < nxt.xp_required), default=0)
        span = nxt.xp_required - prev_xp
        return min(1.0, (self.xp - prev_xp) / span) if span > 0 else 1.0

    @property
    def xp_to_next_unlock(self) -> int:
        nxt = self.next_unlock
        return max(0, nxt.xp_required - self.xp) if nxt else 0

    @property
    def unlocked_functions(self) -> list[UnlockEntry]:
        return [u for u in UNLOCKS if self.xp >= u.xp_required]

    def _entry_for(self, fn_name: str) -> UnlockEntry | None:
        for u in UNLOCKS:
            if u.fn_name == fn_name:
                return u
        return None

    def _check_new_unlocks(self, old_xp: int, event_bus) -> None:
        if event_bus is None:
            return
        for u in UNLOCKS:
            if u.fn_name in self._notified:
                continue
            if old_xp < u.xp_required <= self.xp:
                event_bus.notify(f"UNLOCKED: {u.fn_name}()  --  {u.description}")
                self._notified.add(u.fn_name)
