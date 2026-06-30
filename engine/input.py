"""
Input manager.

Wraps pygame's key state so the rest of the engine can ask semantic
questions ("was this just pressed this frame?") instead of dealing with
raw pygame events directly. This will later also gate input during script
execution (Phase 3), where the robot is driven by code, not the keyboard.
"""

from __future__ import annotations

import pygame


class InputManager:
    def __init__(self):
        self._held: set[int] = set()
        self._pressed_this_frame: set[int] = set()
        self._released_this_frame: set[int] = set()
        self.quit_requested = False

        # Toggled by F3, read by the game loop to show/hide the debug overlay.
        self.debug_overlay_visible = True

    def begin_frame(self) -> None:
        """Call once per frame, before processing events."""
        self._pressed_this_frame.clear()
        self._released_this_frame.clear()

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.quit_requested = True
        elif event.type == pygame.KEYDOWN:
            if event.key not in self._held:
                self._pressed_this_frame.add(event.key)
            self._held.add(event.key)

            if event.key == pygame.K_F3:
                self.debug_overlay_visible = not self.debug_overlay_visible
            elif event.key == pygame.K_ESCAPE:
                self.quit_requested = True
        elif event.type == pygame.KEYUP:
            self._held.discard(event.key)
            self._released_this_frame.add(event.key)

    def is_held(self, key: int) -> bool:
        return key in self._held

    def was_pressed(self, key: int) -> bool:
        return key in self._pressed_this_frame

    def was_released(self, key: int) -> bool:
        return key in self._released_this_frame

    def movement_direction(self) -> tuple[int, int] | None:
        """Returns a (dx, dy) tile-step for the most recently pressed
        movement key this frame, or None. Arrow keys and WASD both work.
        """
        if self.was_pressed(pygame.K_UP) or self.was_pressed(pygame.K_w):
            return 0, -1
        if self.was_pressed(pygame.K_DOWN) or self.was_pressed(pygame.K_s):
            return 0, 1
        if self.was_pressed(pygame.K_LEFT) or self.was_pressed(pygame.K_a):
            return -1, 0
        if self.was_pressed(pygame.K_RIGHT) or self.was_pressed(pygame.K_d):
            return 1, 0
        return None
