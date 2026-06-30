"""
Game: owns the main loop, fixed timestep, and top-level wiring between
the renderer, input, and the current level (the Office, for now).
"""

from __future__ import annotations

import pygame

from engine import constants as c
from engine.events import EventBus
from engine.input import InputManager
from engine.renderer import Renderer
from game.office import Office


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.init()
        pygame.font.init()

        self.renderer = Renderer()
        self.input = InputManager()
        self.clock = pygame.time.Clock()
        self.events = EventBus()

        self.office = Office()

        self._running = False
        self._fps_samples: list[float] = []

    def run(self) -> None:
        self._running = True
        while self._running:
            dt = self.clock.tick(c.FPS) / 1000.0
            dt = min(dt, 1 / 20)  # clamp huge dt spikes (e.g. window drag-resize)

            self._process_events()
            self._update(dt)
            self._draw()

            if self.input.quit_requested:
                self._running = False

        pygame.quit()

    # -- internals -----------------------------------------------------
    def _process_events(self) -> None:
        self.input.begin_frame()
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                self.renderer.handle_resize(event.w, event.h)
            self.input.process_event(event)

    def _update(self, dt: float) -> None:
        self.office.update(dt, self.input, self.events)
        self.events.update(dt)

        self._fps_samples.append(self.clock.get_fps())
        if len(self._fps_samples) > 30:
            self._fps_samples.pop(0)

    def _draw(self) -> None:
        self.renderer.begin_frame()
        self.office.draw(self.renderer)
        self.renderer.draw_energy_bar(self.office.robot.energy_ratio)
        self.renderer.draw_toasts(self.events.toasts)

        if self.input.debug_overlay_visible:
            self._draw_debug_overlay()

        self.renderer.present()

    def _draw_debug_overlay(self) -> None:
        avg_fps = sum(self._fps_samples) / len(self._fps_samples) if self._fps_samples else 0.0
        robot = self.office.robot
        lines = [
            f"FPS: {avg_fps:.1f}",
            f"Tile: ({robot.grid_x}, {robot.grid_y})",
            f"Facing: {robot.facing}",
            f"Moving: {robot.is_moving}",
            f"Energy: {robot.energy:.0f}/{c.PLAYER_MAX_ENERGY:.0f}",
            "F3: toggle overlay | E: interact | ESC: quit",
        ]
        self.renderer.draw_debug_overlay(lines)
