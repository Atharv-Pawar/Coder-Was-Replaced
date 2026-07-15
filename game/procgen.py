"""
Procedural office generator — Phase 8.

Generates a fresh TileMap + object list for each floor. Uses a
deterministic seed (based on floor number) so the same floor always
looks the same on replay, while different floors feel genuinely different.

Algorithm
---------
1.  Fill the map with alternating floor tiles (checkerboard texture).
2.  Draw outer walls.
3.  Place N meeting rooms (walled rectangles, each with a doorway).
4.  Place desk rows in the open space between rooms.
5.  Place the infrastructure cluster (server rack, git repo, WiFi) in
    the top-right corner.
6.  Place the coffee machine, laptop, and Jira ticket.
7.  Scatter bugs at random walkable positions.
8.  Guarantee the player spawn (top-left open area) is clear.

Public API
----------
  generate(floor_num)  -> (TileMap, list[GameObject], spawn_pos)
"""

from __future__ import annotations

import random
from engine import constants as c
from engine.tilemap import TileMap, TileType
from game.objects import ObjectType, make_object, GameObject


# ── Floor configuration ───────────────────────────────────────────────────────
FLOOR_CONFIGS: list[dict] = [
    dict(name="Basement Startup",  width=26, height=15, n_rooms=2, n_desks=3, n_bugs=2, n_desk_rows=2),
    dict(name="Open Plan Office",  width=34, height=18, n_rooms=3, n_desks=4, n_bugs=3, n_desk_rows=3),
    dict(name="Corporate Floor",   width=42, height=22, n_rooms=4, n_desks=5, n_bugs=4, n_desk_rows=4),
    dict(name="Executive Suite",   width=50, height=26, n_rooms=5, n_desks=6, n_bugs=5, n_desk_rows=5),
    dict(name="Penthouse HQ",      width=58, height=30, n_rooms=6, n_desks=7, n_bugs=6, n_desk_rows=6),
]

# XP-level index required to unlock each floor (matches Progression.level_index)
FLOOR_UNLOCK_LEVELS = [0, 1, 2, 3, 4]

# Player spawn offset from top-left (always tries to be a clear tile)
SPAWN_OFFSET = (2, 2)


def get_config(floor_num: int) -> dict:
    return FLOOR_CONFIGS[min(floor_num, len(FLOOR_CONFIGS) - 1)]


def generate(floor_num: int, seed: int | None = None
             ) -> tuple[TileMap, list[GameObject], tuple[int, int]]:
    """
    Generate a complete office layout for `floor_num`.

    Returns
    -------
    tilemap    : TileMap
    objects    : list[GameObject]
    spawn_pos  : (grid_x, grid_y) — safe starting position for the player
    """
    cfg  = get_config(floor_num)
    rng  = random.Random(seed if seed is not None else floor_num * 7919 + 42)
    W, H = cfg["width"], cfg["height"]

    tilemap  = TileMap(width=W, height=H)
    objects: list[GameObject] = []

    # Track cells reserved by rooms (so desk rows avoid them)
    reserved: set[tuple[int, int]] = set()

    # ── Step 1: checkerboard floor fill ──────────────────────────────────────
    for y in range(H):
        for x in range(W):
            tt = TileType.FLOOR if (x + y) % 2 == 0 else TileType.FLOOR_ALT
            tilemap.set_tile(x, y, tt)

    # ── Step 2: outer walls ───────────────────────────────────────────────────
    for x in range(W):
        tilemap.set_tile(x, 0, TileType.WALL)
        tilemap.set_tile(x, H - 1, TileType.WALL)
    for y in range(H):
        tilemap.set_tile(0, y, TileType.WALL)
        tilemap.set_tile(W - 1, y, TileType.WALL)
    for x in range(W):
        reserved.add((x, 0)); reserved.add((x, H - 1))
    for y in range(H):
        reserved.add((0, y)); reserved.add((W - 1, y))

    # ── Step 3: meeting rooms ─────────────────────────────────────────────────
    room_rects: list[tuple[int, int, int, int]] = []
    for _ in range(cfg["n_rooms"] * 8):   # max attempts
        if len(room_rects) >= cfg["n_rooms"]:
            break
        rw = rng.randint(5, max(5, min(9, W // 4)))
        rh = rng.randint(4, max(4, min(7, H // 4)))
        rx = rng.randint(4, W - rw - 4)
        ry = rng.randint(4, H - rh - 4)

        # Reject if too close to another room
        candidate = set()
        for cy in range(ry - 1, ry + rh + 2):
            for cx in range(rx - 1, rx + rw + 2):
                candidate.add((cx, cy))
        if candidate & reserved:
            continue

        # Accept: draw walls
        for bx in range(rx, rx + rw):
            tilemap.set_tile(bx, ry, TileType.WALL)
            tilemap.set_tile(bx, ry + rh - 1, TileType.WALL)
        for by in range(ry, ry + rh):
            tilemap.set_tile(rx, by, TileType.WALL)
            tilemap.set_tile(rx + rw - 1, by, TileType.WALL)

        # Add a doorway (gap in one wall)
        side = rng.randint(0, 3)
        if side == 0:   # top wall
            tilemap.set_tile(rng.randint(rx + 1, rx + rw - 2), ry, TileType.FLOOR)
        elif side == 1: # bottom wall
            tilemap.set_tile(rng.randint(rx + 1, rx + rw - 2), ry + rh - 1, TileType.FLOOR)
        elif side == 2: # left wall
            tilemap.set_tile(rx, rng.randint(ry + 1, ry + rh - 2), TileType.FLOOR)
        else:           # right wall
            tilemap.set_tile(rx + rw - 1, rng.randint(ry + 1, ry + rh - 2), TileType.FLOOR)

        # Mark as meeting room object on the door side
        door_x = rx + rw // 2
        door_y = ry + rh // 2
        objects.append(make_object(ObjectType.MEETING_ROOM, door_x, door_y))

        reserved |= candidate
        room_rects.append((rx, ry, rw, rh))

    # ── Step 4: desk rows ─────────────────────────────────────────────────────
    desk_placed = 0
    for _ in range(cfg["n_desk_rows"] * 10):
        if desk_placed >= cfg["n_desk_rows"] * cfg["n_desks"]:
            break
        row_y = rng.randint(2, H - 3)
        row_x_start = rng.randint(2, W - cfg["n_desks"] * 2 - 2)
        gap = rng.randint(1, 2)

        placed_this_row = 0
        for i in range(cfg["n_desks"]):
            dx = row_x_start + i * (1 + gap)
            dy = row_y
            if (dx, dy) in reserved or not tilemap.is_walkable(dx, dy):
                continue
            objects.append(make_object(ObjectType.DESK, dx, dy))
            reserved.add((dx, dy))
            placed_this_row += 1

        desk_placed += placed_this_row

    # ── Step 5: infrastructure cluster (top-right corner) ────────────────────
    infra_x = W - 4
    for infra_y, obj_type in [(3, ObjectType.WIFI_ROUTER),
                               (4, ObjectType.SERVER_RACK),
                               (5, ObjectType.GIT_REPO)]:
        if tilemap.is_walkable(infra_x, infra_y) and (infra_x, infra_y) not in reserved:
            objects.append(make_object(obj_type, infra_x, infra_y))
            reserved.add((infra_x, infra_y))

    # ── Step 6: coffee machine, laptop, jira ticket ───────────────────────────
    singles = [
        (ObjectType.COFFEE_MACHINE, W // 2,     H // 2    ),
        (ObjectType.LAPTOP,         W // 2 - 3, 2         ),
        (ObjectType.JIRA_TICKET,    W - 5,      2         ),
    ]
    for obj_type, px, py in singles:
        # Walk nearby until a free walkable tile is found
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                tx, ty = px + dx, py + dy
                if (tilemap.is_walkable(tx, ty)
                        and (tx, ty) not in reserved
                        and 1 < tx < W - 2
                        and 1 < ty < H - 2):
                    objects.append(make_object(obj_type, tx, ty))
                    reserved.add((tx, ty))
                    break
            else:
                continue
            break

    # ── Step 7: bugs ──────────────────────────────────────────────────────────
    bugs_placed = 0
    attempts = 0
    while bugs_placed < cfg["n_bugs"] and attempts < 200:
        bx = rng.randint(2, W - 3)
        by = rng.randint(2, H - 3)
        if tilemap.is_walkable(bx, by) and (bx, by) not in reserved:
            objects.append(make_object(ObjectType.BUG, bx, by))
            reserved.add((bx, by))
            bugs_placed += 1
        attempts += 1

    # ── Step 8: safe spawn position (top-left open area) ─────────────────────
    spawn_x, spawn_y = SPAWN_OFFSET
    for sy in range(spawn_y, H - 1):
        for sx in range(spawn_x, W // 3):
            if tilemap.is_walkable(sx, sy) and (sx, sy) not in reserved:
                return tilemap, objects, (sx, sy)

    return tilemap, objects, (spawn_x, spawn_y)


def floor_name(floor_num: int) -> str:
    cfg = get_config(floor_num)
    return cfg["name"]


def floor_unlock_level(floor_num: int) -> int:
    return FLOOR_UNLOCK_LEVELS[min(floor_num, len(FLOOR_UNLOCK_LEVELS) - 1)]
