"""
Placeholder tilemap for Phase 1.

Real Tiled (.tmx) support will be added via `pytmx` in a later phase once
we have an actual map authored in Tiled. For now we generate a simple
procedural office layout in code so the engine, camera, and player
movement can all be built and tested without waiting on art assets.

The public interface (`TileMap`) is intentionally small and stable:
    - width, height          (in tiles)
    - tile_size               (in pixels)
    - is_walkable(x, y)       -> bool
    - get_tile(x, y)          -> Tile
    - layers                  iterable of layers for rendering

When we swap in real .tmx files, only `load_office_map()` needs to change;
everything downstream (camera, renderer, player) consumes the same
`TileMap` interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from engine import constants as c


class TileType(IntEnum):
    FLOOR = 0
    FLOOR_ALT = 1
    WALL = 2
    DESK = 3


# Which tile types block movement.
SOLID_TILES = {TileType.WALL, TileType.DESK}


@dataclass(frozen=True)
class Tile:
    tile_type: TileType

    @property
    def is_solid(self) -> bool:
        return self.tile_type in SOLID_TILES


class TileMap:
    """A simple grid-based map. Origin (0, 0) is top-left."""

    def __init__(self, width: int, height: int, tile_size: int = c.TILE_SIZE):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        # grid[y][x] -> TileType
        self._grid: list[list[TileType]] = [
            [TileType.FLOOR for _ in range(width)] for _ in range(height)
        ]

    # -- editing -------------------------------------------------------
    def set_tile(self, x: int, y: int, tile_type: TileType) -> None:
        if self.in_bounds(x, y):
            self._grid[y][x] = tile_type

    def fill_rect(self, x0: int, y0: int, x1: int, y1: int, tile_type: TileType) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set_tile(x, y, tile_type)

    # -- queries ---------------------------------------------------------
    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int) -> Tile:
        if not self.in_bounds(x, y):
            return Tile(TileType.WALL)
        return Tile(self._grid[y][x])

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        return not self.get_tile(x, y).is_solid

    @property
    def pixel_width(self) -> int:
        return self.width * self.tile_size

    @property
    def pixel_height(self) -> int:
        return self.height * self.tile_size


def load_office_map() -> TileMap:
    """Build the Phase 1/2 placeholder office.

    Layout legend:
        # = wall
        . = floor
        , = floor (alt, for a checkerboard look)

    Desks, coffee machines, and other furniture are no longer baked into
    the tile grid -- they're placed as real interactable GameObjects
    (see game/objects.py) so they can be walked up to and used. This
    layout will be replaced by `load_tmx("levels/office.tmx")` once a
    real Tiled map exists, without changing any calling code.
    """
    layout = [
        "##########################",
        "#........................#",
        "#........................#",
        "#........................#",
        "#........................#",
        "#........................#",
        "#........................#",
        "#....######....######....#",
        "#....#....#....#....#....#",
        "#....#....#....#....#....#",
        "#....######....######....#",
        "#........................#",
        "#........................#",
        "#........................#",
        "##########################",
    ]

    height = len(layout)
    width = len(layout[0])
    tile_map = TileMap(width=width, height=height)

    for y, row in enumerate(layout):
        for x, ch in enumerate(row):
            if ch == "#":
                tile_map.set_tile(x, y, TileType.WALL)
            else:
                # checkerboard floor for a bit of visual texture
                tile_type = TileType.FLOOR if (x + y) % 2 == 0 else TileType.FLOOR_ALT
                tile_map.set_tile(x, y, tile_type)

    return tile_map
