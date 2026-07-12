"""Mission system — Phase 6."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class Objective:
    action: str
    target: int
    label: str
    current: int = 0

    @property
    def done(self) -> bool:
        return self.current >= self.target

    @property
    def progress_ratio(self) -> float:
        return min(1.0, self.current / max(1, self.target))

    def try_advance(self, action: str) -> bool:
        if action == self.action and not self.done:
            self.current += 1
            return True
        return False


@dataclass
class Mission:
    mission_id: str
    title: str
    flavour: str
    objectives: list[Objective]
    rewards: dict[str, int]
    time_limit: float | None = None
    min_level: int = 0
    elapsed: float = 0.0

    @property
    def all_done(self) -> bool:
        return all(o.done for o in self.objectives)

    @property
    def timed_out(self) -> bool:
        return self.time_limit is not None and self.elapsed >= self.time_limit

    @property
    def time_remaining(self) -> float:
        if self.time_limit is None:
            return float("inf")
        return max(0.0, self.time_limit - self.elapsed)

    @property
    def is_urgent(self) -> bool:
        return self.time_limit is not None and self.time_remaining < self.time_limit * 0.25

    def on_action(self, action: str) -> None:
        for obj in self.objectives:
            obj.try_advance(action)

    def update(self, dt: float) -> None:
        self.elapsed += dt


# ── 10-mission catalog ────────────────────────────────────────────────────────
_CATALOG: list[dict[str, Any]] = [
    dict(mission_id="first_steps",    title="First Steps",
         flavour="Get the robot moving around the office.",
         objectives=[dict(action="move",         target=20, label="Move tiles")],
         rewards=dict(xp=15, salary=10),
         time_limit=None, min_level=0, scale_key="move"),

    dict(mission_id="coffee_run",     title="Coffee Run",
         flavour="The robot needs fuel. Find the machine.",
         objectives=[dict(action="drink_coffee", target=2,  label="Drink coffee")],
         rewards=dict(xp=20, salary=15, reputation=2),
         time_limit=None, min_level=0, scale_key="drink_coffee"),

    dict(mission_id="bug_hunt",       title="Bug Hunt",
         flavour="Three bugs spotted on the floor.",
         objectives=[dict(action="fix_bug",      target=3,  label="Fix bugs")],
         rewards=dict(xp=30, salary=25, reputation=5),
         time_limit=None, min_level=0, scale_key="fix_bug"),

    dict(mission_id="commit_streak",  title="Commit Streak",
         flavour="The team wants to see green on the graph.",
         objectives=[dict(action="commit",        target=3,  label="Git commits")],
         rewards=dict(xp=40, salary=30, git_stars=3, reputation=5),
         time_limit=None, min_level=1, scale_key="commit"),

    dict(mission_id="debug_session",  title="Debug Session",
         flavour="Five bugs — someone pushed on a Friday.",
         objectives=[dict(action="fix_bug",      target=5,  label="Fix bugs"),
                     dict(action="commit",        target=1,  label="Commit the fix")],
         rewards=dict(xp=55, salary=45, reputation=8),
         time_limit=None, min_level=1, scale_key="fix_bug"),

    dict(mission_id="inbox_zero",     title="Inbox Zero",
         flavour="34 unread. Management is watching.",
         objectives=[dict(action="answer_email", target=3,  label="Answer emails")],
         rewards=dict(xp=35, salary=40, reputation=10),
         time_limit=None, min_level=1, scale_key="answer_email"),

    dict(mission_id="monday_standup", title="Monday Standup",
         flavour="Answer emails before the 9 AM call!",
         objectives=[dict(action="answer_email", target=3,  label="Answer emails"),
                     dict(action="move",         target=10, label="Stay active")],
         rewards=dict(xp=50, salary=50, reputation=12),
         time_limit=75.0, min_level=1, scale_key="answer_email"),

    dict(mission_id="deploy_day",     title="Deploy Day",
         flavour="Ship it. The server rack is waiting.",
         objectives=[dict(action="fix_bug",      target=2,  label="Pre-deploy fixes"),
                     dict(action="commit",        target=2,  label="Commit changes"),
                     dict(action="deploy",        target=1,  label="Deploy to prod")],
         rewards=dict(xp=80, salary=80, reputation=15, git_stars=5),
         time_limit=None, min_level=2, scale_key="fix_bug"),

    dict(mission_id="deadline_crunch",title="Deadline Crunch",
         flavour="Demo in 2 minutes. Fix everything. NOW.",
         objectives=[dict(action="fix_bug",      target=5,  label="Fix critical bugs"),
                     dict(action="deploy",        target=1,  label="Deploy hotfix")],
         rewards=dict(xp=100, salary=100, reputation=20, git_stars=3),
         time_limit=120.0, min_level=2, scale_key="fix_bug"),

    dict(mission_id="sprint_complete",title="Sprint Complete",
         flavour="End of sprint. Deliver the whole board.",
         objectives=[dict(action="fix_bug",      target=4,  label="Fix sprint bugs"),
                     dict(action="commit",        target=3,  label="Commit work"),
                     dict(action="run_tests",     target=1,  label="Run test suite"),
                     dict(action="deploy",        target=1,  label="Deploy sprint")],
         rewards=dict(xp=150, salary=150, reputation=30, git_stars=8),
         time_limit=None, min_level=3, scale_key="fix_bug"),
]


def _build_mission(template: dict, cycle: int = 0) -> Mission:
    scale_key   = template.get("scale_key")
    tgt_mult    = 1.0 + cycle * 0.5
    reward_mult = 1.0 + cycle * 0.3

    objectives = []
    for od in template["objectives"]:
        tgt = od["target"]
        if scale_key and od["action"] == scale_key and cycle > 0:
            tgt = max(1, round(tgt * tgt_mult))
        objectives.append(Objective(action=od["action"], target=tgt, label=od["label"]))

    rewards = {k: max(1, round(v * reward_mult)) for k, v in template["rewards"].items()}

    return Mission(
        mission_id=template["mission_id"],
        title=template["title"],
        flavour=template["flavour"],
        objectives=objectives,
        rewards=rewards,
        time_limit=template.get("time_limit"),
        min_level=template.get("min_level", 0),
    )


class MissionTracker:
    """Manages mission lifecycle: picks, tracks progress, awards rewards."""

    COMPLETE_DISPLAY = 4.0

    def __init__(self, progression, economy, event_bus):
        self._progression = progression
        self._economy     = economy
        self._event_bus   = event_bus
        self._cycle: int        = 0
        self._catalog_index: int = 0

        self.active: Mission | None         = None
        self.just_completed: Mission | None = None
        self.last_failed: bool              = False
        self._complete_timer: float         = 0.0
        self.total_completed: int           = 0
        self.total_failed: int              = 0
        self.action_totals: dict[str, int]  = {}

        self._load_next()

    # ── public ────────────────────────────────────────────────────────────────
    def on_action(self, action: str) -> None:
        self.action_totals[action] = self.action_totals.get(action, 0) + 1
        if self.active is not None:
            self.active.on_action(action)
            if self.active.all_done:
                self._complete()

    def update(self, dt: float) -> None:
        if self._complete_timer > 0:
            self._complete_timer -= dt
            if self._complete_timer <= 0:
                self.just_completed = None
        if self.active is not None:
            self.active.update(dt)
            if self.active.timed_out:
                self._fail()

    @property
    def overlay_alpha(self) -> float:
        return min(1.0, self._complete_timer / self.COMPLETE_DISPLAY)

    # ── lifecycle ─────────────────────────────────────────────────────────────
    def _complete(self) -> None:
        m = self.active
        self.active = None
        self.total_completed += 1
        self.last_failed = False

        xp    = m.rewards.get("xp", 0)
        sal   = m.rewards.get("salary", 0)
        rep   = m.rewards.get("reputation", 0)
        stars = m.rewards.get("git_stars", 0)

        if xp:
            self._progression.add_xp(xp, self._event_bus)
        self._economy.award(self._event_bus, salary=sal, reputation=rep, git_stars=stars)

        parts = []
        if sal:   parts.append(f"+${sal}")
        if xp:    parts.append(f"+{xp} XP")
        if rep:   parts.append(f"+{rep} Rep")
        if stars: parts.append(f"+{stars} Stars")
        self._event_bus.notify(f"Mission complete: {m.title}!  " + "  ".join(parts),
                               duration=4.0)

        self.just_completed  = m
        self._complete_timer = self.COMPLETE_DISPLAY
        self._load_next()

    def _fail(self) -> None:
        m = self.active
        self.active = None
        self.total_failed += 1
        self.last_failed   = True
        self._economy.award(self._event_bus, reputation=-3)
        self._event_bus.notify(f"Mission failed: {m.title}  (-3 Rep)")
        self.just_completed  = m          # show the failed overlay too
        self._complete_timer = self.COMPLETE_DISPLAY
        self._load_next()

    def _load_next(self) -> None:
        pool = [t for t in _CATALOG if t.get("min_level", 0) <= self._progression.level_index]
        if not pool:
            return
        self._catalog_index %= len(pool)
        template = pool[self._catalog_index]
        self._catalog_index += 1
        if self._catalog_index >= len(pool):
            self._catalog_index = 0
            self._cycle += 1
        self.active = _build_mission(template, self._cycle)
