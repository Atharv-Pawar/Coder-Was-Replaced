# Coder Was Replaced

> You are the last software engineer in a company that has automated
> everything. Instead of writing code yourself, you program an AI coding
> bot to survive office life.

An original automation/idle game inspired by the gameplay mechanics of
*The Farmer Was Replaced*, *Human Resource Machine*, and *shapez* — built
from scratch with Pygame, in clean, testable phases.

## Status: Phase 2 — Office World ✅

Phase 1 built the engine. Phase 2 fills the office with real,
interactable furniture:

- `game/objects.py`: a `GameObject` system (desk, laptop, coffee
  machine, bug, jira ticket, server rack, git repo, wifi router,
  meeting room door), each with its own collision behavior and a
  unique interaction effect
- Combined tilemap + object collision (`Office.is_walkable`) — desks,
  servers, etc. block movement just like walls
- Interaction: face an object and press **E** (or Space). A context
  prompt ("[E] Coffee Machine") appears automatically when in range
- `engine/events.py`: a toast notification queue for feedback
  ("+20 energy (coffee)", "Bug fixed!")
- An energy stat on the robot, restored by the coffee machine, shown
  via an on-screen energy bar
- Objects render as distinct colored shapes/labels for now — same
  swap-in plan as the tilemap once real sprite art exists

## Running it

```bash
pip install -r requirements.txt
python main.py
```

**Controls**

| Key | Action |
|---|---|
| Arrow keys / WASD | Move the robot |
| **E** / Space | Interact with the object you're facing |
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
│   ├── objects.py         # Interactable office furniture (desk, coffee, bug, ...)
│   └── office.py          # Ties map + objects + robot + camera together
├── assets/                # Sprites, tiles, UI, fonts, sounds, music
├── levels/                # Will hold real .tmx maps (Phase 2+)
├── scripts/                # Where player-written automation code will live (Phase 3)
├── data/                  # JSON config (items, upgrades) — Phase 4+
└── tests/                 # Unit tests
```

## Roadmap

| Phase | Focus |
|---|---|
| 1 ✅ | Engine foundation: window, loop, renderer, camera, tilemap, input |
| 2 ✅ | Office world: real objects (desk, coffee, printer, server, AI robot sprite) |
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
