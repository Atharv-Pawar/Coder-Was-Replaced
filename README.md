# Coder Was Replaced

> You are the last software engineer in a company that has automated
> everything. Instead of writing code yourself, you program an AI coding
> bot to survive office life.

An original automation/idle game inspired by *The Farmer Was Replaced*,
*Human Resource Machine*, and *shapez* — built from scratch in Python +
Pygame, in clean, testable phases.

---

## Status: Phase 3 — Python Scripting Engine ✅

Phases 1–3 are fully complete and running at 60 FPS on Windows/Linux/macOS.

---

## Running it

```bash
pip install -r requirements.txt
python main.py
```

Requires **Python 3.12+** and **pygame-ce ≥ 2.5.0**.

---

## Controls

| Key / Input | Action |
|---|---|
| Arrow keys / WASD | Move the robot manually (when script is not running) |
| **E** / Space | Interact with the object you're facing |
| **F5** / Run button | Run your script |
| **F6** / Stop button | Stop execution |
| **F3** | Toggle debug overlay |
| Esc | Quit |
| `<` `>` buttons | Adjust script execution speed (0.5× / 0.75× / 1× / 2×) |
| Click in editor | Place text cursor |

---

## Script API

Write Python in the editor. The robot executes each command live, one
step at a time, with smooth animations.

### Movement

```python
move()          # step forward one tile (in the direction the robot is facing)
turn_left()     # rotate 90° counter-clockwise
turn_right()    # rotate 90° clockwise
```

### Sensing

```python
result = look()   # returns what's directly in front of the robot
```

Possible return values: `EMPTY`, `WALL`, `BUG`, `COFFEE`, `DESK`,
`SERVER`, `JIRA`, `GIT`, `WIFI`, `MEETING`, `LAPTOP`

### Actions

```python
fix_bug()        # fix the bug you're facing
drink_coffee()   # use the coffee machine you're facing (+20 energy)
commit()         # commit to the git repo you're facing
```

### Example scripts

```python
# Fix every bug and grab coffee on the way
while True:
    if look() == BUG:
        fix_bug()
    elif look() == COFFEE:
        drink_coffee()
    move()
```

```python
# Sweep every tile in a grid pattern
for row in range(13):
    for col in range(24):
        if look() == BUG:
            fix_bug()
        move()
    turn_right()
    move()
    turn_right()
```

Safe Python subset is supported: `for`, `while`, `if/elif/else`, `def`,
`range()`, `len()`, `list`, `int`, `str`, `bool`, `min`, `max`, `abs`,
`enumerate`, `zip`, and more. No file I/O, no imports, no `__builtins__`
escape — the sandbox is locked down.

---

## Project structure

```
Coder-Was-Replaced/
├── main.py                    # Entry point — run this
│
├── engine/                    # Low-level systems (no game content)
│   ├── game.py                # Main loop, fixed timestep, top-level wiring
│   ├── renderer.py            # Window, logical surface, all draw calls
│   ├── camera.py              # Smoothed camera with split-screen viewport offset
│   ├── tilemap.py             # Grid map + collision (placeholder; .tmx-ready)
│   ├── animation.py           # Tweening / Vec2Tween / easing helpers
│   ├── input.py               # Keyboard + mouse event routing
│   ├── events.py              # Toast notification queue
│   ├── scripting.py           # Thread-based Python execution engine + sandbox
│   └── constants.py           # Every tunable value lives here
│
├── game/                      # Game content that sits on top of the engine
│   ├── player.py              # The AI robot entity + tile-based movement
│   ├── objects.py             # Office furniture system (desk, coffee, bug, ...)
│   ├── office.py              # Ties map + objects + robot + camera together
│   └── editor.py              # Split-screen code editor (syntax highlight, cursor, ...)
│
├── assets/                    # Sprites, tiles, UI, fonts, sounds, music (Phase 9)
├── levels/                    # Real .tmx maps via pytmx (Phase 8)
├── scripts/                   # Saved player scripts (Phase 4+)
├── data/                      # JSON config for items / upgrades (Phase 4+)
└── tests/                     # Unit tests
```

### Key files by size (Phase 3 baseline)

| File | Lines | Purpose |
|---|---|---|
| `game/editor.py` | 524 | Code editor UI |
| `engine/scripting.py` | 371 | Thread-based execution engine |
| `engine/renderer.py` | 244 | All rendering and draw calls |
| `game/objects.py` | 163 | Office object system |
| `engine/constants.py` | 157 | All tunable values |
| **Total** | **~2,300** | across 16 Python files |

---

## Architecture highlights

### Split-screen layout

```
┌──────────────────────┬─────────────────────────────────┐
│   SCRIPT EDITOR      │                                  │
│   490 px             │   GAME WORLD  790 px             │
│                      │                                  │
│  [Run F5] [Stop F6]  │   tile map + objects + robot     │
│  1 │ while True:     │   camera follows robot           │
│  2 │     if look()   │   energy bar + toast HUD         │
│  3 │         fix_bug │                                  │
│  ► │ ← executing     │                                  │
│    │                 │                                  │
│  Status / error bar  │                                  │
└──────────────────────┴─────────────────────────────────┘
```

### Script execution model

The script runs in a **background thread**. Each API call (`move()`,
`look()`, etc.) posts a command to the main thread and **blocks** until
the animation finishes. This means:

- The game loop never freezes (script and rendering are decoupled)
- Step-by-step visual execution is automatic — no coroutines or manual
  yielding needed in player code
- Stop is instant: a threading.Event raises `ScriptStopped` at the next
  command boundary
- `sys.settrace()` tracks the currently-executing source line with zero
  overhead, enabling live line highlighting in the editor

### Collision model

`Office.is_walkable(x, y)` combines tilemap walls **and** solid objects
(desks, servers, etc.) into one callable. The robot's `try_move()` and
the scripting engine both go through this single function, so map and
object collision are always consistent.

---

## Roadmap

| Phase | What ships | Status |
|---|---|---|
| 1 | Engine foundation: window, loop, renderer, camera, tilemap, input | ✅ Done |
| 2 | Office world: objects, collision, interaction, energy bar, toasts | ✅ Done |
| 3 | Python scripting engine: editor, syntax highlighting, step execution | ✅ Done |
| 4 | Unlock system: gate API functions behind XP; upgrade shop | 🔜 Next |
| 5 | Economy: salary, reputation, git stars, compute credits | ⏳ |
| 6 | Missions: fix bugs, deploy, close tickets, survive Monday | ⏳ |
| 7 | AI employees: hire interns → architects, assign them scripts | ⏳ |
| 8 | Procedural offices + real Tiled `.tmx` maps | ⏳ |
| 9 | Steam polish: audio, achievements, settings, controller, packaging | ⏳ |

---

## Design philosophy

Built **one phase at a time**, each fully playable before the next
begins — the way a small indie studio would build it. Engine code
(`engine/`) is kept strictly independent of game content (`game/`) so
systems are swappable without cascading changes:

- The placeholder tilemap can be replaced by real `.tmx` files by
  changing only `load_office_map()` — the renderer and camera are
  unchanged.
- The placeholder colored-rectangle art can be replaced by sprite sheets
  by swapping drawing calls in `renderer.py` — no gameplay logic changes.
- The scripting sandbox (`scripting.py`) is the only file that knows
  which API functions exist; adding a new command (`deploy()`, etc.)
  requires a change in exactly two places there, nothing else.

Type hints, docstrings, and consistent naming throughout. Suitable for
GitHub portfolio, resume showcase, and eventual Steam release.
