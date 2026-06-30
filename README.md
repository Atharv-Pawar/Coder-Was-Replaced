# Coder Was Replaced

> You are the last software engineer in a company that has automated
> everything. Instead of writing code yourself, you program an AI coding
> bot to survive office life.

An original automation/idle game inspired by the gameplay mechanics of
*The Farmer Was Replaced*, *Human Resource Machine*, and *shapez* — built
from scratch with Pygame, in clean, testable phases.

## Status: Phase 1 — Engine Foundation ✅

This milestone establishes the core engine that every later feature
builds on:

- Fixed-timestep game loop at 60 FPS, decoupled from rendering
- Logical-resolution renderer that scales cleanly to any window size
- Grid-based tilemap with collision (`engine/tilemap.py`) — currently a
  procedural placeholder office; will be swapped for real Tiled (`.tmx`)
  maps via `pytmx` once art assets exist
- Smooth tile-to-tile movement with easing (`engine/animation.py`)
- Camera that follows the player with smoothing and clamps to map bounds
- Keyboard input manager (arrow keys / WASD to move, F3 debug overlay,
  Esc to quit)
- On-screen debug overlay (FPS, tile position, facing, movement state)

## Running it

```bash
pip install -r requirements.txt
python main.py
```

**Controls**

| Key | Action |
|---|---|
| Arrow keys / WASD | Move the robot |
| F3 | Toggle debug overlay |
| Esc | Quit |

## Project structure

```
Coder-Was-Replaced/
├── main.py                # Entry point
├── engine/                # Engine: rendering, camera, animation, input
│   ├── game.py            # Main loop
│   ├── renderer.py        # Window + drawing
│   ├── camera.py          # Smoothed, bounded camera
│   ├── tilemap.py         # Grid map + collision (placeholder content)
│   ├── animation.py       # Tweening / easing helpers
│   ├── input.py           # Keyboard input manager
│   └── constants.py       # All tunable values live here
├── game/                  # Game-specific content
│   ├── player.py          # The AI robot entity
│   └── office.py          # Ties map + robot + camera together
├── assets/                # Sprites, tiles, UI, fonts, sounds, music
├── levels/                # Will hold real .tmx maps (Phase 2+)
├── scripts/               # Where player-written automation code will live (Phase 3)
├── data/                  # JSON config (items, upgrades) — Phase 4+
└── tests/                 # Unit tests
```

## Roadmap

| Phase | Focus |
|---|---|
| 1 ✅ | Engine foundation: window, loop, renderer, camera, tilemap, input |
| 2 | Office world: real objects (desk, coffee, printer, server, AI robot sprite) |
| 3 | Python scripting engine: write code, watch the robot execute it step by step |
| 4 | Unlock system for functions (`fix_bug()`, `commit()`, `deploy()`, ...) |
| 5 | Economy: salary, experience, reputation, coffee, compute credits, git stars |
| 6 | Missions (fix bugs, deploy, close tickets, merge PRs, survive Monday) |
| 7 | AI employees you can hire and assign scripts to |
| 8 | Procedural office generation |
| 9 | Steam polish: achievements, settings, audio, music, controller support |

## Design philosophy

Built in clean phases, each fully playable before moving to the next —
the way a small indie studio would build it, rather than as one giant
script. Type hints and docstrings throughout; engine code (`engine/`) is
kept independent of game-specific rules (`game/`) so systems stay
testable and swappable (e.g. the placeholder tilemap can be replaced by
real Tiled maps without touching the renderer or camera).
