"""Renderer — owns the window and all draw calls for Phases 1-6."""
from __future__ import annotations
import pygame
from engine import constants as c
from engine.camera import Camera
from engine.tilemap import TileMap, TileType

_TILE_COLORS = {
    TileType.FLOOR:     c.COLOR_FLOOR,
    TileType.FLOOR_ALT: c.COLOR_FLOOR_ALT,
    TileType.WALL:      c.COLOR_WALL,
}


class Renderer:
    def __init__(self):
        pygame.display.set_caption(c.WINDOW_TITLE)
        self.window  = pygame.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.RESIZABLE)
        self.surface = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        self.debug_font = pygame.font.SysFont("consolas", c.DEBUG_FONT_SIZE) or pygame.font.Font(None, c.DEBUG_FONT_SIZE)
        self._game_clip = pygame.Rect(c.GAME_VIEWPORT_X, 0, c.GAME_VIEWPORT_W, c.GAME_VIEWPORT_H)

    # ── Frame lifecycle ───────────────────────────────────────────────────────
    def begin_frame(self) -> None:
        self.surface.fill(c.COLOR_BG)
        self._game_clip = pygame.Rect(c.GAME_VIEWPORT_X, 0, c.GAME_VIEWPORT_W, c.GAME_VIEWPORT_H)

    def present(self) -> None:
        ww, wh = self.window.get_size()
        self.window.blit(pygame.transform.smoothscale(self.surface, (ww, wh)), (0, 0))
        pygame.display.flip()

    def handle_resize(self, w: int, h: int) -> None:
        self.window = pygame.display.set_mode((w, h), pygame.RESIZABLE)

    def begin_world_draw(self) -> None:
        self.surface.set_clip(self._game_clip)

    def end_world_draw(self) -> None:
        self.surface.set_clip(None)

    # ── World rendering ───────────────────────────────────────────────────────
    def draw_tilemap(self, tile_map: TileMap, camera: Camera) -> None:
        ts = tile_map.tile_size
        fc = max(0, int(camera.x // ts))
        fr = max(0, int(camera.y // ts))
        lc = min(tile_map.width,  int((camera.x + camera.viewport_width)  // ts) + 1)
        lr = min(tile_map.height, int((camera.y + camera.viewport_height) // ts) + 1)
        for y in range(fr, lr):
            for x in range(fc, lc):
                color = _TILE_COLORS.get(tile_map.get_tile(x, y).tile_type, c.COLOR_FLOOR)
                sx, sy = camera.world_to_screen(x * ts, y * ts)
                rect = pygame.Rect(int(sx), int(sy), ts, ts)
                pygame.draw.rect(self.surface, color, rect)
                pygame.draw.rect(self.surface, c.COLOR_GRID, rect, width=1)

    def draw_entity_rect(self, camera, wx, wy, size, color, outline=None, facing=None) -> None:
        sx, sy = camera.world_to_screen(wx, wy)
        rect = pygame.Rect(int(sx), int(sy), size, size)
        pygame.draw.rect(self.surface, color, rect, border_radius=4)
        if outline:
            pygame.draw.rect(self.surface, outline, rect, width=2, border_radius=4)
        if facing:
            cx, cy = rect.center
            dx, dy = facing
            tip   = (cx + dx * size * 0.4,  cy + dy * size * 0.4)
            left  = (cx - dy * size * 0.2 - dx * size * 0.1, cy + dx * size * 0.2 - dy * size * 0.1)
            right = (cx + dy * size * 0.2 - dx * size * 0.1, cy - dx * size * 0.2 - dy * size * 0.1)
            pygame.draw.polygon(self.surface, outline or (20, 20, 20), [tip, left, right])

    def draw_object(self, camera: Camera, obj) -> None:
        from game.objects import ObjectType, OBJECT_LABELS
        if obj.consumed:
            return
        ts = c.TILE_SIZE
        sx, sy = camera.world_to_screen(obj.grid_x * ts, obj.grid_y * ts)
        rect = pygame.Rect(int(sx) + 3, int(sy) + 3, ts - 6, ts - 6)
        color_map = {
            ObjectType.DESK: c.COLOR_OBJ_DESK, ObjectType.COFFEE_MACHINE: c.COLOR_OBJ_COFFEE,
            ObjectType.BUG: c.COLOR_OBJ_BUG, ObjectType.JIRA_TICKET: c.COLOR_OBJ_JIRA,
            ObjectType.SERVER_RACK: c.COLOR_OBJ_SERVER, ObjectType.GIT_REPO: c.COLOR_OBJ_GIT,
            ObjectType.WIFI_ROUTER: c.COLOR_OBJ_ROUTER, ObjectType.MEETING_ROOM: c.COLOR_OBJ_MEETING_DOOR,
            ObjectType.LAPTOP: c.COLOR_OBJ_LAPTOP,
        }
        color = color_map.get(obj.obj_type, c.COLOR_OBJ_DESK)
        if obj.obj_type == ObjectType.BUG:
            cx, cy = rect.center
            h = rect.width // 2
            pygame.draw.polygon(self.surface, color, [(cx, cy-h),(cx+h,cy),(cx,cy+h),(cx-h,cy)])
        else:
            pygame.draw.rect(self.surface, color, rect, border_radius=5)
        if obj.obj_type == ObjectType.SERVER_RACK:
            pygame.draw.circle(self.surface, c.COLOR_OBJ_SERVER_LIGHT, rect.center, 4)
        elif obj.obj_type == ObjectType.WIFI_ROUTER:
            pygame.draw.circle(self.surface, c.COLOR_OBJ_ROUTER_LIGHT, (rect.centerx, rect.top + 4), 3)
        elif obj.obj_type == ObjectType.COFFEE_MACHINE:
            pygame.draw.rect(self.surface, c.COLOR_OBJ_COFFEE_ACCENT,
                             pygame.Rect(rect.centerx - 5, rect.bottom - 9, 10, 6))
        label = OBJECT_LABELS.get(obj.obj_type, "")
        if label:
            ls = self.debug_font.render(label, True, (255, 255, 255))
            self.surface.blit(ls, ls.get_rect(center=rect.center))

    def draw_interaction_prompt(self, camera: Camera, gx: int, gy: int, text: str) -> None:
        sx, sy = camera.world_to_screen(gx * c.TILE_SIZE, gy * c.TILE_SIZE)
        ls = self.debug_font.render(text, True, c.COLOR_INTERACT_PROMPT_TEXT)
        p = 4
        bg = pygame.Rect(int(sx) - p, int(sy) - ls.get_height() - p*2, ls.get_width() + p*2, ls.get_height() + p*2)
        ov = pygame.Surface(bg.size, pygame.SRCALPHA); ov.fill((*c.COLOR_INTERACT_PROMPT_BG, 180))
        self.surface.blit(ov, bg.topleft)
        self.surface.blit(ls, (bg.x + p, bg.y + p))

    # ── HUD elements ──────────────────────────────────────────────────────────
    def draw_energy_bar(self, ratio: float) -> None:
        bw, bh = 140, 14
        x = c.SCREEN_WIDTH - bw - 12
        y = 12
        pygame.draw.rect(self.surface, (30, 30, 36), pygame.Rect(x, y, bw, bh), border_radius=4)
        fw = int(bw * max(0.0, min(1.0, ratio)))
        if fw > 0:
            pygame.draw.rect(self.surface, (90, 200, 120) if ratio > 0.3 else (210, 90, 70),
                             pygame.Rect(x, y, fw, bh), border_radius=4)
        pygame.draw.rect(self.surface, (10, 10, 14), pygame.Rect(x, y, bw, bh), width=2, border_radius=4)
        self.draw_text("Energy", x, y + bh + 2, color=(180, 180, 190))

    def draw_level_hud(self, progression) -> None:
        bw, bh = 180, 36
        x = c.SCREEN_WIDTH - bw - 10
        y = 40
        bg = pygame.Surface((bw, bh), pygame.SRCALPHA); bg.fill((*c.COLOR_LEVEL_BG, 210))
        self.surface.blit(bg, (x, y))
        pygame.draw.rect(self.surface, c.COLOR_LEVEL_BORDER, pygame.Rect(x, y, bw, bh), width=1, border_radius=4)
        self.surface.blit(self.debug_font.render(progression.level.title, True, c.COLOR_LEVEL_TEXT), (x+6, y+4))
        xp_s = self.debug_font.render(f"{progression.xp} XP", True, c.COLOR_LEVEL_XP_TEXT)
        self.surface.blit(xp_s, (x + bw - xp_s.get_width() - 6, y+4))
        bx, by, biw = x+6, y+bh-11, bw-12
        pygame.draw.rect(self.surface, (30,33,42), pygame.Rect(bx, by, biw, 6), border_radius=3)
        fw = max(0, int(biw * progression.xp_progress_ratio))
        if fw:
            fc = c.COLOR_XP_BAR_FILL2 if progression.xp_progress_ratio > 0.75 else c.COLOR_XP_BAR_FILL
            pygame.draw.rect(self.surface, fc, pygame.Rect(bx, by, fw, 6), border_radius=3)

    def draw_toasts(self, toasts: list) -> None:
        gx, gw = c.GAME_VIEWPORT_X, c.GAME_VIEWPORT_W
        y = c.SCREEN_HEIGHT - 24
        for toast in reversed(toasts):
            ts = self.debug_font.render(toast.text, True, c.COLOR_TOAST_TEXT)
            p = 8; bw = ts.get_width() + p*2; bh = ts.get_height() + p*2
            bx = gx + (gw - bw) // 2
            y -= bh
            alpha = int(220 * toast.alpha)
            box = pygame.Surface((bw, bh), pygame.SRCALPHA); box.fill((*c.COLOR_TOAST_BG, min(200, alpha)))
            self.surface.blit(box, (bx, y))
            ta = ts.copy(); ta.set_alpha(alpha)
            self.surface.blit(ta, (bx + p, y + p))
            y -= 4

    # ── Mission HUD ───────────────────────────────────────────────────────────
    def draw_mission_hud(self, tracker) -> None:
        if tracker is None or tracker.active is None:
            return
        m = tracker.active
        lh = c.DEBUG_FONT_SIZE + 4
        pad = 8
        n_obj = len(m.objectives)
        hud_h = pad + lh * (2 + n_obj + 1) + (lh if m.time_limit else 0) + pad
        hud_w = c.MISSION_HUD_W
        x = c.SCREEN_WIDTH - hud_w - c.MISSION_HUD_MARGIN
        y = c.SCREEN_HEIGHT - hud_h - c.MISSION_HUD_MARGIN

        bg = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA); bg.fill((*c.COLOR_MISSION_BG, 220))
        self.surface.blit(bg, (x, y))
        border = c.COLOR_MISSION_TIMER_CRIT if m.is_urgent else c.COLOR_MISSION_BORDER
        pygame.draw.rect(self.surface, border, pygame.Rect(x, y, hud_w, hud_h), width=2, border_radius=6)

        cy = y + pad
        self.surface.blit(self.debug_font.render(m.title, True, c.COLOR_MISSION_TITLE), (x+pad, cy)); cy += lh
        flavour = m.flavour[:30] + "…" if len(m.flavour) > 32 else m.flavour
        self.surface.blit(self.debug_font.render(flavour, True, c.COLOR_MISSION_FLAVOUR), (x+pad, cy)); cy += lh

        for obj in m.objectives:
            col = c.COLOR_MISSION_OBJ_DONE if obj.done else c.COLOR_MISSION_OBJ_ACTIVE
            chk = "[x]" if obj.done else "[ ]"
            self.surface.blit(self.debug_font.render(f"{chk} {obj.label}: {obj.current}/{obj.target}", True, col), (x+pad, cy))
            bx2, by2, bw2 = x+pad, cy+lh-5, hud_w-pad*2
            pygame.draw.rect(self.surface, c.COLOR_MISSION_BAR_BG, pygame.Rect(bx2, by2, bw2, 4), border_radius=2)
            fw = max(0, int(bw2 * obj.progress_ratio))
            if fw:
                fc = c.COLOR_MISSION_BAR_DONE if obj.done else c.COLOR_MISSION_BAR_FILL
                pygame.draw.rect(self.surface, fc, pygame.Rect(bx2, by2, fw, 4), border_radius=2)
            cy += lh

        if m.time_limit is not None:
            rem = m.time_remaining
            mm, ss = divmod(int(rem), 60)
            tc = c.COLOR_MISSION_TIMER_CRIT if m.is_urgent else (c.COLOR_MISSION_TIMER_WARN if rem < m.time_limit * 0.5 else c.COLOR_MISSION_TIMER_OK)
            self.surface.blit(self.debug_font.render(f"Time: {mm:02d}:{ss:02d}", True, tc), (x+pad, cy)); cy += lh

        r = m.rewards
        parts = []
        if r.get("salary"):    parts.append(f"+${r['salary']}")
        if r.get("xp"):        parts.append(f"+{r['xp']}XP")
        if r.get("reputation"):parts.append(f"+{r['reputation']}Rep")
        if r.get("git_stars"): parts.append(f"+{r['git_stars']}Stars")
        self.surface.blit(self.debug_font.render("  ".join(parts), True, c.COLOR_MISSION_REWARD), (x+pad, cy))

    def draw_mission_complete_overlay(self, tracker) -> None:
        if tracker is None or tracker.just_completed is None:
            return
        m = tracker.just_completed
        alpha = int(180 * tracker.overlay_alpha)
        failed = tracker.last_failed
        bg_col  = c.COLOR_FAIL_BG    if failed else c.COLOR_COMPLETE_BG
        txt_col = c.COLOR_FAIL_TEXT  if failed else c.COLOR_COMPLETE_TEXT
        header  = "MISSION FAILED"   if failed else "MISSION COMPLETE"

        ov = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((*bg_col, min(140, alpha))); self.surface.blit(ov, (0,0))

        bw, bh = 500, 110
        bx, by = (c.SCREEN_WIDTH - bw) // 2, (c.SCREEN_HEIGHT - bh) // 2
        ban = pygame.Surface((bw, bh), pygame.SRCALPHA); ban.fill((*bg_col, min(230, alpha+50)))
        self.surface.blit(ban, (bx, by))
        pygame.draw.rect(self.surface, txt_col, pygame.Rect(bx, by, bw, bh), width=2, border_radius=8)

        big = pygame.font.SysFont("consolas,courier,monospace", 22)
        hs = big.render(header, True, txt_col); hs.set_alpha(alpha)
        self.surface.blit(hs, (bx + (bw - hs.get_width())//2, by+12))
        ts = self.debug_font.render(m.title, True, (200,215,255)); ts.set_alpha(alpha)
        self.surface.blit(ts, (bx + (bw - ts.get_width())//2, by+42))
        if not failed:
            r = m.rewards
            parts = []
            if r.get("salary"):    parts.append(f"+${r['salary']}")
            if r.get("xp"):        parts.append(f"+{r['xp']} XP")
            if r.get("reputation"):parts.append(f"+{r['reputation']} Rep")
            rs = self.debug_font.render("  ".join(parts), True, c.COLOR_MISSION_REWARD); rs.set_alpha(alpha)
            self.surface.blit(rs, (bx + (bw - rs.get_width())//2, by+68))

    # ── Shop overlay ─────────────────────────────────────────────────────────
    def draw_shop_overlay(self, economy, progression) -> None:
        from game.economy import SHOP_ITEMS
        dim = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0,0,0,160)); self.surface.blit(dim, (0,0))

        sw = 560; ih = 64; sh = 60 + ih*len(SHOP_ITEMS) + 20
        sx = (c.SCREEN_WIDTH - sw)//2; sy = max(20, (c.SCREEN_HEIGHT - sh)//2)
        bg = pygame.Surface((sw, sh), pygame.SRCALPHA); bg.fill((*c.COLOR_SHOP_BG, 245))
        self.surface.blit(bg, (sx, sy))
        pygame.draw.rect(self.surface, c.COLOR_SHOP_BORDER, pygame.Rect(sx, sy, sw, sh), width=2, border_radius=8)

        self.surface.blit(self.debug_font.render("SHOP", True, c.COLOR_SHOP_TITLE), (sx+14, sy+10))
        bs = self.debug_font.render(f"Balance: ${economy.salary}", True, c.COLOR_SALARY)
        self.surface.blit(bs, (sx+sw-bs.get_width()-14, sy+10))
        hs = self.debug_font.render("[TAB] close  |  [1-6] buy", True, (100,110,140))
        self.surface.blit(hs, (sx+(sw-hs.get_width())//2, sy+28))
        pygame.draw.line(self.surface, c.COLOR_SHOP_BORDER, (sx, sy+46), (sx+sw, sy+46))

        for i, item in enumerate(SHOP_ITEMS):
            iy = sy + 50 + i*ih
            owned = economy.has_upgrade(item.item_id)
            affordable = economy.can_afford(item.item_id)
            rbg = pygame.Surface((sw-4, ih-4), pygame.SRCALPHA)
            rbg.fill((30,60,40,200) if owned else (*c.COLOR_SHOP_ITEM_BG, 200))
            self.surface.blit(rbg, (sx+2, iy+2))
            kc = c.COLOR_SHOP_OWNED if owned else (180,190,210)
            self.surface.blit(self.debug_font.render(f"[{i+1}]", True, kc), (sx+10, iy+10))
            nc = c.COLOR_SHOP_OWNED if owned else (200,215,240)
            self.surface.blit(self.debug_font.render(item.name, True, nc), (sx+46, iy+8))
            self.surface.blit(self.debug_font.render(item.effect_line, True, (130,140,160)), (sx+46, iy+28))
            if owned:
                ss2 = self.debug_font.render("OWNED", True, c.COLOR_SHOP_OWNED)
                self.surface.blit(ss2, (sx+sw-ss2.get_width()-14, iy+18))
            else:
                cc = c.COLOR_SHOP_AFFORD if affordable else c.COLOR_SHOP_CANT
                cs = self.debug_font.render(f"${item.cost_salary}", True, cc)
                self.surface.blit(cs, (sx+sw-cs.get_width()-14, iy+18))

    # ── Debug overlay ─────────────────────────────────────────────────────────
    def draw_text(self, text: str, x: int, y: int, color=None) -> None:
        self.surface.blit(self.debug_font.render(text, True, color or c.COLOR_DEBUG_TEXT), (x, y))

    def draw_debug_overlay(self, lines: list[str], x_offset: int = 0) -> None:
        p = 6; lh = c.DEBUG_FONT_SIZE + 2; bw = 320
        bh = p*2 + lh*len(lines)
        ov = pygame.Surface((bw, bh), pygame.SRCALPHA); ov.fill((*c.COLOR_DEBUG_BG, 150))
        self.surface.blit(ov, (8+x_offset, 8))
        for i, line in enumerate(lines):
            self.draw_text(line, 8+x_offset+p, 8+p+i*lh)
