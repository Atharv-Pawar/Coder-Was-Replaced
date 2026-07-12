"""Toast notification queue."""
from __future__ import annotations
from dataclasses import dataclass
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
        fade = c.TOAST_FADE
        if self.elapsed < fade:
            return self.elapsed / fade
        if self.elapsed > self.duration - fade:
            return max(0.0, (self.duration - self.elapsed) / fade)
        return 1.0


class EventBus:
    def __init__(self):
        self.toasts: list[Toast] = []

    def notify(self, text: str, duration: float = c.TOAST_DURATION) -> None:
        self.toasts.append(Toast(text=text, duration=duration))

    def update(self, dt: float) -> None:
        for t in self.toasts:
            t.update(dt)
        self.toasts = [t for t in self.toasts if not t.done]
