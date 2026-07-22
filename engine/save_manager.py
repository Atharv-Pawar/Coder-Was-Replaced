"""Save / Load system — Phase 9.  Saves to data/save.json."""
from __future__ import annotations
import json
import pathlib
import time

SAVE_PATH    = pathlib.Path("data/save.json")
SAVE_VERSION = 9
AUTOSAVE_INTERVAL = 30.0   # seconds


class SaveManager:
    def __init__(self, game):
        self._game   = game
        self._timer  = 0.0
        self.last_save_time: float | None = None

    def update(self, dt: float) -> None:
        self._timer += dt
        if self._timer >= AUTOSAVE_INTERVAL:
            self._timer = 0.0
            self.save()

    # ── Save ─────────────────────────────────────────────────────────────────
    def save(self) -> bool:
        try:
            SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            g = self._game
            data = {
                "version":         SAVE_VERSION,
                "timestamp":       time.time(),
                # Progression
                "xp":              g.progression.xp,
                # Economy
                "salary":          g.economy.salary,
                "reputation":      g.economy.reputation,
                "git_stars":       g.economy.git_stars,
                "coffee_count":    g.economy.coffee_count,
                "compute_credits": g.economy.compute_credits,
                "upgrades":        list(g.economy.upgrades),
                "total_spent":     g.economy.total_spent,
                # Floor
                "floor":           g.floors.current_floor,
                "max_floor":       g.floors.max_floor_reached,
                # Missions stats
                "missions_completed": g.missions.total_completed,
                "missions_failed":    g.missions.total_failed,
                "action_totals":      dict(g.missions.action_totals),
                # Achievements
                "achievements":    list(g.achievements.unlocked),
                # Settings
                "settings":        g.settings.to_dict(),
            }
            SAVE_PATH.write_text(json.dumps(data, indent=2))
            self.last_save_time = time.time()
            return True
        except Exception as exc:
            print(f"[Save] Failed: {exc}")
            return False

    # ── Load ─────────────────────────────────────────────────────────────────
    def load(self) -> bool:
        if not SAVE_PATH.exists():
            return False
        try:
            data = json.loads(SAVE_PATH.read_text())
            if data.get("version", 0) < 8:
                return False   # too old — start fresh

            g = self._game

            # Progression — set directly to avoid stacking
            g.progression.xp = int(data.get("xp", 0))

            # Economy
            g.economy.salary          = int(data.get("salary",          0))
            g.economy.reputation      = int(data.get("reputation",      0))
            g.economy.git_stars       = int(data.get("git_stars",       0))
            g.economy.coffee_count    = int(data.get("coffee_count",    0))
            g.economy.compute_credits = int(data.get("compute_credits", 0))
            g.economy.upgrades        = set(data.get("upgrades",        []))
            g.economy.total_spent     = int(data.get("total_spent",     0))

            # Floor
            saved_floor = int(data.get("floor", 0))
            max_floor   = int(data.get("max_floor", 0))
            for _ in range(saved_floor):
                g.floors.current_floor += 1
                from game.procgen import generate
                tilemap, objects, spawn = generate(g.floors.current_floor)
                g.office.load_generated(tilemap, objects, spawn)
            g.floors.max_floor_reached = max(max_floor, saved_floor)

            # Mission stats
            g.missions.total_completed = int(data.get("missions_completed", 0))
            g.missions.total_failed    = int(data.get("missions_failed",    0))
            g.missions.action_totals   = {k: int(v)
                                           for k, v in data.get("action_totals", {}).items()}

            # Achievements
            g.achievements.unlock_from_save(data.get("achievements", []))

            # Settings
            if "settings" in data:
                from game.settings import Settings
                g.settings = Settings.from_dict(data["settings"])

            self.last_save_time = time.time()
            g.events.notify("Save loaded!")
            return True
        except Exception as exc:
            print(f"[Load] Failed: {exc}")
            return False

    @property
    def last_save_str(self) -> str:
        if self.last_save_time is None:
            return "never"
        import datetime
        return datetime.datetime.fromtimestamp(self.last_save_time).strftime("%H:%M:%S")
