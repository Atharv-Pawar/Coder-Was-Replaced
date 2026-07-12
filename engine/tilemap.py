"""Placeholder grid tilemap. Drop-in replaceable by pytmx .tmx files later."""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from engine import constants as c


class TileType(IntEnum):
    FLOOR = 0
    FLOOR_ALT = 1
    WALL = 2


SOLID_TILES = {TileType.WALL}


@dataclass(frozen=True)
class Tile:
    tile_type: TileType

    @property
    def is_solid(self) -> bool:
        return self.tile_type in SOLID_TILES


class TileMap:
    def __init__(self, width: int, height: int, tile_size: int = c.TILE_SIZE):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self._grid: list[list[TileType]] = [
            [TileType.FLOOR for _ in range(width)] for _ in range(height)
        ]

    def set_tile(self, x: int, y: int, tile_type: TileType) -> None:
        if self.in_bounds(x, y):
            self._grid[y][x] = tile_type

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_tile(self, x: int, y: int) -> Tile:
        if not self.in_bounds(x, y):
            return Tile(TileType.WALL)
        return Tile(self._grid[y][x])

    def is_walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and not self.get_tile(x, y).is_solid

    @property
    def pixel_width(self) -> int:
        return self.width * self.tile_size

    @property
    def pixel_height(self) -> int:
        return self.height * self.tile_size


def load_office_map() -> TileMap:
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
    tile_map = TileMap(width=len(layout[0]), height=len(layout))
    for y, row in enumerate(layout):
        for x, ch in enumerate(row):
            if ch == "#":
                tile_map.set_tile(x, y, TileType.WALL)
            else:
                tile_map.set_tile(x, y, TileType.FLOOR if (x + y) % 2 == 0 else TileType.FLOOR_ALT)
    return tile_map
