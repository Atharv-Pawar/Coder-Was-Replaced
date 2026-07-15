# levels/

This directory holds Tiled map files (`.tmx`) for Phase 9.

Phase 8 uses **procedural generation** (`game/procgen.py`) for all five
floors. When real hand-crafted maps are ready, drop them here and the
loader in `game/procgen.py` will prefer them over the generated fallback.

---

## Adding a .tmx map

1. Install Tiled (https://www.mapeditor.org/) and pytmx:
   ```bash
   pip install pytmx
   ```

2. Create a map in Tiled using 32×32 px tiles.

3. Required layers (by name):

   | Layer | Type | Purpose |
   |---|---|---|
   | `ground` | Tile | Floor / wall tiles |
   | `objects` | Object | Furniture & interactables |

4. Save as `levels/floor_0.tmx`, `levels/floor_1.tmx`, etc.

5. In `game/procgen.py`, the `generate()` function will automatically
   try to load `levels/floor_{n}.tmx` if pytmx is installed:

   ```python
   try:
       import pytmx
       tmx = pytmx.load_pygame(f"levels/floor_{floor_num}.tmx")
       return _load_from_tmx(tmx)
   except (ImportError, FileNotFoundError):
       pass   # fall back to procedural generation
   ```

## Object layer properties

Each object in the Tiled `objects` layer needs a `type` property matching
one of the `ObjectType` enum names:

```
DESK, COFFEE_MACHINE, BUG, JIRA_TICKET, SERVER_RACK,
GIT_REPO, WIFI_ROUTER, MEETING_ROOM, LAPTOP
```

## Tile GIDs

The tile layer should use GID 1 = floor, GID 2 = floor_alt, GID 3 = wall.
(These map directly to `TileType` enum values in `engine/tilemap.py`.)

---

*Phase 9 will add full `.tmx` + `pytmx` loading with real pixel art.*
