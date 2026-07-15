"""
Floor manager — Phase 8.

Tracks the current floor number, decides when the player can advance,
and orchestrates the hot-swap: generate a new office layout and reload
all robots / employees into it without restarting the game.

Transition overlay
------------------
When a floor changes, `transition_active` becomes True for
TRANSITION_DURATION seconds so the renderer can draw a "Advancing to
Floor N" overlay while the new map loads behind it.
"""

from __future__ import annotations

from engine import constants as c
from game.procgen import generate, floor_name, floor_unlock_level, FLOOR_CONFIGS


class FloorManager:
    TRANSITION_DURATION = 3.0   # seconds the overlay is visible

    def __init__(self, office, employees, event_bus, progression):
        self._office      = office
        self._employees   = employees
        self._event_bus   = event_bus
        self._progression = progression

        self.current_floor: int = 0
        self.max_floor_reached: int = 0

        # Transition overlay state
        self.transition_active: bool = False
        self.transition_name:   str  = ""
        self._transition_timer: float = 0.0

    # ── public ────────────────────────────────────────────────────────────────
    def can_advance(self) -> bool:
        next_floor = self.current_floor + 1
        if next_floor >= len(FLOOR_CONFIGS):
            return False
        return self._progression.level_index >= floor_unlock_level(next_floor)

    def advance(self) -> None:
        """Move to the next floor. Rebuilds the office in-place."""
        if not self.can_advance():
            needed_lvl = floor_unlock_level(self.current_floor + 1)
            from game.progression import LEVELS
            need_title = LEVELS[needed_lvl].title if needed_lvl < len(LEVELS) else "???"
            self._event_bus.notify(f"Need {need_title} level for next floor")
            return

        self.current_floor += 1
        self.max_floor_reached = max(self.max_floor_reached, self.current_floor)

        name = floor_name(self.current_floor)
        self._event_bus.notify(f"Advancing to Floor {self.current_floor}: {name}!", duration=4.0)

        # Generate new layout
        tilemap, objects, spawn = generate(self.current_floor)

        # Hot-swap the office
        self._office.load_generated(tilemap, objects, spawn)

        # Reposition employees on the new map
        from game.employees import _SPAWN_POSITIONS
        for i, emp in enumerate(self._employees.employees):
            pos = _SPAWN_POSITIONS[i % len(_SPAWN_POSITIONS)]
            emp.robot.grid_x, emp.robot.grid_y = pos
            emp.robot._tween = None
            # Restart the employee script on the new map
            emp.engine.stop()
            emp._start()

        # Trigger transition overlay
        self.transition_active = True
        self.transition_name   = name
        self._transition_timer = self.TRANSITION_DURATION

    def update(self, dt: float) -> None:
        if self.transition_active:
            self._transition_timer -= dt
            if self._transition_timer <= 0:
                self.transition_active = False

    @property
    def transition_alpha(self) -> float:
        """0.0–1.0 opacity — peaks in the middle of the transition."""
        if not self.transition_active:
            return 0.0
        t = self._transition_timer / self.TRANSITION_DURATION
        # Triangle: ramp up then down (t goes 1→0, peak alpha at t=0.5)
        return 1.0 - abs(t - 0.5) * 2

    @property
    def next_floor_unlock_title(self) -> str:
        """The level title needed to unlock the next floor, or '' if maxed."""
        nf = self.current_floor + 1
        if nf >= len(FLOOR_CONFIGS):
            return ""
        lvl_idx = floor_unlock_level(nf)
        from game.progression import LEVELS
        return LEVELS[lvl_idx].title if lvl_idx < len(LEVELS) else "???"
