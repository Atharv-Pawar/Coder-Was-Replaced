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
        # Clip all world rendering to the game panel area.
        self._game_clip = pygame.Rect(c.GAME_VIEWPORT_X, 0,
                                      c.GAME_VIEWPORT_W, c.GAME_VIEWPORT_H)

    def present(self) -> None:
        window_w, window_h = self.window.get_size()
        scaled = pygame.transform.smoothscale(self.surface, (window_w, window_h))
        self.window.blit(scaled, (0, 0))
        pygame.display.flip()

    def begin_world_draw(self) -> None:
        """Call before drawing any world content to apply the game-panel clip."""
        self.surface.set_clip(self._game_clip)

    def end_world_draw(self) -> None:
        """Call after world drawing to restore full-surface clip."""
        self.surface.set_clip(None)

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

    def draw_debug_overlay(self, lines: list[str], x_offset: int = 0) -> None:
        padding = 6
        line_height = c.DEBUG_FONT_SIZE + 2
        box_width = 310
        box_height = padding * 2 + line_height * len(lines)

        overlay = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        overlay.fill((*c.COLOR_DEBUG_BG, 150))
        self.surface.blit(overlay, (8 + x_offset, 8))

        for i, line in enumerate(lines):
            self.draw_text(line, 8 + x_offset + padding, 8 + padding + i * line_height)

    def draw_object(self, camera: Camera, obj) -> None:
        """Draws a Phase-2 placeholder office object: a colored shape with
        a short text label, distinct per ObjectType. Will be replaced by
        real sprites once art assets exist.
        """
        from game.objects import ObjectType  # local import avoids a cycle

        if obj.consumed:
            return

        ts = c.TILE_SIZE
        screen_x, screen_y = camera.world_to_screen(obj.grid_x * ts, obj.grid_y * ts)
        rect = pygame.Rect(int(screen_x) + 3, int(screen_y) + 3, ts - 6, ts - 6)

        colors = {
            ObjectType.DESK: c.COLOR_OBJ_DESK,
            ObjectType.COFFEE_MACHINE: c.COLOR_OBJ_COFFEE,
            ObjectType.BUG: c.COLOR_OBJ_BUG,
            ObjectType.JIRA_TICKET: c.COLOR_OBJ_JIRA,
            ObjectType.SERVER_RACK: c.COLOR_OBJ_SERVER,
            ObjectType.GIT_REPO: c.COLOR_OBJ_GIT,
            ObjectType.WIFI_ROUTER: c.COLOR_OBJ_ROUTER,
            ObjectType.MEETING_ROOM: c.COLOR_OBJ_MEETING_DOOR,
            ObjectType.LAPTOP: c.COLOR_OBJ_LAPTOP,
        }
        color = colors.get(obj.obj_type, c.COLOR_OBJ_DESK)

        if obj.obj_type == ObjectType.BUG:
            # Small diamond instead of a square so bugs read as "pick-ups".
            cx, cy = rect.center
            half = rect.width // 2
            points = [(cx, cy - half), (cx + half, cy), (cx, cy + half), (cx - half, cy)]
            pygame.draw.polygon(self.surface, color, points)
        else:
            pygame.draw.rect(self.surface, color, rect, border_radius=5)

        if obj.obj_type == ObjectType.SERVER_RACK:
            pygame.draw.circle(self.surface, c.COLOR_OBJ_SERVER_LIGHT, rect.center, 4)
        elif obj.obj_type == ObjectType.WIFI_ROUTER:
            pygame.draw.circle(self.surface, c.COLOR_OBJ_ROUTER_LIGHT, (rect.centerx, rect.top + 4), 3)
        elif obj.obj_type == ObjectType.COFFEE_MACHINE:
            pygame.draw.rect(
                self.surface, c.COLOR_OBJ_COFFEE_ACCENT,
                pygame.Rect(rect.centerx - 5, rect.bottom - 9, 10, 6),
            )

        from game.objects import OBJECT_LABELS
        label = OBJECT_LABELS.get(obj.obj_type, "")
        if label:
            label_surf = self.debug_font.render(label, True, (255, 255, 255))
            label_rect = label_surf.get_rect(center=rect.center)
            self.surface.blit(label_surf, label_rect)

    def draw_interaction_prompt(self, camera: Camera, grid_x: int, grid_y: int, text: str) -> None:
        ts = c.TILE_SIZE
        screen_x, screen_y = camera.world_to_screen(grid_x * ts, grid_y * ts)

        label_surf = self.debug_font.render(text, True, c.COLOR_INTERACT_PROMPT_TEXT)
        padding = 4
        bg_rect = pygame.Rect(
            int(screen_x) - padding,
            int(screen_y) - label_surf.get_height() - padding * 2,
            label_surf.get_width() + padding * 2,
            label_surf.get_height() + padding * 2,
        )
        bg = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg.fill((*c.COLOR_INTERACT_PROMPT_BG, 180))
        self.surface.blit(bg, bg_rect.topleft)
        self.surface.blit(label_surf, (bg_rect.x + padding, bg_rect.y + padding))

    def draw_toasts(self, toasts: list) -> None:
        """Draws active toast notifications stacked above the bottom edge,
        most recent at the bottom, fading in/out per `Toast.alpha`.
        Positions are offset to stay within the game viewport panel.
        """
        spacing = 4
        bottom_margin = 24
        gx = c.GAME_VIEWPORT_X
        gw = c.GAME_VIEWPORT_W
        y = c.SCREEN_HEIGHT - bottom_margin

        for toast in reversed(toasts):
            text_surf = self.debug_font.render(toast.text, True, c.COLOR_TOAST_TEXT)
            padding = 8
            box_w = text_surf.get_width() + padding * 2
            box_h = text_surf.get_height() + padding * 2
            x = gx + (gw - box_w) // 2
            y -= box_h

            alpha = int(220 * toast.alpha)
            box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box.fill((*c.COLOR_TOAST_BG, min(200, alpha)))
            self.surface.blit(box, (x, y))

            text_with_alpha = text_surf.copy()
            text_with_alpha.set_alpha(alpha)
            self.surface.blit(text_with_alpha, (x + padding, y + padding))

            y -= spacing

    def draw_level_hud(self, progression) -> None:
        """Draws the level badge and XP bar in the top-right of the game panel."""
        badge_w, badge_h = 180, 36
        x = c.SCREEN_WIDTH - badge_w - 10
        y = 40  # sits just below the energy bar

        bg = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        bg.fill((*c.COLOR_LEVEL_BG, 210))
        self.surface.blit(bg, (x, y))
        pygame.draw.rect(self.surface, c.COLOR_LEVEL_BORDER,
                         pygame.Rect(x, y, badge_w, badge_h), width=1, border_radius=4)

        title_surf = self.debug_font.render(
            progression.level.title, True, c.COLOR_LEVEL_TEXT)
        self.surface.blit(title_surf, (x + 6, y + 4))

        bar_x = x + 6
        bar_y = y + badge_h - 11
        bar_w_inner = badge_w - 12
        ratio = progression.xp_progress_ratio
        pygame.draw.rect(self.surface, (30, 33, 42),
                         pygame.Rect(bar_x, bar_y, bar_w_inner, 6), border_radius=3)
        if ratio > 0:
            fill_color = c.COLOR_XP_BAR_FILL2 if ratio > 0.75 else c.COLOR_XP_BAR_FILL
            pygame.draw.rect(self.surface, fill_color,
                             pygame.Rect(bar_x, bar_y, max(4, int(bar_w_inner * ratio)), 6),
                             border_radius=3)

        xp_surf = self.debug_font.render(f"{progression.xp} XP", True, c.COLOR_LEVEL_XP_TEXT)
        self.surface.blit(xp_surf, (x + badge_w - xp_surf.get_width() - 6, y + 4))

    def draw_energy_bar(self, ratio: float) -> None:
        bar_w, bar_h = 140, 14
        x = c.SCREEN_WIDTH - bar_w - 12
        y = 12

        bg_rect = pygame.Rect(x, y, bar_w, bar_h)
        pygame.draw.rect(self.surface, (30, 30, 36), bg_rect, border_radius=4)

        fill_w = int(bar_w * max(0.0, min(1.0, ratio)))
        if fill_w > 0:
            fill_color = (90, 200, 120) if ratio > 0.3 else (210, 90, 70)
            fill_rect = pygame.Rect(x, y, fill_w, bar_h)
            pygame.draw.rect(self.surface, fill_color, fill_rect, border_radius=4)

        pygame.draw.rect(self.surface, (10, 10, 14), bg_rect, width=2, border_radius=4)
        self.draw_text("Energy", x, y + bar_h + 2, color=(180, 180, 190))
