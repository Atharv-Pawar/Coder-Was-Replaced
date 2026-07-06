"""
Progression system — Phase 4.

Tracks the robot's XP and controls which API functions are available
to the player at any given moment. Two separate but related ladders:

  Level ladder   — cosmetic title (Intern → CTO → Fully Automated)
  Unlock ladder  — which script functions can be called

The unlock ladder is the gameplay-relevant one. Each unlock entry has
an XP threshold; the scripting engine checks `is_unlocked(fn_name)`
before dispatching any command, and emits a clear error if it's locked.

XP sources (awarded by the scripting engine on successful actions):
  move()         — +1 XP every MOVE_XP_INTERVAL steps
  fix_bug()      — +10 XP
  drink_coffee() — +3 XP
  commit()       — +20 XP
  deploy()       — +40 XP
  run_tests()    — +30 XP

New unlocks trigger a special toast so the player notices immediately.
"""

from __future__ import annotations

from dataclasses import dataclass


# ── Level ladder ────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Level:
    xp_required: int
    title: str

LEVELS: list[Level] = [
    Level(0,     "Intern"),
    Level(50,    "Junior Developer"),
    Level(200,   "Developer"),
    Level(500,   "Senior Dev"),
    Level(1_000, "Tech Lead"),
    Level(2_000, "Architect"),
    Level(4_000, "Eng Manager"),
    Level(8_000, "CTO"),
    Level(15_000,"Fully Automated"),
]


# ── Unlock ladder ────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class UnlockEntry:
    xp_required: int
    fn_name: str
    description: str

UNLOCKS: list[UnlockEntry] = [
    # Always available — the basics
    UnlockEntry(0,     "move",          "Move forward"),
    UnlockEntry(0,     "turn_left",     "Rotate left"),
    UnlockEntry(0,     "turn_right",    "Rotate right"),
    UnlockEntry(0,     "look",          "Sense ahead"),
    # Junior Developer tier
    UnlockEntry(50,    "fix_bug",       "Fix a bug"),
    UnlockEntry(50,    "drink_coffee",  "Refuel energy"),
    # Developer tier
    UnlockEntry(200,   "commit",        "Git commit"),
    # Senior Dev tier
    UnlockEntry(500,   "deploy",        "Deploy to server"),
    UnlockEntry(500,   "answer_email",  "Clear inbox"),
    # Tech Lead tier
    UnlockEntry(1_000, "run_tests",     "Run test suite"),
    UnlockEntry(1_000, "build_project", "Build project"),
    # Architect tier
    UnlockEntry(2_000, "refactor",      "Refactor code"),
    UnlockEntry(2_000, "scan",          "Scan area"),
    # Eng Manager tier
    UnlockEntry(4_000, "spawn_worker",  "Hire a worker"),
    UnlockEntry(4_000, "use_ai",        "Use AI assist"),
    # CTO tier
    UnlockEntry(8_000, "docker_build",  "Docker build"),
    UnlockEntry(8_000, "optimize",      "Optimize code"),
    # Fully Automated
    UnlockEntry(15_000,"train_model",   "Train ML model"),
    UnlockEntry(15_000,"kubernetes_scale","K8s scale"),
]

# XP awarded per action
XP_MOVE_INTERVAL = 10   # award +1 XP every N successful moves
XP_FIX_BUG       = 10
XP_COFFEE         = 3
XP_COMMIT         = 20
XP_DEPLOY         = 40
XP_RUN_TESTS      = 30
XP_ANSWER_EMAIL   = 15
XP_REFACTOR       = 25


class Progression:
    """
    Single source of truth for the player's XP, level, and unlocks.

    Call `add_xp(amount, event_bus)` from the scripting engine after
    each successful action. Call `is_unlocked(fn_name)` before dispatch.
    """

    def __init__(self):
        self.xp: int = 0
        self._move_counter: int = 0
        # Track which unlocks the player has been *notified* about so we
        # only toast each one once.
        self._notified: set[str] = set(
            u.fn_name for u in UNLOCKS if u.xp_required == 0
        )

    # ── XP & moves ──────────────────────────────────────────────────────
    def add_xp(self, amount: int, event_bus=None) -> None:
        old_xp = self.xp
        self.xp += amount
        self._check_new_unlocks(old_xp, event_bus)

    def count_move(self, event_bus=None) -> None:
        """Call once per successful move(); awards XP every N steps."""
        self._move_counter += 1
        if self._move_counter % XP_MOVE_INTERVAL == 0:
            self.add_xp(1, event_bus)

    # ── Queries ──────────────────────────────────────────────────────────
    def is_unlocked(self, fn_name: str) -> bool:
        entry = self._entry_for(fn_name)
        if entry is None:
            return True  # unknown function — don't block it
        return self.xp >= entry.xp_required

    def unlock_error_msg(self, fn_name: str) -> str:
        entry = self._entry_for(fn_name)
        if entry is None:
            return f"{fn_name}() not found"
        return (
            f"{fn_name}() is locked  "
            f"(need {entry.xp_required} XP, you have {self.xp})"
        )

    @property
    def level(self) -> Level:
        current = LEVELS[0]
        for lv in LEVELS:
            if self.xp >= lv.xp_required:
                current = lv
        return current

    @property
    def level_index(self) -> int:
        idx = 0
        for i, lv in enumerate(LEVELS):
            if self.xp >= lv.xp_required:
                idx = i
        return idx

    @property
    def next_level(self) -> Level | None:
        idx = self.level_index
        if idx + 1 < len(LEVELS):
            return LEVELS[idx + 1]
        return None

    @property
    def next_unlock(self) -> UnlockEntry | None:
        """The first locked unlock entry (by XP threshold)."""
        for u in UNLOCKS:
            if self.xp < u.xp_required:
                return u
        return None

    @property
    def unlocked_functions(self) -> list[UnlockEntry]:
        return [u for u in UNLOCKS if self.xp >= u.xp_required]

    @property
    def xp_progress_ratio(self) -> float:
        """0.0–1.0 progress from current unlock tier toward the next one."""
        nxt = self.next_unlock
        if nxt is None:
            return 1.0
        # Find the unlock just below the next one to get the 'from' value
        prev_xp = 0
        for u in UNLOCKS:
            if u.xp_required < nxt.xp_required:
                prev_xp = max(prev_xp, u.xp_required)
        span = nxt.xp_required - prev_xp
        if span <= 0:
            return 1.0
        return min(1.0, (self.xp - prev_xp) / span)

    @property
    def xp_to_next_unlock(self) -> int:
        nxt = self.next_unlock
        return max(0, nxt.xp_required - self.xp) if nxt else 0

    # ── Internal ─────────────────────────────────────────────────────────
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
