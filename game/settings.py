"""User-configurable settings — Phase 9."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Settings:
    # Audio
    master_volume: float = 0.70    # 0.0 – 1.0
    sfx_volume:    float = 0.80    # 0.0 – 1.0 (multiplied by master)

    # Display
    fullscreen: bool = False

    # UI
    show_debug: bool = True

    # Script execution speed (extra delay between steps in seconds)
    script_speed: float = 0.0

    @property
    def effective_sfx(self) -> float:
        return max(0.0, min(1.0, self.master_volume * self.sfx_volume))

    def adjust_master(self, delta: float) -> None:
        self.master_volume = max(0.0, min(1.0, self.master_volume + delta))

    def adjust_sfx(self, delta: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, self.sfx_volume + delta))

    def to_dict(self) -> dict:
        return {
            "master_volume": self.master_volume,
            "sfx_volume":    self.sfx_volume,
            "fullscreen":    self.fullscreen,
            "show_debug":    self.show_debug,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Settings":
        s = cls()
        s.master_volume = float(d.get("master_volume", s.master_volume))
        s.sfx_volume    = float(d.get("sfx_volume",    s.sfx_volume))
        s.fullscreen    = bool(d.get("fullscreen",     s.fullscreen))
        s.show_debug    = bool(d.get("show_debug",     s.show_debug))
        return s
