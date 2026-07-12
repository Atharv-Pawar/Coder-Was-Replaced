"""Tweening utilities for smooth tile-to-tile movement."""
from __future__ import annotations
from dataclasses import dataclass, field


def ease_out_quad(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) * (1 - t)


@dataclass
class Vec2Tween:
    start: tuple[float, float]
    end: tuple[float, float]
    duration: float
    elapsed: float = 0.0
    easing: object = ease_out_quad

    def update(self, dt: float) -> None:
        self.elapsed = min(self.duration, self.elapsed + dt)

    @property
    def value(self) -> tuple[float, float]:
        if self.duration <= 0:
            return self.end
        t = self.easing(self.elapsed / self.duration)
        return (self.start[0] + (self.end[0] - self.start[0]) * t,
                self.start[1] + (self.end[1] - self.start[1]) * t)

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration
