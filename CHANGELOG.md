# Changelog

All notable changes to *Coder Was Replaced* by phase.

---

## Phase 3 — Python Scripting Engine ✅

**New files**
- `engine/scripting.py` — thread-based execution engine with Python sandbox
- `game/editor.py` — full split-screen code editor drawn in pygame

**Changed files**
- `engine/game.py` — wires editor + scripting engine into the main loop;
  F5 runs, F6 stops, speed buttons adjust execution rate
- `engine/camera.py` — added `viewport_x` offset so the camera renders
  correctly inside the right-hand game panel
- `engine/renderer.py` — clip rect for game panel; `draw_debug_overlay`
  accepts `x_offset`; toast and energy bar positions use `GAME_VIEWPORT_*`
- `engine/constants.py` — editor layout, syntax highlight colors, button
  colors, speed/timing constants
- `game/office.py` — uses split-screen camera; `draw()` wrapped in
  `begin_world_draw()` / `end_world_draw()` clip calls

**Features shipped**
- Split-screen layout: 490 px editor left, 790 px game right
- Syntax highlighting: keywords, engine API, world constants, strings,
  comments, numbers — six distinct token types
- Live line highlighting: the currently-executing source line is tinted
  while the script runs, powered by `sys.settrace()`
- Step-by-step visual execution via producer/consumer threading model —
  script thread blocks on `_cmd_done` event until each animation completes
- Run [F5] / Stop [F6] buttons; keyboard shortcuts match
- Execution speed control: 0.5× / 0.75× / 1× / 2×
- Status bar: shows current line number while running, error details on crash
- Auto-indent on Enter (matches leading whitespace + 4 spaces after `:`)
- Ctrl+Backspace word-delete; click-to-place-cursor
- Syntax error caught before thread launch (no zombie threads)
- Safe Python sandbox: no `__import__`, no file I/O, restricted `__builtins__`
- Default starter script demonstrating `look()`, `fix_bug()`, `drink_coffee()`
- Script API: `move()`, `turn_left()`, `turn_right()`, `look()`,
  `fix_bug()`, `drink_coffee()`, `commit()`
- World constants in sandbox: `EMPTY`, `WALL`, `BUG`, `COFFEE`, `DESK`,
  `SERVER`, `JIRA`, `GIT`, `WIFI`, `MEETING`, `LAPTOP`

---

## Phase 2 — Office World ✅

**New files**
- `engine/events.py` — toast notification queue with fade-in/out
- `game/objects.py` — `GameObject` system with 9 object types

**Changed files**
- `game/office.py` — places 29 objects, combined tilemap+object collision,
  interaction dispatch, `[E]` prompt rendering
- `game/player.py` — `try_move` takes a generic `is_walkable` callable;
  added `facing_tile`, `energy_ratio` properties
- `engine/renderer.py` — `draw_object`, `draw_interaction_prompt`,
  `draw_toasts`, `draw_energy_bar`
- `engine/input.py` — added `interact_pressed()`
- `engine/constants.py` — object colors, energy constants, toast timing
- `engine/tilemap.py` — removed baked-in desk tiles (now real objects)

**Features shipped**
- 9 interactable object types: desk, laptop, coffee machine, bug (diamond),
  jira ticket, server rack, git repo, wifi router, meeting room door
- Object collision: solid objects block the robot just like walls
- Context prompt "[E] Object Name" appears when facing an interactable
- Coffee machine restores +20 energy, capped at 100
- Bugs vanish on interact (`consumed = True`)
- Energy bar, top-right of game panel
- Toast notifications for all interactions

---

## Phase 1 — Engine Foundation ✅

**New files** (entire project scaffolded)
- `main.py`, `engine/game.py`, `engine/renderer.py`, `engine/camera.py`,
  `engine/tilemap.py`, `engine/animation.py`, `engine/input.py`,
  `engine/constants.py`, `game/player.py`, `game/office.py`

**Features shipped**
- 60 FPS fixed-timestep game loop, decoupled from rendering
- Logical-resolution renderer (1280×720) scales to any window size
- Procedural placeholder office tilemap with collision
- Smooth tile-to-tile robot movement with ease-out-quad tween
- Exponential-smoothing camera, bounded to map edges
- Arrow key / WASD movement; F3 debug overlay; Esc quit
- Debug overlay: FPS, tile position, facing, movement state
