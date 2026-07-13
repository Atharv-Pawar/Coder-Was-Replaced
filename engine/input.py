"""Keyboard and mouse input manager."""
from __future__ import annotations
import pygame


class InputManager:
    def __init__(self):
        self._held: set[int] = set()
        self._pressed: set[int] = set()
        self._released: set[int] = set()
        self.quit_requested = False
        self.debug_overlay_visible = True

    def begin_frame(self) -> None:
        self._pressed.clear()
        self._released.clear()

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.quit_requested = True
        elif event.type == pygame.KEYDOWN:
            if event.key not in self._held:
                self._pressed.add(event.key)
            self._held.add(event.key)
            if event.key == pygame.K_F3:
                self.debug_overlay_visible = not self.debug_overlay_visible
            elif event.key == pygame.K_ESCAPE:
                self.quit_requested = True
        elif event.type == pygame.KEYUP:
            self._held.discard(event.key)
            self._released.add(event.key)

    def is_held(self, key: int) -> bool:
        return key in self._held

    def was_pressed(self, key: int) -> bool:
        return key in self._pressed

    def movement_direction(self) -> tuple[int, int] | None:
        if self.was_pressed(pygame.K_UP)    or self.was_pressed(pygame.K_w): return (0, -1)
        if self.was_pressed(pygame.K_DOWN)  or self.was_pressed(pygame.K_s): return (0, 1)
        if self.was_pressed(pygame.K_LEFT)  or self.was_pressed(pygame.K_a): return (-1, 0)
        if self.was_pressed(pygame.K_RIGHT) or self.was_pressed(pygame.K_d): return (1, 0)
        return None

    def interact_pressed(self) -> bool:
        return self.was_pressed(pygame.K_e) or self.was_pressed(pygame.K_SPACE)

    def shop_toggle_pressed(self) -> bool:
        return self.was_pressed(pygame.K_TAB)

    def hire_panel_pressed(self) -> bool:
        return self.was_pressed(pygame.K_h)

    def fire_index_pressed(self) -> int | None:
        """F1-F4 fires employee 0-3 when the hire panel is open."""
        for i, key in enumerate([pygame.K_F1, pygame.K_F2, pygame.K_F3, pygame.K_F4]):
            if self.was_pressed(key):
                return i
        return None

    def buy_item_index(self) -> int | None:
        for i, key in enumerate([pygame.K_1, pygame.K_2, pygame.K_3,
                                  pygame.K_4, pygame.K_5, pygame.K_6,
                                  pygame.K_7, pygame.K_8, pygame.K_9]):
            if self.was_pressed(key):
                return i
        return None
