"""
Lightweight tweening utilities for smooth tile-to-tile movement.

We don't have sprite sheets yet (Phase 1 uses colored rectangles), so this
module focuses on positional easing. Once real sprites land, `AnimatedSprite`
below can be extended with frame-based playback without changing how
callers use it.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def ease_out_quad(t: float) -> float:
    """Smooth deceleration easing, used for tile-to-tile glide."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) * (1 - t)


@dataclass
class Tween:
    """Animates a single float value from `start` to `end` over `duration` seconds."""

    start: float
    end: float
    duration: float
    elapsed: float = 0.0
    easing: callable = ease_out_quad

    def update(self, dt: float) -> None:
        self.elapsed = min(self.duration, self.elapsed + dt)

    @property
    def value(self) -> float:
        if self.duration <= 0:
            return self.end
        t = self.easing(self.elapsed / self.duration)
        return self.start + (self.end - self.start) * t

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration


@dataclass
class Vec2Tween:
    """Convenience wrapper animating an (x, y) pair, e.g. grid -> grid movement."""

    start: tuple[float, float]
    end: tuple[float, float]
    duration: float
    elapsed: float = 0.0
    easing: callable = ease_out_quad

    def update(self, dt: float) -> None:
        self.elapsed = min(self.duration, self.elapsed + dt)

    @property
    def value(self) -> tuple[float, float]:
        if self.duration <= 0:
            return self.end
        t = self.easing(self.elapsed / self.duration)
        x = self.start[0] + (self.end[0] - self.start[0]) * t
        y = self.start[1] + (self.end[1] - self.start[1]) * t
        return x, y

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration


@dataclass
class SpriteAnimation:
    """Frame-index animation, ready for when real sprite sheets are added.

    frames: list of pygame.Surface (or frame indices into a sheet)
    frame_duration: seconds per frame
    loop: whether to wrap around at the end
    """

    frames: list = field(default_factory=list)
    frame_duration: float = 0.1
    loop: bool = True
    _elapsed: float = 0.0

    def update(self, dt: float) -> None:
        if not self.frames:
            return
        self._elapsed += dt
        total_duration = self.frame_duration * len(self.frames)
        if self.loop:
            self._elapsed %= total_duration
        else:
            self._elapsed = min(self._elapsed, total_duration - 1e-6)

    @property
    def current_frame(self):
        if not self.frames:
            return None
        index = int(self._elapsed / self.frame_duration) % len(self.frames)
        return self.frames[index]

    def reset(self) -> None:
        self._elapsed = 0.0
