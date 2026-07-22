"""Global constants — single source of truth for every tunable value."""

# ── Window / Display ─────────────────────────────────────────────────────────
WINDOW_TITLE  = "Coder Was Replaced"
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60

# ── Tile / Grid ──────────────────────────────────────────────────────────────
TILE_SIZE = 32

# ── Colors — base palette ────────────────────────────────────────────────────
COLOR_BG           = (18, 18, 24)
COLOR_FLOOR        = (46, 52, 64)
COLOR_FLOOR_ALT    = (51, 58, 71)
COLOR_WALL         = (28, 30, 38)
COLOR_GRID         = (60, 64, 76)
COLOR_DEBUG_TEXT   = (120, 220, 120)
COLOR_DEBUG_BG     = (0, 0, 0)
COLOR_PLAYER       = (240, 200, 80)
COLOR_PLAYER_OUTLINE = (30, 30, 30)

# ── Office objects ────────────────────────────────────────────────────────────
COLOR_OBJ_DESK          = (96, 70, 48)
COLOR_OBJ_COFFEE        = (60, 36, 20)
COLOR_OBJ_COFFEE_ACCENT = (220, 170, 60)
COLOR_OBJ_BUG           = (200, 60, 60)
COLOR_OBJ_JIRA          = (50, 110, 200)
COLOR_OBJ_SERVER        = (40, 40, 50)
COLOR_OBJ_SERVER_LIGHT  = (80, 220, 120)
COLOR_OBJ_GIT           = (240, 130, 40)
COLOR_OBJ_ROUTER        = (90, 90, 110)
COLOR_OBJ_ROUTER_LIGHT  = (90, 200, 220)
COLOR_OBJ_MEETING_DOOR  = (140, 100, 60)
COLOR_OBJ_LAPTOP        = (210, 210, 220)
COLOR_INTERACT_PROMPT_BG   = (0, 0, 0)
COLOR_INTERACT_PROMPT_TEXT = (255, 230, 140)
COLOR_TOAST_BG   = (0, 0, 0)
COLOR_TOAST_TEXT = (230, 230, 240)

# ── Player stats ──────────────────────────────────────────────────────────────
PLAYER_MAX_ENERGY    = 100.0
COFFEE_ENERGY_RESTORE = 20.0
PLAYER_MOVE_DURATION  = 0.18   # seconds for tile-to-tile glide

# ── Camera ────────────────────────────────────────────────────────────────────
CAMERA_SMOOTHING = 8.0

# ── Toast ─────────────────────────────────────────────────────────────────────
TOAST_DURATION = 2.2
TOAST_FADE     = 0.4

# ── Debug ─────────────────────────────────────────────────────────────────────
DEBUG_FONT_SIZE = 16

# ── Script Editor (Phase 3) ───────────────────────────────────────────────────
EDITOR_PANEL_WIDTH     = 490
EDITOR_FONT_SIZE       = 15
EDITOR_LINE_HEIGHT     = 20
EDITOR_LINE_NUM_WIDTH  = 36
EDITOR_TOP_BAR_HEIGHT  = 38
EDITOR_STATUS_BAR_HEIGHT = 28

COLOR_EDITOR_BG            = (22, 24, 30)
COLOR_EDITOR_GUTTER        = (30, 32, 40)
COLOR_EDITOR_GUTTER_TEXT   = (80, 90, 100)
COLOR_EDITOR_CURSOR        = (220, 220, 220)
COLOR_EDITOR_CURSOR_LINE   = (35, 38, 48)
COLOR_EDITOR_ACTIVE_LINE   = (42, 46, 60)
COLOR_EDITOR_PANEL_BORDER  = (50, 55, 70)
COLOR_EDITOR_STATUS_BG     = (18, 20, 26)
COLOR_EDITOR_STATUS_OK     = (100, 200, 140)
COLOR_EDITOR_STATUS_ERR    = (210, 80, 80)
COLOR_EDITOR_STATUS_RUN    = (80, 180, 220)

COLOR_SYN_DEFAULT  = (210, 215, 220)
COLOR_SYN_KEYWORD  = (200, 140, 255)
COLOR_SYN_ENGINE_FN = (100, 210, 255)
COLOR_SYN_STRING   = (155, 210, 110)
COLOR_SYN_COMMENT  = (100, 110, 130)
COLOR_SYN_NUMBER   = (255, 200, 100)
COLOR_SYN_CONSTANT = (255, 160, 90)
COLOR_SYN_BUILTIN  = (180, 210, 180)

COLOR_BTN_RUN        = (50, 180, 100)
COLOR_BTN_RUN_HOVER  = (70, 210, 120)
COLOR_BTN_STOP       = (200, 70, 60)
COLOR_BTN_STOP_HOVER = (220, 90, 80)
COLOR_BTN_INACTIVE   = (55, 60, 75)
COLOR_BTN_TEXT       = (240, 240, 245)

GAME_VIEWPORT_X = EDITOR_PANEL_WIDTH
GAME_VIEWPORT_W = SCREEN_WIDTH - EDITOR_PANEL_WIDTH
GAME_VIEWPORT_H = SCREEN_HEIGHT

SCRIPT_STEP_DELAY_DEFAULT = 0.0
SCRIPT_TURN_DISPLAY_TIME  = 0.12

# ── Progression / Unlock (Phase 4) ───────────────────────────────────────────
PROGRESS_PANEL_HEIGHT = 62

COLOR_XP_BAR_BG    = (30, 33, 42)
COLOR_XP_BAR_FILL  = (80, 180, 110)
COLOR_XP_BAR_FILL2 = (120, 220, 80)
COLOR_LEVEL_BG     = (28, 32, 44)
COLOR_LEVEL_BORDER = (70, 80, 110)
COLOR_LEVEL_TEXT   = (200, 215, 255)
COLOR_LEVEL_XP_TEXT = (140, 200, 140)
COLOR_UNLOCKED_FN  = (100, 215, 140)
COLOR_LOCKED_FN    = (90, 95, 110)
COLOR_NEXT_UNLOCK  = (255, 200, 80)
COLOR_UNLOCK_TOAST = (120, 255, 160)
COLOR_PROGRESS_DIVIDER = (40, 44, 56)

# ── Economy (Phase 5) ────────────────────────────────────────────────────────
ECONOMY_TICK_INTERVAL = 8.0
ECONOMY_PANEL_HEIGHT  = 60

COLOR_SALARY   = (255, 215, 80)
COLOR_REP      = (100, 200, 255)
COLOR_STARS    = (255, 180, 60)
COLOR_COFFEE_C = (180, 120, 70)
COLOR_COMPUTE  = (140, 230, 200)

ECONOMY_HUD_HEIGHT  = 26
COLOR_ECONOMY_HUD_BG = (16, 18, 24)

COLOR_SHOP_BG        = (18, 20, 28)
COLOR_SHOP_BORDER    = (70, 80, 110)
COLOR_SHOP_TITLE     = (200, 215, 255)
COLOR_SHOP_ITEM_BG   = (28, 32, 44)
COLOR_SHOP_OWNED     = (60, 180, 100)
COLOR_SHOP_COST      = (255, 215, 80)
COLOR_SHOP_AFFORD    = (100, 215, 140)
COLOR_SHOP_CANT      = (180, 80, 70)

# ── Missions (Phase 6) ────────────────────────────────────────────────────────
MISSION_HUD_W      = 240
MISSION_HUD_MARGIN = 10

COLOR_MISSION_BG          = (18, 22, 32)
COLOR_MISSION_BORDER      = (70, 90, 140)
COLOR_MISSION_TITLE       = (200, 220, 255)
COLOR_MISSION_FLAVOUR     = (120, 130, 160)
COLOR_MISSION_OBJ_DONE    = (80, 210, 120)
COLOR_MISSION_OBJ_ACTIVE  = (200, 215, 255)
COLOR_MISSION_REWARD      = (255, 215, 80)
COLOR_MISSION_TIMER_OK    = (140, 200, 140)
COLOR_MISSION_TIMER_WARN  = (255, 170, 60)
COLOR_MISSION_TIMER_CRIT  = (220, 70, 60)
COLOR_MISSION_BAR_BG      = (30, 35, 50)
COLOR_MISSION_BAR_FILL    = (60, 140, 220)
COLOR_MISSION_BAR_DONE    = (60, 200, 100)
COLOR_COMPLETE_BG         = (20, 50, 30)
COLOR_COMPLETE_TEXT       = (100, 255, 150)
COLOR_FAIL_BG             = (50, 20, 20)
COLOR_FAIL_TEXT           = (255, 100, 80)

# ----------------------------------------------------------------------------
# Floor Transitions (Phase 8)
# ----------------------------------------------------------------------------
COLOR_FLOOR_TRANSITION_BG   = (10, 12, 20)
COLOR_FLOOR_TRANSITION_TEXT = (180, 210, 255)
COLOR_FLOOR_TRANSITION_SUB  = (100, 130, 180)
COLOR_FLOOR_ADVANCE_HINT    = (255, 200, 80)

# ----------------------------------------------------------------------------
# Phase 9 — Polish (achievements, settings, save)
# ----------------------------------------------------------------------------
# Achievement popup (top of game panel)
COLOR_ACH_BG      = (24, 36, 24)
COLOR_ACH_BORDER  = (80, 200, 100)
COLOR_ACH_TITLE   = (120, 255, 140)
COLOR_ACH_DESC    = (160, 200, 165)
COLOR_ACH_LABEL   = (80, 200, 100)

# Settings overlay
COLOR_SETTINGS_BG       = (16, 18, 28)
COLOR_SETTINGS_BORDER   = (70, 80, 130)
COLOR_SETTINGS_TITLE    = (200, 215, 255)
COLOR_SETTINGS_LABEL    = (140, 150, 190)
COLOR_SETTINGS_VALUE    = (255, 215, 80)
COLOR_SETTINGS_HINT     = (90, 100, 140)
COLOR_SETTINGS_BAR_BG   = (30, 33, 48)
COLOR_SETTINGS_BAR_FILL = (80, 140, 220)

# ----------------------------------------------------------------------------
# AI Employees (Phase 7)
# ----------------------------------------------------------------------------
MAX_EMPLOYEES = 6           # max simultaneous employees

# Bug respawner
BUG_RESPAWN_INTERVAL = 18.0   # seconds between new bug spawns
BUG_MAX_COUNT        = 5      # max bugs alive at once

# Employee HUD (top-left of game panel, below any debug overlay)
EMPLOYEE_HUD_X      = 8       # relative to GAME_VIEWPORT_X
EMPLOYEE_HUD_Y      = 8
EMPLOYEE_HUD_ROW_H  = 22

# Hire panel
COLOR_HIRE_BG       = (18, 20, 28)
COLOR_HIRE_BORDER   = (80, 100, 160)
COLOR_HIRE_TITLE    = (200, 220, 255)
COLOR_HIRE_ITEM_BG  = (28, 32, 44)
COLOR_HIRE_OWNED    = (60, 180, 100)
COLOR_HIRE_LOCKED   = (80, 85, 100)
COLOR_HIRE_COST     = (255, 215, 80)
COLOR_HIRE_AFFORD   = (100, 215, 140)
COLOR_HIRE_CANT     = (180, 80, 70)
COLOR_HIRE_STATUS_RUN  = (80, 200, 120)
COLOR_HIRE_STATUS_IDLE = (160, 160, 180)
COLOR_HIRE_STATUS_ERR  = (210, 80, 80)
