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
