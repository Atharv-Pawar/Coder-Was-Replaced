"""Smoothed camera with split-screen viewport offset support."""
from __future__ import annotations
from engine import constants as c


class Camera:
    def __init__(self, viewport_width: int, viewport_height: int, viewport_x: int = 0):
        self.viewport_width  = viewport_width
        self.viewport_height = viewport_height
        self.viewport_x      = viewport_x
        self.x = 0.0
        self.y = 0.0
        self._map_pixel_w = viewport_width
        self._map_pixel_h = viewport_height

    def set_bounds(self, map_pixel_width: int, map_pixel_height: int) -> None:
        self._map_pixel_w = map_pixel_width
        self._map_pixel_h = map_pixel_height

    def snap_to(self, target_x: float, target_y: float) -> None:
        self.x, self.y = self._centered_on(target_x, target_y)

    def update(self, dt: float, target_x: float, target_y: float) -> None:
        tx, ty = self._centered_on(target_x, target_y)
        t = min(1.0, c.CAMERA_SMOOTHING * dt)
        self.x += (tx - self.x) * t
        self.y += (ty - self.y) * t

    def _centered_on(self, tx: float, ty: float) -> tuple[float, float]:
        cx = max(0.0, min(tx - self.viewport_width  / 2, max(0.0, self._map_pixel_w - self.viewport_width)))
        cy = max(0.0, min(ty - self.viewport_height / 2, max(0.0, self._map_pixel_h - self.viewport_height)))
        return cx, cy

    def world_to_screen(self, wx: float, wy: float) -> tuple[float, float]:
        return wx - self.x + self.viewport_x, wy - self.y

    def screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        return sx + self.x - self.viewport_x, sy + self.y
