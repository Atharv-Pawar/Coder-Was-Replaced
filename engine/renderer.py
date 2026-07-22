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

    # ── Employee rendering ────────────────────────────────────────────────────
    def draw_employees(self, manager, camera) -> None:
        """Draw all employee robots on the map (inside world-draw clip)."""
        if manager is None:
            return
        ts = c.TILE_SIZE
        for emp in manager.employees:
            wx, wy = emp.robot.world_pixel_pos
            sx, sy = camera.world_to_screen(wx + 3, wy + 3)
            size = ts - 6
            rect = pygame.Rect(int(sx), int(sy), size, size)
            pygame.draw.rect(self.surface, emp.tier.color, rect, border_radius=4)
            pygame.draw.rect(self.surface, emp.tier.outline, rect, width=2, border_radius=4)
            cx, cy2 = rect.center
            dx, dy  = emp.robot.facing
            tip   = (cx + dx*size*0.38,  cy2 + dy*size*0.38)
            left  = (cx - dy*size*0.18 - dx*size*0.08, cy2 + dx*size*0.18 - dy*size*0.08)
            right = (cx + dy*size*0.18 - dx*size*0.08, cy2 - dx*size*0.18 - dy*size*0.08)
            pygame.draw.polygon(self.surface, emp.tier.outline, [tip, left, right])
            ls = self.debug_font.render(emp.tier.label, True, (255, 255, 255))
            self.surface.blit(ls, (rect.x + 2, rect.y + 1))

    def draw_employee_hud(self, manager) -> None:
        """Compact status strip in the top-left of the game panel."""
        if manager is None or manager.count == 0:
            return
        gx  = c.GAME_VIEWPORT_X + c.EMPLOYEE_HUD_X
        gy  = c.EMPLOYEE_HUD_Y
        lh  = c.EMPLOYEE_HUD_ROW_H
        pad = 6
        bw  = 220
        bh  = pad + lh * manager.count + pad

        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg.fill((16, 18, 26, 210))
        self.surface.blit(bg, (gx, gy))
        pygame.draw.rect(self.surface, (50, 60, 90),
                         pygame.Rect(gx, gy, bw, bh), width=1, border_radius=4)

        for i, emp in enumerate(manager.employees):
            y = gy + pad + i * lh
            pygame.draw.circle(self.surface, emp.tier.color, (gx + pad + 5, y + lh//2), 5)
            sc = (c.COLOR_HIRE_STATUS_RUN if emp.status == "running"
                  else c.COLOR_HIRE_STATUS_ERR if emp.status == "error"
                  else c.COLOR_HIRE_STATUS_IDLE)
            ns = self.debug_font.render(f"{emp.tier.title}  [{emp.status}]", True, sc)
            self.surface.blit(ns, (gx + pad + 14, y + (lh - ns.get_height())//2))

    def draw_hire_panel(self, manager, economy, progression) -> None:
        """Full-screen hire overlay ([H] key)."""
        from game.employees import TIERS
        dim = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        self.surface.blit(dim, (0, 0))

        ih = 72; header_h = 60; footer_h = 30
        pw = 580; ph = header_h + ih * len(TIERS) + footer_h + 10
        px = (c.SCREEN_WIDTH - pw) // 2
        py = max(20, (c.SCREEN_HEIGHT - ph) // 2)

        bg = pygame.Surface((pw, ph), pygame.SRCALPHA); bg.fill((*c.COLOR_HIRE_BG, 245))
        self.surface.blit(bg, (px, py))
        pygame.draw.rect(self.surface, c.COLOR_HIRE_BORDER,
                         pygame.Rect(px, py, pw, ph), width=2, border_radius=8)

        ts2 = self.debug_font.render("HIRE STAFF", True, c.COLOR_HIRE_TITLE)
        self.surface.blit(ts2, (px + 14, py + 10))
        bs = self.debug_font.render(
            f"Balance: ${economy.salary}  |  Staff: {manager.count}/{c.MAX_EMPLOYEES}",
            True, c.COLOR_HIRE_COST)
        self.surface.blit(bs, (px + pw - bs.get_width() - 14, py + 10))
        hs = self.debug_font.render("[H] close   [1-4] hire", True, (100, 110, 140))
        self.surface.blit(hs, (px + (pw - hs.get_width())//2, py + 32))
        pygame.draw.line(self.surface, c.COLOR_HIRE_BORDER,
                         (px, py + header_h - 2), (px + pw, py + header_h - 2))

        cbt   = manager.count_by_tier
        avail = {t.tier_id for t in manager.available_tiers()}

        for i, tier in enumerate(TIERS):
            iy     = py + header_h + i * ih
            owned  = cbt.get(tier.tier_id, 0)
            locked = tier.tier_id not in avail
            full   = manager.count >= c.MAX_EMPLOYEES
            afford = economy.salary >= tier.cost and not locked and not full

            rbg = pygame.Surface((pw - 4, ih - 4), pygame.SRCALPHA)
            rbg.fill((*c.COLOR_HIRE_ITEM_BG, 200))
            self.surface.blit(rbg, (px + 2, iy + 2))

            sw_y = iy + (ih - 30)//2
            pygame.draw.rect(self.surface, tier.color,   pygame.Rect(px+10, sw_y, 24, 30), border_radius=4)
            pygame.draw.rect(self.surface, tier.outline, pygame.Rect(px+10, sw_y, 24, 30), width=2, border_radius=4)
            lbl = self.debug_font.render(tier.label, True, (255,255,255))
            self.surface.blit(lbl, (px+10+(24-lbl.get_width())//2, sw_y+(30-lbl.get_height())//2))

            kc = (100,110,130) if locked else (180,190,210)
            self.surface.blit(self.debug_font.render(f"[{i+1}]", True, kc), (px+40, iy+10))

            tc = c.COLOR_HIRE_LOCKED if locked else (200,215,240)
            self.surface.blit(self.debug_font.render(tier.title,   True, tc),           (px+70, iy+8))
            self.surface.blit(self.debug_font.render(tier.tagline, True, (120,130,155)),(px+70, iy+28))
            if owned:
                os2 = self.debug_font.render(f"Hired: {owned}", True, c.COLOR_HIRE_OWNED)
                self.surface.blit(os2, (px+70, iy+48))

            right_x = px + pw - 14
            if locked:
                from game.progression import LEVELS
                need = LEVELS[tier.min_level].title if tier.min_level < len(LEVELS) else "???"
                rs2 = self.debug_font.render(f"Needs: {need}", True, c.COLOR_HIRE_LOCKED)
                self.surface.blit(rs2, (right_x - rs2.get_width(), iy + ih//2 - 8))
            elif full:
                fs2 = self.debug_font.render("Office full", True, c.COLOR_HIRE_LOCKED)
                self.surface.blit(fs2, (right_x - fs2.get_width(), iy + ih//2 - 8))
            else:
                cc2 = c.COLOR_HIRE_AFFORD if afford else c.COLOR_HIRE_CANT
                cs2 = self.debug_font.render(f"${tier.cost}", True, cc2)
                self.surface.blit(cs2, (right_x - cs2.get_width(), iy + ih//2 - 8))

        fy2  = py + header_h + ih * len(TIERS) + 6
        foot = self.debug_font.render(
            "Employees run automatically and share XP, salary, and missions.",
            True, (90, 100, 130))
        self.surface.blit(foot, (px + (pw - foot.get_width())//2, fy2))

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

    def draw_achievement_popup(self, achievement_system) -> None:
        """Slide-in banner at top of game panel for newly unlocked achievements."""
        if not achievement_system or not achievement_system.popups:
            return

        popup = achievement_system.popups[0]
        alpha = int(255 * popup.alpha)
        if alpha <= 0:
            return

        gx  = c.GAME_VIEWPORT_X
        pw  = 300
        ph  = 62
        px  = gx + c.GAME_VIEWPORT_W - pw - 10
        py  = 10

        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg.fill((*c.COLOR_ACH_BG, min(230, alpha)))
        self.surface.blit(bg, (px, py))
        pygame.draw.rect(self.surface, c.COLOR_ACH_BORDER,
                         pygame.Rect(px, py, pw, ph), width=2, border_radius=6)

        # Label
        lbl = self.debug_font.render("ACHIEVEMENT UNLOCKED", True, c.COLOR_ACH_LABEL)
        lbl.set_alpha(alpha)
        self.surface.blit(lbl, (px + 8, py + 6))

        # Title
        tf = pygame.font.SysFont("consolas,courier,monospace", 17)
        ts = tf.render(popup.achievement.title, True, c.COLOR_ACH_TITLE)
        ts.set_alpha(alpha)
        self.surface.blit(ts, (px + 8, py + 24))

        # Description
        ds = self.debug_font.render(popup.achievement.description, True, c.COLOR_ACH_DESC)
        ds.set_alpha(alpha)
        self.surface.blit(ds, (px + 8, py + 44))

    def draw_settings_overlay(self, settings, save_manager) -> None:
        """Centered settings panel (S / F9 key)."""
        dim = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        self.surface.blit(dim, (0, 0))

        pw, ph = 480, 340
        px = (c.SCREEN_WIDTH - pw) // 2
        py = (c.SCREEN_HEIGHT - ph) // 2

        bg = pygame.Surface((pw, ph), pygame.SRCALPHA)
        bg.fill((*c.COLOR_SETTINGS_BG, 245))
        self.surface.blit(bg, (px, py))
        pygame.draw.rect(self.surface, c.COLOR_SETTINGS_BORDER,
                         pygame.Rect(px, py, pw, ph), width=2, border_radius=8)

        lh  = 28
        pad = 16

        def _row(label, value, hint, y):
            self.surface.blit(
                self.debug_font.render(label, True, c.COLOR_SETTINGS_LABEL),
                (px + pad, y))
            self.surface.blit(
                self.debug_font.render(str(value), True, c.COLOR_SETTINGS_VALUE),
                (px + 200, y))
            self.surface.blit(
                self.debug_font.render(hint, True, c.COLOR_SETTINGS_HINT),
                (px + 280, y))

        def _bar(ratio, y):
            bx, bw, bh = px + pad, pw - pad * 2, 8
            pygame.draw.rect(self.surface, c.COLOR_SETTINGS_BAR_BG,
                             pygame.Rect(bx, y, bw, bh), border_radius=4)
            fw = max(0, int(bw * ratio))
            if fw:
                pygame.draw.rect(self.surface, c.COLOR_SETTINGS_BAR_FILL,
                                 pygame.Rect(bx, y, fw, bh), border_radius=4)

        # Title
        tf = pygame.font.SysFont("consolas,courier,monospace", 20)
        ts = tf.render("SETTINGS", True, c.COLOR_SETTINGS_TITLE)
        self.surface.blit(ts, (px + (pw - ts.get_width()) // 2, py + pad))
        hs = self.debug_font.render("[S / F9] close   [F2] quick-save", True, c.COLOR_SETTINGS_HINT)
        self.surface.blit(hs, (px + (pw - hs.get_width()) // 2, py + pad + 24))
        pygame.draw.line(self.surface, c.COLOR_SETTINGS_BORDER,
                         (px, py + 60), (px + pw, py + 60))

        cy = py + 70
        _row("Master Volume", f"{int(settings.master_volume * 100)}%", "[Z] − / [X] +", cy)
        cy += 10; _bar(settings.master_volume, cy); cy += lh

        _row("SFX Volume",    f"{int(settings.sfx_volume * 100)}%",    "[C] − / [V] +", cy)
        cy += 10; _bar(settings.sfx_volume, cy); cy += lh

        pygame.draw.line(self.surface, c.COLOR_SETTINGS_BORDER,
                         (px, cy), (px + pw, cy)); cy += 10

        _row("Fullscreen",    "ON" if settings.fullscreen else "OFF",  "[F11] toggle",    cy); cy += lh
        _row("Debug Overlay", "ON" if settings.show_debug  else "OFF", "[F3] toggle",     cy); cy += lh

        pygame.draw.line(self.surface, c.COLOR_SETTINGS_BORDER,
                         (px, cy), (px + pw, cy)); cy += 10

        # Save / load info
        last = save_manager.last_save_str if save_manager else "never"
        _row("Auto-save",  "every 30s", "[F2] save now", cy); cy += lh
        _row("Last saved", last, "", cy); cy += lh

        pygame.draw.line(self.surface, c.COLOR_SETTINGS_BORDER,
                         (px, cy), (px + pw, cy)); cy += 10

        # Achievement progress
        if hasattr(self, '_ach_count'):
            pass
        info = self.debug_font.render(
            "Close with [S] or [F9]  —  ESC exits the game",
            True, c.COLOR_SETTINGS_HINT)
        self.surface.blit(info, (px + (pw - info.get_width()) // 2, py + ph - 28))

    # ── Floor transition overlay ──────────────────────────────────────────────
    def draw_floor_transition(self, floor_manager) -> None:
        """Full-screen fade overlay shown when advancing floors."""
        if floor_manager is None or not floor_manager.transition_active:
            return
        alpha = int(220 * floor_manager.transition_alpha)
        if alpha <= 0:
            return

        ov = pygame.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((*c.COLOR_FLOOR_TRANSITION_BG, min(210, alpha)))
        self.surface.blit(ov, (0, 0))

        big_font = pygame.font.SysFont("consolas,courier,monospace", 28)
        floor_num = floor_manager.current_floor
        title = big_font.render(
            f"FLOOR  {floor_num}", True, c.COLOR_FLOOR_TRANSITION_TEXT)
        title.set_alpha(alpha)
        tx = (c.SCREEN_WIDTH - title.get_width()) // 2
        ty = c.SCREEN_HEIGHT // 2 - 40
        self.surface.blit(title, (tx, ty))

        name_s = big_font.render(
            floor_manager.transition_name, True, c.COLOR_FLOOR_TRANSITION_TEXT)
        name_s.set_alpha(alpha)
        self.surface.blit(name_s, ((c.SCREEN_WIDTH - name_s.get_width()) // 2, ty + 44))

        from game.procgen import get_config
        cfg   = get_config(floor_num)
        size_s = self.debug_font.render(
            f"{cfg['width']} x {cfg['height']} tiles", True, c.COLOR_FLOOR_TRANSITION_SUB)
        size_s.set_alpha(alpha)
        self.surface.blit(size_s, ((c.SCREEN_WIDTH - size_s.get_width()) // 2, ty + 90))

    def draw_floor_hud(self, floor_manager) -> None:
        """Small floor indicator in the bottom-left of the game panel."""
        if floor_manager is None:
            return
        gx = c.GAME_VIEWPORT_X + 8
        gy = c.SCREEN_HEIGHT - 28

        fn = floor_manager.current_floor
        from game.procgen import floor_name
        text = f"Floor {fn}: {floor_name(fn)}"

        if floor_manager.can_advance():
            text += "  [N] Next Floor"
            col = c.COLOR_FLOOR_ADVANCE_HINT
        else:
            nxt = floor_manager.next_floor_unlock_title
            if nxt:
                text += f"  (Next: {nxt})"
            col = c.COLOR_FLOOR_TRANSITION_SUB

        bg = pygame.Surface((len(text) * 8 + 16, 20), pygame.SRCALPHA)
        bg.fill((10, 12, 20, 180))
        self.surface.blit(bg, (gx - 4, gy - 2))
        self.surface.blit(self.debug_font.render(text, True, col), (gx, gy))

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
