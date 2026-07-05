"""
Split-screen code editor drawn entirely in pygame.

Left panel:  EDITOR_PANEL_WIDTH px wide
  ┌─────────────────────┐
  │ SCRIPT EDITOR       │  ← top bar
  ├────────────────────-┤
  │ [Run F5] [Stop F6]  │  ← button row
  ├────────────────────-┤
  │ 1 │                 │
  │ 2 │ while True:     │  ← scrollable code area with syntax highlighting
  │ 3 │     move()      │
  │~~~│ ← current exec  │
  ├────────────────────-┤
  │ Status / error      │  ← status bar
  └─────────────────────┘

The editor is always visible. The game world renders in the right panel
(x = EDITOR_PANEL_WIDTH onward).
"""

from __future__ import annotations

import re
import pygame
from engine import constants as c


# ─── Syntax highlighting ────────────────────────────────────────────────────
_KEYWORDS = (
    "for while if elif else def return in and or not True False None "
    "break continue pass import from as class try except finally raise with"
)
_ENGINE_FNS = (
    "move turn_left turn_right look fix_bug drink_coffee commit deploy "
    "scan run_tests build_project refactor optimize parallel_execute "
    "spawn_worker use_ai train_model docker_build kubernetes_scale "
    "terraform_apply answer_email merge_pull_request charge_laptop navigate"
)
_CONSTANTS = "EMPTY WALL BUG COFFEE DESK SERVER JIRA GIT WIFI MEETING LAPTOP"
_BUILTINS = "range len list tuple dict set int float str bool abs min max print type enumerate zip reversed sorted"

_TOKEN_RE = re.compile(
    r"(?P<comment>#[^\n]*)"
    r"|(?P<string>\"[^\"]*\"|\'[^\']*\')"
    r"|(?P<keyword>\b(?:" + "|".join(_KEYWORDS.split()) + r")\b)"
    r"|(?P<engine>\b(?:" + "|".join(_ENGINE_FNS.split()) + r")\b)"
    r"|(?P<constant>\b(?:" + "|".join(_CONSTANTS.split()) + r")\b)"
    r"|(?P<builtin>\b(?:" + "|".join(_BUILTINS.split()) + r")\b)"
    r"|(?P<number>\b\d+\.?\d*\b)"
)

_TOKEN_COLORS = {
    "comment":  c.COLOR_SYN_COMMENT,
    "string":   c.COLOR_SYN_STRING,
    "keyword":  c.COLOR_SYN_KEYWORD,
    "engine":   c.COLOR_SYN_ENGINE_FN,
    "constant": c.COLOR_SYN_CONSTANT,
    "builtin":  c.COLOR_SYN_BUILTIN,
    "number":   c.COLOR_SYN_NUMBER,
}


def _tokenize(line: str) -> list[tuple[str, tuple]]:
    """Tokenize a source line into (text, color) pairs for rendering."""
    result: list[tuple[str, tuple]] = []
    last = 0
    for m in _TOKEN_RE.finditer(line):
        if m.start() > last:
            result.append((line[last:m.start()], c.COLOR_SYN_DEFAULT))
        result.append((m.group(), _TOKEN_COLORS[m.lastgroup]))
        last = m.end()
    if last < len(line):
        result.append((line[last:], c.COLOR_SYN_DEFAULT))
    return result or [(line, c.COLOR_SYN_DEFAULT)]


# ─── Default starter script shown when the game launches ────────────────────
DEFAULT_SCRIPT = """\
# Welcome to Coder Was Replaced!
# Write Python here. The robot executes it live.
# Arrow keys move the robot manually; [Run] runs your script.
#
# API reference:
#   move()          -- step forward one tile
#   turn_left()     -- rotate 90 deg left
#   turn_right()    -- rotate 90 deg right
#   look()          -- what's in front? (EMPTY/BUG/COFFEE/WALL/...)
#   fix_bug()       -- fix the bug you're facing
#   drink_coffee()  -- use the coffee machine you're facing
#   commit()        -- commit to the git repo you're facing

while True:
    if look() == BUG:
        fix_bug()
    elif look() == COFFEE:
        drink_coffee()
    move()
"""


class Button:
    """A simple click-target rectangle with hover state."""

    def __init__(self, x: int, y: int, w: int, h: int, label: str,
                 color_normal, color_hover, color_text=c.COLOR_BTN_TEXT):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.color_normal = color_normal
        self.color_hover = color_hover
        self.color_text = color_text
        self._hovered = False

    def update(self, mouse_pos: tuple[int, int]) -> None:
        self._hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font,
             enabled: bool = True) -> None:
        color = (self.color_hover if self._hovered else self.color_normal) if enabled else c.COLOR_BTN_INACTIVE
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, width=1, border_radius=5)
        label_surf = font.render(self.label, True, self.color_text if enabled else (130, 130, 140))
        surface.blit(label_surf, label_surf.get_rect(center=self.rect.center))


class Editor:
    """The split-screen code editor panel."""

    W = c.EDITOR_PANEL_WIDTH
    TOP = c.EDITOR_TOP_BAR_HEIGHT
    BOTTOM = c.EDITOR_STATUS_BAR_HEIGHT
    LNW = c.EDITOR_LINE_NUM_WIDTH
    LH = c.EDITOR_LINE_HEIGHT

    def __init__(self):
        self.font = pygame.font.SysFont("consolas,couriernew,courier,monospace", c.EDITOR_FONT_SIZE)
        # Ensure we get a monospace font; fall back to default if unavailable.
        if self.font is None:
            self.font = pygame.font.Font(None, c.EDITOR_FONT_SIZE + 2)

        self.char_w = self.font.size("M")[0]

        # Text buffer: list of strings, one per line.
        self.lines: list[str] = DEFAULT_SCRIPT.split("\n")
        if self.lines and self.lines[-1] == "":
            self.lines.pop()

        # Cursor position (0-indexed).
        self.cursor_row: int = len(self.lines)
        self.cursor_col: int = 0

        # Scroll offset (first visible line).
        self.scroll: int = 0

        # Cursor blink state.
        self._blink_timer: float = 0.0
        self._cursor_visible: bool = True

        # Buttons
        btn_y = (c.EDITOR_TOP_BAR_HEIGHT - 26) // 2
        self.btn_run = Button(8, btn_y, 96, 26, "Run  [F5]",
                              c.COLOR_BTN_RUN, c.COLOR_BTN_RUN_HOVER)
        self.btn_stop = Button(112, btn_y, 96, 26, "Stop [F6]",
                               c.COLOR_BTN_STOP, c.COLOR_BTN_STOP_HOVER)

        # Speed buttons (decrease/increase step delay).
        self.btn_slower = Button(228, btn_y + 2, 22, 22, "<",
                                 c.COLOR_EDITOR_GUTTER, (60, 64, 80))
        self.btn_faster = Button(290, btn_y + 2, 22, 22, ">",
                                 c.COLOR_EDITOR_GUTTER, (60, 64, 80))
        self._speed_index: int = 2  # index into _SPEEDS
        self._SPEEDS = [0.8, 0.4, 0.0, -0.05]  # step_delay values (negative = turbo)
        self._SPEED_LABELS = ["0.5x", "0.75x", "1x", "2x"]

        # Small title font.
        self.title_font = pygame.font.SysFont("segoeui,arial,sans", 14)
        self.status_font = pygame.font.SysFont("consolas,courier,monospace", 13)

    # ── visible code area geometry ─────────────────────────────────────────
    @property
    def _code_y(self) -> int:
        return self.TOP

    @property
    def _code_h(self) -> int:
        return c.SCREEN_HEIGHT - self.TOP - self.BOTTOM

    @property
    def _visible_lines(self) -> int:
        return self._code_h // self.LH

    # ── public interface ──────────────────────────────────────────────────
    def get_code(self) -> str:
        return "\n".join(self.lines)

    def handle_event(self, event: pygame.event.Event, engine_running: bool
                     ) -> str | None:
        """
        Processes one pygame event.
        Returns one of: 'run', 'stop', or None.
        """
        # Update hover state whenever mouse moves.
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
            mp = pygame.mouse.get_pos()
            self.btn_run.update(mp)
            self.btn_stop.update(mp)
            self.btn_slower.update(mp)
            self.btn_faster.update(mp)

        # Button clicks.
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_run.is_clicked(event) and not engine_running:
                return "run"
            if self.btn_stop.is_clicked(event) and engine_running:
                return "stop"
            if self.btn_slower.is_clicked(event):
                self._speed_index = max(0, self._speed_index - 1)
            if self.btn_faster.is_clicked(event):
                self._speed_index = min(len(self._SPEEDS) - 1, self._speed_index + 1)
            # Click in code area → set cursor.
            self._handle_click(event.pos)

        # Keyboard shortcuts.
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F5 and not engine_running:
                return "run"
            if event.key == pygame.K_F6 and engine_running:
                return "stop"
            if not engine_running:
                self._handle_key(event)

        # Unicode text input (printable characters, handles shift/compose etc.)
        if event.type == pygame.TEXTINPUT and not engine_running:
            self._insert_text(event.text)

        return None

    def update(self, dt: float, script_engine=None) -> None:
        self._blink_timer += dt
        if self._blink_timer >= 0.5:
            self._blink_timer = 0.0
            self._cursor_visible = not self._cursor_visible

        # Keep the currently executing line in view.
        if script_engine is not None and script_engine.current_line >= 0:
            self._scroll_to(script_engine.current_line)

        # Sync speed setting to the engine.
        if script_engine is not None:
            delay = self._SPEEDS[self._speed_index]
            script_engine.set_step_delay(max(0.0, delay))

    @property
    def step_speed_label(self) -> str:
        return self._SPEED_LABELS[self._speed_index]

    # ── rendering ─────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface, script_engine=None) -> None:
        # Background.
        pygame.draw.rect(surface, c.COLOR_EDITOR_BG,
                         pygame.Rect(0, 0, self.W, c.SCREEN_HEIGHT))

        self._draw_top_bar(surface, script_engine)
        self._draw_code_area(surface, script_engine)
        self._draw_status_bar(surface, script_engine)

        # Right border dividing editor from game.
        pygame.draw.line(surface, c.COLOR_EDITOR_PANEL_BORDER,
                         (self.W - 1, 0), (self.W - 1, c.SCREEN_HEIGHT), 2)

    def _draw_top_bar(self, surface: pygame.Surface, engine) -> None:
        pygame.draw.rect(surface, c.COLOR_EDITOR_GUTTER,
                         pygame.Rect(0, 0, self.W, self.TOP))
        pygame.draw.line(surface, c.COLOR_EDITOR_PANEL_BORDER,
                         (0, self.TOP - 1), (self.W, self.TOP - 1))

        title = self.title_font.render("SCRIPT EDITOR", True, (160, 170, 200))
        surface.blit(title, (self.W - title.get_width() - 8,
                              (self.TOP - title.get_height()) // 2))

        running = engine is not None and engine.is_running
        self.btn_run.draw(surface, self.font, enabled=not running)
        self.btn_stop.draw(surface, self.font, enabled=running)

        # Speed control.
        self.btn_slower.draw(surface, self.font, enabled=True)
        speed_label = self.status_font.render(
            self.step_speed_label, True, (180, 190, 210))
        surface.blit(speed_label, (254, (self.TOP - speed_label.get_height()) // 2))
        self.btn_faster.draw(surface, self.font, enabled=True)

    def _draw_code_area(self, surface: pygame.Surface, engine) -> None:
        exec_line = engine.current_line if (engine and engine.is_running) else -1

        for rel_idx in range(self._visible_lines + 1):
            line_idx = self.scroll + rel_idx
            y = self._code_y + rel_idx * self.LH

            # Gutter background.
            pygame.draw.rect(surface, c.COLOR_EDITOR_GUTTER,
                             pygame.Rect(0, y, self.LNW, self.LH))

            if line_idx >= len(self.lines):
                break

            # Active-execution line highlight.
            if line_idx == exec_line:
                pygame.draw.rect(surface, c.COLOR_EDITOR_ACTIVE_LINE,
                                 pygame.Rect(0, y, self.W, self.LH))
            # Cursor line highlight.
            elif line_idx == self.cursor_row:
                pygame.draw.rect(surface, c.COLOR_EDITOR_CURSOR_LINE,
                                 pygame.Rect(self.LNW, y, self.W - self.LNW, self.LH))

            # Line number.
            num_surf = self.font.render(str(line_idx + 1), True,
                                        c.COLOR_SYN_ENGINE_FN if line_idx == exec_line
                                        else c.COLOR_EDITOR_GUTTER_TEXT)
            surface.blit(num_surf, (self.LNW - num_surf.get_width() - 4,
                                    y + (self.LH - num_surf.get_height()) // 2))

            # Syntax-highlighted line text.
            tokens = _tokenize(self.lines[line_idx])
            tx = self.LNW + 4
            ty = y + (self.LH - self.font.get_height()) // 2
            for text, color in tokens:
                if not text:
                    continue
                seg = self.font.render(text, True, color)
                surface.blit(seg, (tx, ty))
                tx += seg.get_width()
                if tx >= self.W - 4:
                    break  # clip

        # Gutter separator line.
        pygame.draw.line(surface, c.COLOR_EDITOR_PANEL_BORDER,
                         (self.LNW - 1, self._code_y),
                         (self.LNW - 1, self._code_y + self._code_h))

        # Blinking cursor (only when not running).
        if engine is None or not engine.is_running:
            if self._cursor_visible:
                self._draw_cursor(surface)

    def _draw_cursor(self, surface: pygame.Surface) -> None:
        if self.cursor_row < self.scroll:
            return
        rel = self.cursor_row - self.scroll
        if rel >= self._visible_lines:
            return
        y = self._code_y + rel * self.LH
        line = self.lines[self.cursor_row] if self.cursor_row < len(self.lines) else ""
        col = min(self.cursor_col, len(line))
        text_before = line[:col]
        x = self.LNW + 4 + self.font.size(text_before)[0]
        pygame.draw.line(surface, c.COLOR_EDITOR_CURSOR,
                         (x, y + 2), (x, y + self.LH - 3), 2)

    def _draw_status_bar(self, surface: pygame.Surface, engine) -> None:
        bar_y = c.SCREEN_HEIGHT - self.BOTTOM
        pygame.draw.rect(surface, c.COLOR_EDITOR_STATUS_BG,
                         pygame.Rect(0, bar_y, self.W, self.BOTTOM))
        pygame.draw.line(surface, c.COLOR_EDITOR_PANEL_BORDER,
                         (0, bar_y), (self.W, bar_y))

        if engine is None:
            return

        if engine.error:
            color = c.COLOR_EDITOR_STATUS_ERR
            msg = engine.error
        elif engine.is_running:
            color = c.COLOR_EDITOR_STATUS_RUN
            line_disp = engine.current_line + 1 if engine.current_line >= 0 else "?"
            msg = f"Running...  line {line_disp}"
        else:
            color = c.COLOR_EDITOR_STATUS_OK
            msg = f"Ready  |  Ln {self.cursor_row + 1}, Col {self.cursor_col + 1}"

        status_surf = self.status_font.render(msg, True, color)
        surface.blit(status_surf, (8, bar_y + (self.BOTTOM - status_surf.get_height()) // 2))

    # ── text editing ──────────────────────────────────────────────────────
    def _handle_key(self, event: pygame.event.Event) -> None:
        ctrl = event.mod & pygame.KMOD_CTRL
        key = event.key

        if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            self._key_enter()
        elif key == pygame.K_BACKSPACE:
            self._key_backspace(ctrl)
        elif key == pygame.K_DELETE:
            self._key_delete()
        elif key == pygame.K_TAB:
            self._insert_text("    ")
        elif key == pygame.K_UP:
            self._move_cursor(-1, 0)
        elif key == pygame.K_DOWN:
            self._move_cursor(1, 0)
        elif key == pygame.K_LEFT:
            self._move_cursor(0, -1)
        elif key == pygame.K_RIGHT:
            self._move_cursor(0, 1)
        elif key == pygame.K_HOME:
            self.cursor_col = 0
        elif key == pygame.K_END:
            self.cursor_col = len(self._cur_line())
        elif key == pygame.K_PAGEUP:
            self._move_cursor(-self._visible_lines // 2, 0)
        elif key == pygame.K_PAGEDOWN:
            self._move_cursor(self._visible_lines // 2, 0)
        elif ctrl and key == pygame.K_a:
            # Select all — just jump cursor to end for now.
            self.cursor_row = len(self.lines) - 1
            self.cursor_col = len(self._cur_line())
        elif ctrl and key == pygame.K_z:
            pass  # Undo — Phase 9
        self._ensure_cursor_in_view()

    def _key_enter(self) -> None:
        line = self._cur_line()
        rest = line[self.cursor_col:]
        self.lines[self.cursor_row] = line[:self.cursor_col]
        self.cursor_row += 1
        self.lines.insert(self.cursor_row, rest)
        # Auto-indent: match leading whitespace of the previous line,
        # plus add 4 more spaces if the previous line ends in ':'.
        prev = self.lines[self.cursor_row - 1]
        indent = len(prev) - len(prev.lstrip())
        extra = 4 if prev.rstrip().endswith(":") else 0
        self.cursor_col = indent + extra
        self.lines[self.cursor_row] = " " * self.cursor_col + rest

    def _key_backspace(self, ctrl: bool) -> None:
        if self.cursor_col > 0:
            line = self._cur_line()
            if ctrl:
                # Delete to start of previous word.
                col = self.cursor_col
                while col > 0 and line[col - 1] == " ":
                    col -= 1
                while col > 0 and line[col - 1] != " ":
                    col -= 1
                self.lines[self.cursor_row] = line[:col] + line[self.cursor_col:]
                self.cursor_col = col
            else:
                self.lines[self.cursor_row] = line[:self.cursor_col - 1] + line[self.cursor_col:]
                self.cursor_col -= 1
        elif self.cursor_row > 0:
            prev = self.lines[self.cursor_row - 1]
            self.cursor_col = len(prev)
            self.lines[self.cursor_row - 1] = prev + self._cur_line()
            self.lines.pop(self.cursor_row)
            self.cursor_row -= 1

    def _key_delete(self) -> None:
        line = self._cur_line()
        if self.cursor_col < len(line):
            self.lines[self.cursor_row] = line[:self.cursor_col] + line[self.cursor_col + 1:]
        elif self.cursor_row < len(self.lines) - 1:
            self.lines[self.cursor_row] = line + self.lines[self.cursor_row + 1]
            self.lines.pop(self.cursor_row + 1)

    def _insert_text(self, text: str) -> None:
        line = self._cur_line()
        self.lines[self.cursor_row] = line[:self.cursor_col] + text + line[self.cursor_col:]
        self.cursor_col += len(text)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        mx, my = pos
        if mx >= self.W:
            return  # click is in the game area
        if my < self._code_y or my >= self._code_y + self._code_h:
            return
        rel = (my - self._code_y) // self.LH
        row = self.scroll + rel
        row = max(0, min(row, len(self.lines) - 1))
        line = self.lines[row]
        col_x = mx - self.LNW - 4
        col = max(0, col_x // max(1, self.char_w))
        self.cursor_row = row
        self.cursor_col = min(col, len(line))

    # ── helpers ───────────────────────────────────────────────────────────
    def _cur_line(self) -> str:
        if self.cursor_row < len(self.lines):
            return self.lines[self.cursor_row]
        self.lines.append("")
        return ""

    def _move_cursor(self, drow: int, dcol: int) -> None:
        if drow != 0:
            self.cursor_row = max(0, min(len(self.lines) - 1, self.cursor_row + drow))
            self.cursor_col = min(self.cursor_col, len(self._cur_line()))
        if dcol != 0:
            self.cursor_col += dcol
            line = self._cur_line()
            if self.cursor_col < 0:
                if self.cursor_row > 0:
                    self.cursor_row -= 1
                    self.cursor_col = len(self._cur_line())
                else:
                    self.cursor_col = 0
            elif self.cursor_col > len(line):
                if self.cursor_row < len(self.lines) - 1:
                    self.cursor_row += 1
                    self.cursor_col = 0
                else:
                    self.cursor_col = len(line)

    def _scroll_to(self, row: int) -> None:
        vis = self._visible_lines
        if row < self.scroll:
            self.scroll = row
        elif row >= self.scroll + vis:
            self.scroll = row - vis + 1

    def _ensure_cursor_in_view(self) -> None:
        self._scroll_to(self.cursor_row)
