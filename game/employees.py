"""
AI Employee system — Phase 7.

Each employee is a robot that runs a pre-written role script automatically
once hired.  They share the same office, mission tracker, progression, and
economy as the player, so their work counts toward everything.

Four tiers (Intern → Senior Dev → Architect) with escalating cost, capability,
and passive income contribution.  The player can have up to MAX_EMPLOYEES
employees active simultaneously.

Architecture
------------
  EmployeeTier     — static definition (cost, colours, role script, unlocks)
  Employee         — live instance: owns a Robot + ScriptEngine, tracks status
  EmployeeManager  — hire, update all employees, draw delegation
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from engine import constants as c
from engine.scripting import ScriptEngine
from game.player import Robot


# ── Tier definitions ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class EmployeeTier:
    tier_id:     str
    label:       str          # short label drawn on the robot square
    title:       str          # display name
    cost:        int          # salary to hire
    color:       tuple        # RGB fill colour
    outline:     tuple        # RGB outline colour
    min_level:   int          # player progression.level_index needed to hire
    role_script: str          # pre-written Python the employee runs
    tagline:     str          # one-line description shown in the hire panel


TIERS: list[EmployeeTier] = [
    EmployeeTier(
        tier_id="intern",
        label="I", title="Intern", cost=100,
        color=(70, 150, 220), outline=(30, 90, 160),
        min_level=0,
        tagline="Patrols and fixes bugs automatically.",
        role_script="""\
while True:
    if look() == BUG:
        fix_bug()
    elif look() == WALL or look() == DESK:
        turn_right()
    else:
        move()
""",
    ),
    EmployeeTier(
        tier_id="junior",
        label="J", title="Junior Dev", cost=350,
        color=(70, 200, 120), outline=(30, 130, 70),
        min_level=1,
        tagline="Fixes bugs and commits to git.",
        role_script="""\
while True:
    if look() == BUG:
        fix_bug()
    elif look() == GIT:
        commit()
    elif look() == COFFEE:
        drink_coffee()
    elif look() == WALL or look() == DESK:
        turn_right()
    else:
        move()
""",
    ),
    EmployeeTier(
        tier_id="senior",
        label="S", title="Senior Dev", cost=900,
        color=(220, 140, 60), outline=(160, 90, 20),
        min_level=2,
        tagline="Full pipeline: fix, commit, test, deploy.",
        role_script="""\
steps = 0
while True:
    if look() == BUG:
        fix_bug()
    elif look() == GIT:
        commit()
    elif look() == SERVER:
        deploy()
    elif look() == WALL or look() == DESK:
        turn_right()
    else:
        move()
        steps = steps + 1
        if steps % 20 == 0:
            run_tests()
""",
    ),
    EmployeeTier(
        tier_id="architect",
        label="A", title="Architect", cost=2_500,
        color=(180, 80, 220), outline=(120, 40, 160),
        min_level=3,
        tagline="Refactors, deploys, and optimises at scale.",
        role_script="""\
cycle = 0
while True:
    if look() == BUG:
        fix_bug()
    elif look() == GIT:
        if cycle % 3 == 0:
            refactor()
        else:
            commit()
    elif look() == SERVER:
        deploy()
    elif look() == WALL or look() == DESK:
        turn_right()
    else:
        move()
        cycle = cycle + 1
""",
    ),
]

TIER_BY_ID = {t.tier_id: t for t in TIERS}

# Spawn positions for up to MAX_EMPLOYEES employees (grid coords)
_SPAWN_POSITIONS = [(4, 2), (4, 4), (16, 2), (16, 4), (8, 12), (18, 12)]


# ── Employee (live instance) ─────────────────────────────────────────────────
class Employee:
    _next_id = 0

    def __init__(self, tier: EmployeeTier, spawn_x: int, spawn_y: int,
                 office, event_bus, progression, economy, mission_tracker):
        Employee._next_id += 1
        self.uid    = Employee._next_id
        self.tier   = tier
        self.name   = f"{tier.title} #{self.uid}"

        self.robot  = Robot(grid_x=spawn_x, grid_y=spawn_y)
        self.robot.facing = random.choice([(1,0),(-1,0),(0,1),(0,-1)])

        self.engine = ScriptEngine(
            office, event_bus,
            progression=progression,
            economy=economy,
            mission_tracker=mission_tracker,
            robot=self.robot,           # ← each employee controls its OWN robot
        )
        self._role_script = tier.role_script
        self.status = "idle"     # "running" | "idle" | "error"

        self._start()

    def _start(self) -> None:
        self.engine.run(self._role_script)
        self.status = "running"

    def update(self, dt: float) -> None:
        self.robot.update(dt)
        self.engine.update(dt)
        if self.engine.error:
            self.status = "error"
        elif self.engine.is_running:
            self.status = "running"
        else:
            # Script finished or errored — restart after a brief moment
            self.status = "idle"
            self._start()

    def stop(self) -> None:
        self.engine.stop()
        self.status = "idle"


# ── EmployeeManager ──────────────────────────────────────────────────────────
class EmployeeManager:
    """
    Owns all hired employees. Delegates update/draw to each one.

    hire(tier_id) — deduct salary and spawn a new employee
    update(dt)    — tick all employee engines + robots
    """

    def __init__(self, office, event_bus, progression, economy, mission_tracker):
        self._office          = office
        self._event_bus       = event_bus
        self._progression     = progression
        self._economy         = economy
        self._mission_tracker = mission_tracker

        self.employees: list[Employee] = []

    # ── public ────────────────────────────────────────────────────────────────
    def hire(self, tier_id: str) -> tuple[bool, str]:
        tier = TIER_BY_ID.get(tier_id)
        if tier is None:
            return False, "Unknown role."
        if len(self.employees) >= c.MAX_EMPLOYEES:
            return False, f"Office full ({c.MAX_EMPLOYEES} max)."
        if self._progression.level_index < tier.min_level:
            from game.progression import LEVELS
            needed = LEVELS[tier.min_level].title
            return False, f"Need {needed} level to hire {tier.title}."
        if self._economy.salary < tier.cost:
            return False, f"Need ${tier.cost - self._economy.salary} more salary."

        self._economy.salary -= tier.cost
        spawn = _SPAWN_POSITIONS[len(self.employees) % len(_SPAWN_POSITIONS)]
        emp = Employee(
            tier, spawn[0], spawn[1],
            self._office, self._event_bus,
            self._progression, self._economy, self._mission_tracker,
        )
        self.employees.append(emp)
        self._event_bus.notify(f"Hired: {emp.name}!")
        return True, f"Hired {emp.name}."

    def fire(self, index: int) -> None:
        if 0 <= index < len(self.employees):
            self.employees[index].stop()
            self.employees.pop(index)

    def update(self, dt: float) -> None:
        for emp in self.employees:
            emp.update(dt)

    def stop_all(self) -> None:
        for emp in self.employees:
            emp.stop()

    def available_tiers(self) -> list[EmployeeTier]:
        return [t for t in TIERS
                if self._progression.level_index >= t.min_level]

    @property
    def count(self) -> int:
        return len(self.employees)

    @property
    def count_by_tier(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for emp in self.employees:
            result[emp.tier.tier_id] = result.get(emp.tier.tier_id, 0) + 1
        return result
