"""
Camera system.

The camera tracks a world-space target position (e.g. the player) with
exponential smoothing, and is clamped so it never shows outside the map
bounds. It exposes helpers to convert world <-> screen coordinates, which
every renderer call should go through.
"""

from __future__ import annotations

from engine import constants as c


class Camera:
    def __init__(self, viewport_width: int, viewport_height: int):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        # Top-left corner of the camera in world pixels (float for smoothing).
        self.x = 0.0
        self.y = 0.0

        # World pixel bounds the camera is allowed to show (set via set_bounds).
        self._map_pixel_w = viewport_width
        self._map_pixel_h = viewport_height

    def set_bounds(self, map_pixel_width: int, map_pixel_height: int) -> None:
        self._map_pixel_w = map_pixel_width
        self._map_pixel_h = map_pixel_height

    def snap_to(self, target_x: float, target_y: float) -> None:
        """Immediately center the camera on a world point (used on level load)."""
        self.x, self.y = self._centered_on(target_x, target_y)

    def update(self, dt: float, target_x: float, target_y: float) -> None:
        target_cam_x, target_cam_y = self._centered_on(target_x, target_y)
        # Exponential smoothing towards the target camera position.
        t = min(1.0, c.CAMERA_SMOOTHING * dt)
        self.x += (target_cam_x - self.x) * t
        self.y += (target_cam_y - self.y) * t

    def _centered_on(self, target_x: float, target_y: float) -> tuple[float, float]:
        cam_x = target_x - self.viewport_width / 2
        cam_y = target_y - self.viewport_height / 2

        max_x = max(0.0, self._map_pixel_w - self.viewport_width)
        max_y = max(0.0, self._map_pixel_h - self.viewport_height)

        cam_x = min(max(0.0, cam_x), max_x)
        cam_y = min(max(0.0, cam_y), max_y)
        return cam_x, cam_y

    # -- coordinate helpers ----------------------------------------------
    def world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float]:
        return world_x - self.x, world_y - self.y

    def screen_to_world(self, screen_x: float, screen_y: float) -> tuple[float, float]:
        return screen_x + self.x, screen_y + self.y
