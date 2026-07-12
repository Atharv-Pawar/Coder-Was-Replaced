"""The AI robot — grid-based movement with smooth tween animation."""
from __future__ import annotations
from engine import constants as c
from engine.animation import Vec2Tween


class Robot:
    def __init__(self, grid_x: int, grid_y: int):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.facing: tuple[int, int] = c.DIR_DOWN if hasattr(c, 'DIR_DOWN') else (0, 1)
        self.energy: float = c.PLAYER_MAX_ENERGY
        self.move_duration: float = c.PLAYER_MOVE_DURATION  # upgradeable
        self._tween: Vec2Tween | None = None

    @property
    def is_moving(self) -> bool:
        return self._tween is not None and not self._tween.done

    @property
    def world_pixel_pos(self) -> tuple[float, float]:
        if self._tween is not None:
            return self._tween.value
        return self._grid_to_pixel(self.grid_x, self.grid_y)

    @property
    def center_pixel_pos(self) -> tuple[float, float]:
        x, y = self.world_pixel_pos
        return x + c.TILE_SIZE / 2, y + c.TILE_SIZE / 2

    @property
    def facing_tile(self) -> tuple[int, int]:
        return self.grid_x + self.facing[0], self.grid_y + self.facing[1]

    @property
    def energy_ratio(self) -> float:
        return max(0.0, min(1.0, self.energy / c.PLAYER_MAX_ENERGY))

    def update(self, dt: float) -> None:
        if self._tween is not None:
            self._tween.update(dt)
            if self._tween.done:
                self._tween = None

    def try_move(self, dx: int, dy: int, is_walkable) -> bool:
        self.facing = (dx, dy)
        if self.is_moving:
            return False
        tx, ty = self.grid_x + dx, self.grid_y + dy
        if not is_walkable(tx, ty):
            return False
        start = self._grid_to_pixel(self.grid_x, self.grid_y)
        end   = self._grid_to_pixel(tx, ty)
        self._tween = Vec2Tween(start=start, end=end, duration=self.move_duration)
        self.grid_x, self.grid_y = tx, ty
        return True

    @staticmethod
    def _grid_to_pixel(gx: int, gy: int) -> tuple[float, float]:
        return gx * c.TILE_SIZE, gy * c.TILE_SIZE
