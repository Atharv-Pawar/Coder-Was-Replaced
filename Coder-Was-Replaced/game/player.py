"""
The player-controlled AI robot.

Movement is grid-based: the robot always occupies a tile, and moving to
an adjacent tile plays a short glide animation rather than snapping
instantly. This is the same model `scripting.py` will use in Phase 3 to
drive the robot from player-written Python (`move()`, `turn_left()`, etc.)
-- the keyboard control here is a stand-in until the scripting engine
exists, and exercises the exact same `try_move` / facing API.
"""

from __future__ import annotations

from engine import constants as c
from engine.animation import Vec2Tween


class Robot:
    def __init__(self, grid_x: int, grid_y: int):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.facing: tuple[int, int] = c.DIR_DOWN

        self._tween: Vec2Tween | None = None

        # Stats that will matter once economy/missions land (Phase 5+).
        self.energy: float = c.PLAYER_MAX_ENERGY

    @property
    def is_moving(self) -> bool:
        return self._tween is not None and not self._tween.done

    @property
    def world_pixel_pos(self) -> tuple[float, float]:
        """Current draw position in world pixels (top-left of the tile)."""
        if self._tween is not None:
            return self._tween.value
        return self._grid_to_pixel(self.grid_x, self.grid_y)

    @property
    def center_pixel_pos(self) -> tuple[float, float]:
        x, y = self.world_pixel_pos
        return x + c.TILE_SIZE / 2, y + c.TILE_SIZE / 2

    def update(self, dt: float) -> None:
        if self._tween is not None:
            self._tween.update(dt)
            if self._tween.done:
                self._tween = None

    def try_move(self, dx: int, dy: int, is_walkable) -> bool:
        """Attempt to step one tile in the given direction.

        `is_walkable` is a callable(grid_x, grid_y) -> bool, so the caller
        (Office) can combine tilemap collision with object collision
        (desks, servers, etc.) without this class needing to know about
        objects at all.

        Always updates facing (so bumping into something still turns the
        robot to face it, mirroring `turn_left()/turn_right()` semantics
        used later by the scripting engine). Returns True if the robot
        actually moved.
        """
        self.facing = (dx, dy)

        if self.is_moving:
            return False

        target_x, target_y = self.grid_x + dx, self.grid_y + dy
        if not is_walkable(target_x, target_y):
            return False

        start_pixel = self._grid_to_pixel(self.grid_x, self.grid_y)
        end_pixel = self._grid_to_pixel(target_x, target_y)
        self._tween = Vec2Tween(start=start_pixel, end=end_pixel, duration=c.PLAYER_MOVE_DURATION)

        self.grid_x, self.grid_y = target_x, target_y
        return True

    @property
    def facing_tile(self) -> tuple[int, int]:
        """Grid coordinate of the tile directly in front of the robot."""
        return self.grid_x + self.facing[0], self.grid_y + self.facing[1]

    @property
    def energy_ratio(self) -> float:
        return max(0.0, min(1.0, self.energy / c.PLAYER_MAX_ENERGY))

    @staticmethod
    def _grid_to_pixel(grid_x: int, grid_y: int) -> tuple[float, float]:
        return grid_x * c.TILE_SIZE, grid_y * c.TILE_SIZE
