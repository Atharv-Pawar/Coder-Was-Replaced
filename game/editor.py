"""Split-screen code editor — Phases 3-5."""
from __future__ import annotations
import re
import pygame
from engine import constants as c

# ── Syntax highlighting ───────────────────────────────────────────────────────
_KW   = "for while if elif else def return in and or not True False None break continue pass"
_EFN  = "move turn_left turn_right look fix_bug drink_coffee commit deploy run_tests answer_email refactor scan spawn_worker use_ai docker_build optimize train_model kubernetes_scale"
_CONS = "EMPTY WALL BUG COFFEE DESK SERVER JIRA GIT WIFI MEETING LAPTOP"
_BLT  = "range len list tuple dict set int float str bool abs min max print type enumerate zip reversed sorted"

_TOKEN_RE = re.compile(
    r"(?P<comment>#[^\n]*)"
    r"|(?P<string>\"[^\"]*\"|\'[^\']*\')"
    r"|(?P<keyword>\b(?:" + "|".join(_KW.split())   + r")\b)"
    r"|(?P<engine>\b(?:"  + "|".join(_EFN.split())  + r")\b)"
    r"|(?P<constant>\b(?:"+ "|".join(_CONS.split()) + r")\b)"
    r"|(?P<builtin>\b(?:"  + "|".join(_BLT.split()) + r")\b)"
    r"|(?P<number>\b\d+\.?\d*\b)"
)
_TCOLORS = {"comment":c.COLOR_SYN_COMMENT,"string":c.COLOR_SYN_STRING,
            "keyword":c.COLOR_SYN_KEYWORD,"engine":c.COLOR_SYN_ENGINE_FN,
            "constant":c.COLOR_SYN_CONSTANT,"builtin":c.COLOR_SYN_BUILTIN,
            "number":c.COLOR_SYN_NUMBER}

def _tokenize(line: str):
    result, last = [], 0
    for m in _TOKEN_RE.finditer(line):
        if m.start() > last:
            result.append((line[last:m.start()], c.COLOR_SYN_DEFAULT))
        result.append((m.group(), _TCOLORS[m.lastgroup]))
        last = m.end()
    if last < len(line):
        result.append((line[last:], c.COLOR_SYN_DEFAULT))
    return result or [(line, c.COLOR_SYN_DEFAULT)]


DEFAULT_SCRIPT = """\
# Welcome to Coder Was Replaced!
# Write Python — the robot executes it live.
# Move manually with arrow keys / WASD.
# Press [Run] or F5 to execute your script.
# Press [TAB] to open the shop.
#
# API: move()  turn_left()  turn_right()  look()
#      fix_bug()  drink_coffee()  commit()  deploy()
#      run_tests()  answer_email()  refactor()
# Constants: BUG  COFFEE  WALL  SERVER  GIT  JIRA  EMPTY

while True:
    if look() == BUG:
        fix_bug()
    elif look() == COFFEE:
        drink_coffee()
    elif look() == WALL:
        turn_right()
    else:
        move()
"""


class Button:
    def __init__(self, x, y, w, h, label, color_n, color_h):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.color_n, self.color_h = color_n, color_h
        self._hov = False

    def update(self, mp): self._hov = self.rect.collidepoint(mp)
    def is_clicked(self, ev): return ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos)

    def draw(self, surf, font, enabled=True):
        col = (self.color_h if self._hov else self.color_n) if enabled else c.COLOR_BTN_INACTIVE
        pygame.draw.rect(surf, col, self.rect, border_radius=5)
        pygame.draw.rect(surf, (0,0,0), self.rect, width=1, border_radius=5)
        ls = font.render(self.label, True, c.COLOR_BTN_TEXT if enabled else (130,130,140))
        surf.blit(ls, ls.get_rect(center=self.rect.center))


class Editor:
    W   = c.EDITOR_PANEL_WIDTH
    TOP = c.EDITOR_TOP_BAR_HEIGHT
    BOT = c.EDITOR_STATUS_BAR_HEIGHT
    LNW = c.EDITOR_LINE_NUM_WIDTH
    LH  = c.EDITOR_LINE_HEIGHT

    def __init__(self):
        self.font  = pygame.font.SysFont("consolas,couriernew,courier,monospace", c.EDITOR_FONT_SIZE) \
                     or pygame.font.Font(None, c.EDITOR_FONT_SIZE + 2)
        self.sfont = pygame.font.SysFont("consolas,courier,monospace", 13)
        self.tfont = pygame.font.SysFont("segoeui,arial,sans", 14)
        self.char_w = self.font.size("M")[0]

        self.lines: list[str] = DEFAULT_SCRIPT.rstrip("\n").split("\n")
        self.cursor_row = len(self.lines)
        self.cursor_col = 0
        self.scroll = 0
        self._blink = 0.0; self._cur_vis = True

        by = (self.TOP - 26) // 2
        self.btn_run  = Button(8,   by, 96, 26, "Run  [F5]",  c.COLOR_BTN_RUN,  c.COLOR_BTN_RUN_HOVER)
        self.btn_stop = Button(112, by, 96, 26, "Stop [F6]",  c.COLOR_BTN_STOP, c.COLOR_BTN_STOP_HOVER)
        self.btn_sl   = Button(228, by+2, 22, 22, "<", c.COLOR_EDITOR_GUTTER, (60,64,80))
        self.btn_fa   = Button(290, by+2, 22, 22, ">", c.COLOR_EDITOR_GUTTER, (60,64,80))
        self._speeds  = [0.8, 0.4, 0.0, -0.05]
        self._slabels = ["0.5x","0.75x","1x","2x"]
        self._sidx    = 2

    @property
    def _code_h(self):
        return c.SCREEN_HEIGHT - self.TOP - self.BOT - c.PROGRESS_PANEL_HEIGHT - c.ECONOMY_PANEL_HEIGHT

    @property
    def _code_y(self): return self.TOP

    @property
    def _vis_lines(self): return self._code_h // self.LH

    def get_code(self): return "\n".join(self.lines)

    # ── Events ────────────────────────────────────────────────────────────────
    def handle_event(self, ev, running: bool) -> str | None:
        if ev.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            mp = pygame.mouse.get_pos()
            for b in (self.btn_run, self.btn_stop, self.btn_sl, self.btn_fa):
                b.update(mp)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.btn_run.is_clicked(ev)  and not running: return "run"
            if self.btn_stop.is_clicked(ev) and running:     return "stop"
            if self.btn_sl.is_clicked(ev):  self._sidx = max(0, self._sidx - 1)
            if self.btn_fa.is_clicked(ev):  self._sidx = min(len(self._speeds)-1, self._sidx+1)
            self._click(ev.pos)
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_F5 and not running: return "run"
            if ev.key == pygame.K_F6 and running:     return "stop"
            if not running: self._key(ev)
        if ev.type == pygame.TEXTINPUT and not running:
            self._insert(ev.text)
        return None

    def update(self, dt, engine=None, progression=None):
        self._blink += dt
        if self._blink >= 0.5:
            self._blink = 0.0; self._cur_vis = not self._cur_vis
        if engine and engine.current_line >= 0:
            self._scroll_to(engine.current_line)
        if engine:
            engine.set_step_delay(max(0.0, self._speeds[self._sidx]))

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surf, engine=None, progression=None, economy=None):
        pygame.draw.rect(surf, c.COLOR_EDITOR_BG, pygame.Rect(0, 0, self.W, c.SCREEN_HEIGHT))
        self._draw_topbar(surf, engine)
        self._draw_code(surf, engine)
        self._draw_progress(surf, progression)
        self._draw_economy(surf, economy)
        self._draw_status(surf, engine)
        pygame.draw.line(surf, c.COLOR_EDITOR_PANEL_BORDER, (self.W-1, 0), (self.W-1, c.SCREEN_HEIGHT), 2)

    def _draw_topbar(self, surf, engine):
        pygame.draw.rect(surf, c.COLOR_EDITOR_GUTTER, pygame.Rect(0, 0, self.W, self.TOP))
        pygame.draw.line(surf, c.COLOR_EDITOR_PANEL_BORDER, (0, self.TOP-1), (self.W, self.TOP-1))
        ts = self.tfont.render("SCRIPT EDITOR", True, (160,170,200))
        surf.blit(ts, (self.W - ts.get_width() - 8, (self.TOP - ts.get_height())//2))
        running = engine and engine.is_running
        self.btn_run.draw(surf, self.font, not running)
        self.btn_stop.draw(surf, self.font, running)
        self.btn_sl.draw(surf, self.font)
        sl = self.sfont.render(self._slabels[self._sidx], True, (180,190,210))
        surf.blit(sl, (254, (self.TOP - sl.get_height())//2))
        self.btn_fa.draw(surf, self.font)

    def _draw_code(self, surf, engine):
        exec_line = engine.current_line if (engine and engine.is_running) else -1
        for ri in range(self._vis_lines + 1):
            li = self.scroll + ri
            y  = self._code_y + ri * self.LH
            pygame.draw.rect(surf, c.COLOR_EDITOR_GUTTER, pygame.Rect(0, y, self.LNW, self.LH))
            if li >= len(self.lines): break
            if li == exec_line:
                pygame.draw.rect(surf, c.COLOR_EDITOR_ACTIVE_LINE, pygame.Rect(0, y, self.W, self.LH))
            elif li == self.cursor_row:
                pygame.draw.rect(surf, c.COLOR_EDITOR_CURSOR_LINE, pygame.Rect(self.LNW, y, self.W - self.LNW, self.LH))
            nc = c.COLOR_SYN_ENGINE_FN if li == exec_line else c.COLOR_EDITOR_GUTTER_TEXT
            ns = self.font.render(str(li+1), True, nc)
            surf.blit(ns, (self.LNW - ns.get_width() - 4, y + (self.LH - ns.get_height())//2))
            tx, ty = self.LNW + 4, y + (self.LH - self.font.get_height())//2
            for text, col in _tokenize(self.lines[li]):
                if not text: continue
                sg = self.font.render(text, True, col)
                surf.blit(sg, (tx, ty)); tx += sg.get_width()
                if tx >= self.W - 4: break
        pygame.draw.line(surf, c.COLOR_EDITOR_PANEL_BORDER, (self.LNW-1, self._code_y), (self.LNW-1, self._code_y + self._code_h))
        if not (engine and engine.is_running) and self._cur_vis:
            self._draw_cursor(surf)

    def _draw_cursor(self, surf):
        if self.cursor_row < self.scroll: return
        rel = self.cursor_row - self.scroll
        if rel >= self._vis_lines: return
        y    = self._code_y + rel * self.LH
        line = self.lines[self.cursor_row] if self.cursor_row < len(self.lines) else ""
        x    = self.LNW + 4 + self.font.size(line[:self.cursor_col])[0]
        pygame.draw.line(surf, c.COLOR_EDITOR_CURSOR, (x, y+2), (x, y+self.LH-3), 2)

    def _draw_progress(self, surf, progression):
        py = self._code_y + self._code_h
        ph = c.PROGRESS_PANEL_HEIGHT
        pygame.draw.rect(surf, c.COLOR_EDITOR_GUTTER, pygame.Rect(0, py, self.W, ph))
        pygame.draw.line(surf, c.COLOR_PROGRESS_DIVIDER, (0, py), (self.W, py), 1)
        if not progression: return
        p = 8; cy = py + 7
        ls = self.font.render(f">> {progression.level.title}", True, c.COLOR_LEVEL_TEXT)
        surf.blit(ls, (p, cy))
        nxt = progression.next_unlock
        xt  = f"XP: {progression.xp}" + (f" / {nxt.xp_required}" if nxt else "")
        xs  = self.sfont.render(xt, True, c.COLOR_LEVEL_XP_TEXT)
        surf.blit(xs, (self.W - xs.get_width() - p, cy+1))
        by  = cy + self.LH + 2; bw = self.W - p*2
        pygame.draw.rect(surf, c.COLOR_XP_BAR_BG, pygame.Rect(p, by, bw, 9), border_radius=4)
        fw = max(0, int(bw * progression.xp_progress_ratio))
        if fw:
            fc = c.COLOR_XP_BAR_FILL2 if progression.xp_progress_ratio > 0.75 else c.COLOR_XP_BAR_FILL
            pygame.draw.rect(surf, fc, pygame.Rect(p, by, fw, 9), border_radius=4)
        hy = by + 13
        if nxt:
            hs = self.sfont.render(f"Next: {nxt.fn_name}()  --  {progression.xp_to_next_unlock} XP away", True, c.COLOR_NEXT_UNLOCK)
        else:
            hs = self.sfont.render("All functions unlocked!", True, c.COLOR_UNLOCKED_FN)
        surf.blit(hs, (p, hy))

    def _draw_economy(self, surf, economy):
        py = self._code_y + self._code_h + c.PROGRESS_PANEL_HEIGHT
        ph = c.ECONOMY_PANEL_HEIGHT
        pygame.draw.rect(surf, (20,22,30), pygame.Rect(0, py, self.W, ph))
        pygame.draw.line(surf, c.COLOR_PROGRESS_DIVIDER, (0, py), (self.W, py), 1)
        if not economy: return
        p = 8; cy = py + 7

        def _cur(label, val, col, x, y):
            ls = self.sfont.render(f"{label}: ", True, (140,145,160))
            vs = self.sfont.render(str(val), True, col)
            surf.blit(ls, (x, y)); surf.blit(vs, (x + ls.get_width(), y))
            return x + ls.get_width() + vs.get_width() + 10

        col = p
        col = _cur("$",    economy.salary,          c.COLOR_SALARY,   col, cy)
        col = _cur("Rep",  economy.reputation,       c.COLOR_REP,      col, cy)
        col = _cur("Stars",economy.git_stars,        c.COLOR_STARS,    col, cy)

        r2y = cy + self.LH + 1; col2 = p
        col2 = _cur("Coffee", economy.coffee_count,    c.COLOR_COFFEE_C, col2, r2y)
        col2 = _cur("CPU",    economy.compute_credits, c.COLOR_COMPUTE,  col2, r2y)

        tw = self.W - col2 - p - 4
        if tw > 20:
            pygame.draw.rect(surf, c.COLOR_XP_BAR_BG, pygame.Rect(col2, r2y+3, tw, 8), border_radius=3)
            fw2 = max(0, int(tw * economy.tick_progress))
            if fw2:
                pygame.draw.rect(surf, c.COLOR_SALARY, pygame.Rect(col2, r2y+3, fw2, 8), border_radius=3)
            ths = self.sfont.render("[TAB] Shop", True, (100,110,140))
            surf.blit(ths, (col2, r2y + 13))

    def _draw_status(self, surf, engine):
        by = c.SCREEN_HEIGHT - self.BOT
        pygame.draw.rect(surf, c.COLOR_EDITOR_STATUS_BG, pygame.Rect(0, by, self.W, self.BOT))
        pygame.draw.line(surf, c.COLOR_EDITOR_PANEL_BORDER, (0, by), (self.W, by))
        if not engine: return
        if engine.error:
            col, msg = c.COLOR_EDITOR_STATUS_ERR, engine.error
        elif engine.is_running:
            col = c.COLOR_EDITOR_STATUS_RUN
            msg = f"Running...  line {engine.current_line+1}" if engine.current_line >= 0 else "Running..."
        else:
            col = c.COLOR_EDITOR_STATUS_OK
            msg = f"Ready  |  Ln {self.cursor_row+1}, Col {self.cursor_col+1}"
        ss = self.sfont.render(msg, True, col)
        surf.blit(ss, (8, by + (self.BOT - ss.get_height())//2))

    # ── Text editing ──────────────────────────────────────────────────────────
    def _key(self, ev):
        ctrl = ev.mod & pygame.KMOD_CTRL
        k = ev.key
        if   k in (pygame.K_RETURN, pygame.K_KP_ENTER): self._enter()
        elif k == pygame.K_BACKSPACE:  self._backspace(ctrl)
        elif k == pygame.K_DELETE:     self._delete()
        elif k == pygame.K_TAB:        self._insert("    ")
        elif k == pygame.K_UP:         self._mv(-1, 0)
        elif k == pygame.K_DOWN:       self._mv(1, 0)
        elif k == pygame.K_LEFT:       self._mv(0, -1)
        elif k == pygame.K_RIGHT:      self._mv(0, 1)
        elif k == pygame.K_HOME:       self.cursor_col = 0
        elif k == pygame.K_END:        self.cursor_col = len(self._cl())
        elif k == pygame.K_PAGEUP:     self._mv(-self._vis_lines//2, 0)
        elif k == pygame.K_PAGEDOWN:   self._mv(self._vis_lines//2, 0)
        elif ctrl and k == pygame.K_a:
            self.cursor_row = len(self.lines)-1; self.cursor_col = len(self._cl())
        self._ensure_vis()

    def _enter(self):
        line = self._cl(); rest = line[self.cursor_col:]
        self.lines[self.cursor_row] = line[:self.cursor_col]
        self.cursor_row += 1
        prev = self.lines[self.cursor_row-1]
        indent = len(prev) - len(prev.lstrip())
        extra  = 4 if prev.rstrip().endswith(":") else 0
        self.cursor_col = indent + extra
        self.lines.insert(self.cursor_row, " " * self.cursor_col + rest)

    def _backspace(self, ctrl):
        if self.cursor_col > 0:
            line = self._cl()
            if ctrl:
                col = self.cursor_col
                while col > 0 and line[col-1] == " ": col -= 1
                while col > 0 and line[col-1] != " ": col -= 1
                self.lines[self.cursor_row] = line[:col] + line[self.cursor_col:]
                self.cursor_col = col
            else:
                self.lines[self.cursor_row] = line[:self.cursor_col-1] + line[self.cursor_col:]
                self.cursor_col -= 1
        elif self.cursor_row > 0:
            prev = self.lines[self.cursor_row-1]
            self.cursor_col = len(prev)
            self.lines[self.cursor_row-1] = prev + self._cl()
            self.lines.pop(self.cursor_row)
            self.cursor_row -= 1

    def _delete(self):
        line = self._cl()
        if self.cursor_col < len(line):
            self.lines[self.cursor_row] = line[:self.cursor_col] + line[self.cursor_col+1:]
        elif self.cursor_row < len(self.lines)-1:
            self.lines[self.cursor_row] = line + self.lines[self.cursor_row+1]
            self.lines.pop(self.cursor_row+1)

    def _insert(self, text):
        line = self._cl()
        self.lines[self.cursor_row] = line[:self.cursor_col] + text + line[self.cursor_col:]
        self.cursor_col += len(text)

    def _click(self, pos):
        mx, my = pos
        if mx >= self.W or my < self._code_y or my >= self._code_y + self._code_h: return
        row = min(self.scroll + (my - self._code_y)//self.LH, len(self.lines)-1)
        self.cursor_row = max(0, row)
        self.cursor_col = min(max(0, (mx-self.LNW-4)//max(1,self.char_w)), len(self._cl()))

    def _mv(self, dr, dc):
        if dr:
            self.cursor_row = max(0, min(len(self.lines)-1, self.cursor_row+dr))
            self.cursor_col = min(self.cursor_col, len(self._cl()))
        if dc:
            self.cursor_col += dc
            line = self._cl()
            if self.cursor_col < 0:
                if self.cursor_row > 0: self.cursor_row -= 1; self.cursor_col = len(self._cl())
                else: self.cursor_col = 0
            elif self.cursor_col > len(line):
                if self.cursor_row < len(self.lines)-1: self.cursor_row += 1; self.cursor_col = 0
                else: self.cursor_col = len(line)

    def _cl(self):
        if self.cursor_row >= len(self.lines): self.lines.append(""); return ""
        return self.lines[self.cursor_row]

    def _scroll_to(self, row):
        if row < self.scroll: self.scroll = row
        elif row >= self.scroll + self._vis_lines: self.scroll = row - self._vis_lines + 1

    def _ensure_vis(self): self._scroll_to(self.cursor_row)
