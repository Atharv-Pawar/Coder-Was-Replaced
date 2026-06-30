"""
Renderer.

Owns the actual OS window and the logical "virtual" surface the game
draws to. We render everything at a fixed logical resolution
(constants.SCREEN_WIDTH x SCREEN_HEIGHT) and then scale that surface up
to whatever the real window size is. This means gameplay code never has
to worry about the user resizing the window or running on a different
monitor DPI.
"""

from __future__ import annotations

import pygame

from engine import constants as c
from engine.camera import Camera
from engine.tilemap import TileMap, TileType

_TILE_COLORS = {
    TileType.FLOOR: c.COLOR_FLOOR,
    TileType.FLOOR_ALT: c.COLOR_FLOOR_ALT,
    TileType.WALL: c.COLOR_WALL,
    TileType.DESK: c.COLOR_DESK,
}


class Renderer:
    def __init__(self):
        pygame.display.set_caption(c.WINDOW_TITLE)
        self.window = pygame.display.set_mode(
            (c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.RESIZABLE
        )
        # Logical surface we actually draw to; gets scaled to self.window.
        self.surface = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))

        self.debug_font = pygame.font.SysFont("consolas", c.DEBUG_FONT_SIZE)
        if self.debug_font is None:
            self.debug_font = pygame.font.Font(None, c.DEBUG_FONT_SIZE)

    # -- frame lifecycle ---------------------------------------------------
    def begin_frame(self) -> None:
        self.surface.fill(c.COLOR_BG)

    def present(self) -> None:
        window_w, window_h = self.window.get_size()
        scaled = pygame.transform.smoothscale(self.surface, (window_w, window_h))
        self.window.blit(scaled, (0, 0))
        pygame.display.flip()

    def handle_resize(self, width: int, height: int) -> None:
        self.window = pygame.display.set_mode((width, height), pygame.RESIZABLE)

    # -- world rendering -----------------------------------------------
    def draw_tilemap(self, tile_map: TileMap, camera: Camera) -> None:
        ts = tile_map.tile_size

        # Only draw the tiles actually visible in the viewport (basic culling).
        first_col = max(0, int(camera.x // ts))
        first_row = max(0, int(camera.y // ts))
        last_col = min(tile_map.width, int((camera.x + camera.viewport_width) // ts) + 1)
        last_row = min(tile_map.height, int((camera.y + camera.viewport_height) // ts) + 1)

        for y in range(first_row, last_row):
            for x in range(first_col, last_col):
                tile = tile_map.get_tile(x, y)
                color = _TILE_COLORS.get(tile.tile_type, c.COLOR_FLOOR)
                screen_x, screen_y = camera.world_to_screen(x * ts, y * ts)
                rect = pygame.Rect(int(screen_x), int(screen_y), ts, ts)
                pygame.draw.rect(self.surface, color, rect)
                pygame.draw.rect(self.surface, c.COLOR_GRID, rect, width=1)

    def draw_entity_rect(
        self,
        camera: Camera,
        world_x: float,
        world_y: float,
        size: int,
        color: tuple[int, int, int],
        outline: tuple[int, int, int] | None = None,
        facing: tuple[int, int] | None = None,
    ) -> None:
        """Draws a Phase-1 placeholder entity (a colored square) at a world
        pixel position, plus a small triangle indicating facing direction.
        """
        screen_x, screen_y = camera.world_to_screen(world_x, world_y)
        rect = pygame.Rect(int(screen_x), int(screen_y), size, size)
        pygame.draw.rect(self.surface, color, rect, border_radius=4)
        if outline:
            pygame.draw.rect(self.surface, outline, rect, width=2, border_radius=4)

        if facing:
            cx, cy = rect.center
            dx, dy = facing
            tip = (cx + dx * size * 0.4, cy + dy * size * 0.4)
            left = (cx - dy * size * 0.2 - dx * size * 0.1, cy + dx * size * 0.2 - dy * size * 0.1)
            right = (cx + dy * size * 0.2 - dx * size * 0.1, cy - dx * size * 0.2 - dy * size * 0.1)
            pygame.draw.polygon(self.surface, outline or (20, 20, 20), [tip, left, right])

    # -- UI / debug ------------------------------------------------------
    def draw_text(self, text: str, x: int, y: int, color=c.COLOR_DEBUG_TEXT) -> None:
        surf = self.debug_font.render(text, True, color)
        self.surface.blit(surf, (x, y))

    def draw_debug_overlay(self, lines: list[str]) -> None:
        padding = 6
        line_height = c.DEBUG_FONT_SIZE + 2
        box_width = 260
        box_height = padding * 2 + line_height * len(lines)

        overlay = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        overlay.fill((*c.COLOR_DEBUG_BG, 150))
        self.surface.blit(overlay, (8, 8))

        for i, line in enumerate(lines):
            self.draw_text(line, 8 + padding, 8 + padding + i * line_height)
