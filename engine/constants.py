"""
Global constants for Coder Was Replaced.

Keeping every tunable value in one place makes it trivial to rebalance
the game later (Phase 5+) without hunting through the codebase.
"""

from __future__ import annotations

# ----------------------------------------------------------------------------
# Window / Display
# ----------------------------------------------------------------------------
WINDOW_TITLE = "Coder Was Replaced"

# Logical resolution the game is designed around. The renderer can scale
# this up to fill larger windows (handled by engine/renderer.py).
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Target framerate. The game loop uses a fixed timestep for logic so that
# gameplay (and later, script execution) stays deterministic regardless
# of rendering hiccups.
FPS = 60

# ----------------------------------------------------------------------------
# Tile / Grid
# ----------------------------------------------------------------------------
TILE_SIZE = 32  # pixels, matches the pixel-art spec in the design doc

# ----------------------------------------------------------------------------
# Colors (used by the Phase 1 placeholder tileset)
# ----------------------------------------------------------------------------
COLOR_BG = (18, 18, 24)
COLOR_FLOOR = (46, 52, 64)
COLOR_FLOOR_ALT = (51, 58, 71)
COLOR_WALL = (28, 30, 38)
COLOR_DESK = (96, 70, 48)
COLOR_GRID = (60, 64, 76)
COLOR_DEBUG_TEXT = (120, 220, 120)
COLOR_DEBUG_BG = (0, 0, 0)
COLOR_PLAYER = (240, 200, 80)
COLOR_PLAYER_OUTLINE = (30, 30, 30)

# ----------------------------------------------------------------------------
# Player / Robot movement
# ----------------------------------------------------------------------------
# Time (seconds) for the robot to glide from one tile to the next.
PLAYER_MOVE_DURATION = 0.18

# Directions, expressed as (dx, dy) in tile units. Matches a standard
# screen-space grid: +x is right, +y is down.
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

# ----------------------------------------------------------------------------
# Camera
# ----------------------------------------------------------------------------
CAMERA_SMOOTHING = 8.0  # higher = camera snaps to target faster

# ----------------------------------------------------------------------------
# Asset paths (relative to project root)
# ----------------------------------------------------------------------------
ASSETS_DIR = "assets"
SPRITES_DIR = f"{ASSETS_DIR}/sprites"
TILES_DIR = f"{ASSETS_DIR}/tiles"
UI_DIR = f"{ASSETS_DIR}/ui"
FONTS_DIR = f"{ASSETS_DIR}/fonts"
LEVELS_DIR = "levels"

# ----------------------------------------------------------------------------
# Debug
# ----------------------------------------------------------------------------
DEBUG_FONT_SIZE = 16

# ----------------------------------------------------------------------------
# Office Objects (Phase 2)
# ----------------------------------------------------------------------------
INTERACT_RANGE_TILES = 1  # how close (in tiles) the robot must be to interact

# Object colors, keyed by ObjectType name (see game/objects.py)
COLOR_OBJ_DESK = (96, 70, 48)
COLOR_OBJ_COFFEE = (60, 36, 20)
COLOR_OBJ_COFFEE_ACCENT = (220, 170, 60)
COLOR_OBJ_BUG = (200, 60, 60)
COLOR_OBJ_JIRA = (50, 110, 200)
COLOR_OBJ_SERVER = (40, 40, 50)
COLOR_OBJ_SERVER_LIGHT = (80, 220, 120)
COLOR_OBJ_GIT = (240, 130, 40)
COLOR_OBJ_ROUTER = (90, 90, 110)
COLOR_OBJ_ROUTER_LIGHT = (90, 200, 220)
COLOR_OBJ_MEETING_DOOR = (140, 100, 60)
COLOR_OBJ_LAPTOP = (210, 210, 220)

COLOR_INTERACT_PROMPT_BG = (0, 0, 0)
COLOR_INTERACT_PROMPT_TEXT = (255, 230, 140)
COLOR_TOAST_BG = (0, 0, 0)
COLOR_TOAST_TEXT = (230, 230, 240)

# Player stats
PLAYER_MAX_ENERGY = 100.0
COFFEE_ENERGY_RESTORE = 20.0

# Toast notifications
TOAST_DURATION = 2.2  # seconds visible
TOAST_FADE = 0.4  # seconds of fade in/out at start/end

# ----------------------------------------------------------------------------
# Script Editor (Phase 3)
# ----------------------------------------------------------------------------
EDITOR_PANEL_WIDTH = 490       # left panel width in logical pixels
EDITOR_FONT_SIZE = 15          # monospace code font size
EDITOR_LINE_HEIGHT = 20        # pixels per code line
EDITOR_LINE_NUM_WIDTH = 36     # width of the line-number gutter
EDITOR_TOP_BAR_HEIGHT = 38     # header bar (title + buttons)
EDITOR_STATUS_BAR_HEIGHT = 28  # bottom status/error bar

# Editor color palette
COLOR_EDITOR_BG = (22, 24, 30)
COLOR_EDITOR_GUTTER = (30, 32, 40)
COLOR_EDITOR_GUTTER_TEXT = (80, 90, 100)
COLOR_EDITOR_CURSOR = (220, 220, 220)
COLOR_EDITOR_CURSOR_LINE = (35, 38, 48)
COLOR_EDITOR_ACTIVE_LINE = (42, 46, 60)  # currently executing line
COLOR_EDITOR_PANEL_BORDER = (50, 55, 70)
COLOR_EDITOR_STATUS_BG = (18, 20, 26)
COLOR_EDITOR_STATUS_OK = (100, 200, 140)
COLOR_EDITOR_STATUS_ERR = (210, 80, 80)
COLOR_EDITOR_STATUS_RUN = (80, 180, 220)

# Syntax highlight colors
COLOR_SYN_DEFAULT = (210, 215, 220)
COLOR_SYN_KEYWORD = (200, 140, 255)
COLOR_SYN_ENGINE_FN = (100, 210, 255)
COLOR_SYN_STRING = (155, 210, 110)
COLOR_SYN_COMMENT = (100, 110, 130)
COLOR_SYN_NUMBER = (255, 200, 100)
COLOR_SYN_CONSTANT = (255, 160, 90)  # BUG, COFFEE, WALL, EMPTY, ...
COLOR_SYN_BUILTIN = (180, 210, 180)

# Toolbar button colors
COLOR_BTN_RUN = (50, 180, 100)
COLOR_BTN_RUN_HOVER = (70, 210, 120)
COLOR_BTN_STOP = (200, 70, 60)
COLOR_BTN_STOP_HOVER = (220, 90, 80)
COLOR_BTN_INACTIVE = (55, 60, 75)
COLOR_BTN_TEXT = (240, 240, 245)

# Game viewport sits to the right of the editor panel
GAME_VIEWPORT_X = EDITOR_PANEL_WIDTH
GAME_VIEWPORT_W = SCREEN_WIDTH - EDITOR_PANEL_WIDTH
GAME_VIEWPORT_H = SCREEN_HEIGHT

# Scripting execution timing
SCRIPT_STEP_DELAY_DEFAULT = 0.0    # extra pause after each animation (seconds)
SCRIPT_TURN_DISPLAY_TIME = 0.12    # seconds the robot is "shown" mid-turn
