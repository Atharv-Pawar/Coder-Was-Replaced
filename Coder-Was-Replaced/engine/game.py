"""
Game: owns the main loop, fixed timestep, and top-level wiring between
the renderer, input, editor, scripting engine, and the office level.

Phase 3 introduces the split-screen layout:
  Left  (490 px) – script editor
  Right (790 px) – game world (office + robot)

The player writes Python in the editor, clicks Run (or F5), and watches
the robot execute each instruction one by one with smooth animations.
"""

from __future__ import annotations

import pygame

from engine import constants as c
from engine.events import EventBus
from engine.input import InputManager
from engine.renderer import Renderer
from engine.scripting import ScriptEngine
from game.editor import Editor
from game.office import Office
from game.progression import Progression


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        pygame.font.init()
        pygame.key.start_text_input()  # enable TEXTINPUT events for the editor

        self.renderer = Renderer()
        self.input = InputManager()
        self.clock = pygame.time.Clock()
        self.events = EventBus()

        self.office = Office()
        self.progression = Progression()
        self.editor = Editor()
        self.script_engine = ScriptEngine(self.office, self.events, self.progression)

        self._running = False
        self._fps_samples: list[float] = []

    def run(self) -> None:
        self._running = True
        while self._running:
            dt = self.clock.tick(c.FPS) / 1000.0
            dt = min(dt, 1 / 20)  # clamp spikes from window drag/resize

            self._process_events()
            self._update(dt)
            self._draw()

            if self.input.quit_requested:
                self.script_engine.stop()
                self._running = False

        pygame.quit()

    # ── event processing ─────────────────────────────────────────────────
    def _process_events(self) -> None:
        self.input.begin_frame()
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                self.renderer.handle_resize(event.w, event.h)
            self.input.process_event(event)

            # Route keyboard/mouse events to the editor.
            action = self.editor.handle_event(event, self.script_engine.is_running)
            if action == "run":
                self._run_script()
            elif action == "stop":
                self.script_engine.stop()

    # ── update ───────────────────────────────────────────────────────────
    def _update(self, dt: float) -> None:
        # Manual robot control only when the script engine is idle.
        if not self.script_engine.is_running:
            self.office.update(dt, self.input, self.events)
        else:
            # Office still updates the camera and robot animation even when
            # the script drives the robot; we just skip keyboard movement.
            self.office.robot.update(dt)
            self.office.camera.update(dt, *self.office.robot.center_pixel_pos)

        self.script_engine.update(dt)
        self.events.update(dt)
        self.editor.update(dt, self.script_engine, self.progression)

        self._fps_samples.append(self.clock.get_fps())
        if len(self._fps_samples) > 30:
            self._fps_samples.pop(0)

    # ── rendering ────────────────────────────────────────────────────────
    def _draw(self) -> None:
        self.renderer.begin_frame()

        # Left panel: editor
        self.editor.draw(self.renderer.surface, self.script_engine, self.progression)

        # Right panel: game world
        self.office.draw(self.renderer)
        self.renderer.draw_energy_bar(self.office.robot.energy_ratio)
        self.renderer.draw_level_hud(self.progression)
        self.renderer.draw_toasts(self.events.toasts)

        if self.input.debug_overlay_visible:
            self._draw_debug_overlay()

        self.renderer.present()

    def _draw_debug_overlay(self) -> None:
        avg_fps = sum(self._fps_samples) / len(self._fps_samples) if self._fps_samples else 0.0
        robot = self.office.robot
        engine = self.script_engine
        lines = [
            f"FPS: {avg_fps:.1f}",
            f"Tile: ({robot.grid_x}, {robot.grid_y})",
            f"Facing: {robot.facing}",
            f"Moving: {robot.is_moving}",
            f"Energy: {robot.energy:.0f}/{c.PLAYER_MAX_ENERGY:.0f}",
            f"Script: {'running' if engine.is_running else 'idle'}",
            f"XP: {self.progression.xp}  |  {self.progression.level.title}",
            "F3: overlay | F5: run | F6: stop | ESC: quit",
        ]
        # Draw overlay inside the game panel (offset by GAME_VIEWPORT_X)
        self.renderer.draw_debug_overlay(lines, x_offset=c.GAME_VIEWPORT_X)

    # ── script control ───────────────────────────────────────────────────
    def _run_script(self) -> None:
        code = self.editor.get_code()
        self.script_engine.run(code)
