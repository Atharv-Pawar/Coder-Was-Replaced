"""Main game loop — Phases 1-7."""
from __future__ import annotations
import pygame
from engine import constants as c
from engine.events import EventBus
from engine.input import InputManager
from engine.renderer import Renderer
from engine.scripting import ScriptEngine
from game.economy import Economy, SHOP_ITEMS
from game.editor import Editor
from game.employees import EmployeeManager, TIERS
from game.missions import MissionTracker
from game.office import Office
from game.progression import Progression


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        pygame.font.init()
        pygame.key.start_text_input()

        self.renderer    = Renderer()
        self.input       = InputManager()
        self.clock       = pygame.time.Clock()
        self.events      = EventBus()

        self.office      = Office()
        self.progression = Progression()
        self.economy     = Economy()
        self.missions    = MissionTracker(self.progression, self.economy, self.events)
        self.employees   = EmployeeManager(
            self.office, self.events, self.progression,
            self.economy, self.missions,
        )
        self.editor      = Editor()
        self.script_engine = ScriptEngine(
            self.office, self.events,
            progression=self.progression,
            economy=self.economy,
            mission_tracker=self.missions,
            robot=self.office.robot,        # player robot
        )

        self._running     = False
        self._shop_open   = False
        self._hire_open   = False
        self._fps_samples: list[float] = []

    def run(self) -> None:
        self._running = True
        while self._running:
            dt = min(self.clock.tick(c.FPS) / 1000.0, 1 / 20)
            self._process_events()
            self._update(dt)
            self._draw()
            if self.input.quit_requested:
                self.script_engine.stop()
                self.employees.stop_all()
                self._running = False
        pygame.quit()

    # ── Events ────────────────────────────────────────────────────────────────
    def _process_events(self) -> None:
        self.input.begin_frame()
        for ev in pygame.event.get():
            if ev.type == pygame.VIDEORESIZE:
                self.renderer.handle_resize(ev.w, ev.h)
            self.input.process_event(ev)
            # Only route text/key events to editor when no overlay is blocking
            if not self._hire_open:
                action = self.editor.handle_event(ev, self.script_engine.is_running)
                if action == "run":
                    self.script_engine.run(self.editor.get_code())
                elif action == "stop":
                    self.script_engine.stop()

    # ── Update ────────────────────────────────────────────────────────────────
    def _update(self, dt: float) -> None:
        # ── overlay toggles ───────────────────────────────────────────────────
        if self.input.shop_toggle_pressed():
            self._shop_open = not self._shop_open
            if self._shop_open:
                self._hire_open = False

        if self.input.hire_panel_pressed():
            self._hire_open = not self._hire_open
            if self._hire_open:
                self._shop_open = False

        # ── shop purchases ────────────────────────────────────────────────────
        if self._shop_open:
            idx = self.input.buy_item_index()
            if idx is not None and idx < len(SHOP_ITEMS):
                ok, msg = self.economy.buy(SHOP_ITEMS[idx].item_id, self.events)
                if not ok:
                    self.events.notify(msg)

        # ── hire panel ────────────────────────────────────────────────────────
        if self._hire_open:
            idx = self.input.buy_item_index()
            if idx is not None and idx < len(TIERS):
                ok, msg = self.employees.hire(TIERS[idx].tier_id)
                if not ok:
                    self.events.notify(msg)
            # F1-F4 fire employees
            fire_idx = self.input.fire_index_pressed()
            if fire_idx is not None:
                if fire_idx < self.employees.count:
                    emp_name = self.employees.employees[fire_idx].name
                    self.employees.fire(fire_idx)
                    self.events.notify(f"Fired: {emp_name}")

        # ── robot + world ─────────────────────────────────────────────────────
        if not self.script_engine.is_running:
            self.office.update(dt, self.input, self.events)
        else:
            self.office.robot.update(dt)
            self.office.camera.update(dt, *self.office.robot.center_pixel_pos)

        # ── all systems ───────────────────────────────────────────────────────
        self.script_engine.update(dt)
        self.employees.update(dt)
        self.economy.update(dt, self.progression, self.events)
        self.missions.update(dt)
        self.events.update(dt)
        self.editor.update(dt, self.script_engine, self.progression)

        self._fps_samples.append(self.clock.get_fps())
        if len(self._fps_samples) > 30:
            self._fps_samples.pop(0)

    # ── Draw ──────────────────────────────────────────────────────────────────
    def _draw(self) -> None:
        self.renderer.begin_frame()

        # Left: editor
        self.editor.draw(self.renderer.surface, self.script_engine,
                         self.progression, self.economy)

        # Right: world (employees drawn inside world clip)
        self.office.draw(self.renderer, self.employees)

        # Right-panel HUD overlays (drawn outside clip, over whole surface)
        self.renderer.draw_energy_bar(self.office.robot.energy_ratio)
        self.renderer.draw_level_hud(self.progression)
        self.renderer.draw_employee_hud(self.employees)
        self.renderer.draw_mission_hud(self.missions)
        self.renderer.draw_toasts(self.events.toasts)

        if self.input.debug_overlay_visible:
            self._draw_debug()

        # Full-screen overlays last
        self.renderer.draw_mission_complete_overlay(self.missions)
        if self._hire_open:
            self.renderer.draw_hire_panel(self.employees, self.economy, self.progression)
        elif self._shop_open:
            self.renderer.draw_shop_overlay(self.economy, self.progression)

        self.renderer.present()

    def _draw_debug(self) -> None:
        avg = sum(self._fps_samples) / len(self._fps_samples) if self._fps_samples else 0
        r, e, m = self.office.robot, self.script_engine, self.missions
        lines = [
            f"FPS: {avg:.1f}",
            f"Tile: ({r.grid_x}, {r.grid_y})  Facing: {r.facing}",
            f"Energy: {r.energy:.0f}  Moving: {r.is_moving}",
            f"Script: {'running' if e.is_running else 'idle'}",
            f"XP: {self.progression.xp}  |  {self.progression.level.title}",
            f"$ {self.economy.salary}  Rep:{self.economy.reputation}  Stars:{self.economy.git_stars}",
            f"Mission: {m.active.title if m.active else 'none'}  Done:{m.total_completed}",
            f"Staff: {self.employees.count}/{c.MAX_EMPLOYEES}",
            "F3:debug  F5:run  F6:stop  TAB:shop  H:hire  ESC:quit",
        ]
        self.renderer.draw_debug_overlay(lines, x_offset=c.GAME_VIEWPORT_X)
