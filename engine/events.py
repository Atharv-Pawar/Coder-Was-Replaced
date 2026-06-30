"""
Lightweight event/notification system.

Phase 2 just needs a way to show short-lived "toast" messages when the
player interacts with something ("+20 energy", "Bug fixed!"). This same
queue will later carry structured game events (mission complete, level
up) once missions/economy exist, so other systems can subscribe without
the renderer needing to know about them directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine import constants as c


@dataclass
class Toast:
    text: str
    elapsed: float = 0.0
    duration: float = c.TOAST_DURATION

    def update(self, dt: float) -> None:
        self.elapsed += dt

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration

    @property
    def alpha(self) -> float:
        """0..1 opacity, fading in then out."""
        fade = c.TOAST_FADE
        if self.elapsed < fade:
            return self.elapsed / fade
        if self.elapsed > self.duration - fade:
            return max(0.0, (self.duration - self.elapsed) / fade)
        return 1.0


class EventBus:
    """Holds active toast notifications and any future structured events."""

    def __init__(self):
        self.toasts: list[Toast] = []

    def notify(self, text: str) -> None:
        self.toasts.append(Toast(text=text))

    def update(self, dt: float) -> None:
        for toast in self.toasts:
            toast.update(dt)
        self.toasts = [t for t in self.toasts if not t.done]
