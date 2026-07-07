# Changelog

All notable changes to *Coder Was Replaced* by phase.

---

## Phase 4 — Unlock System ✅

**New files**
- `game/progression.py` — XP engine, level ladder (9 tiers), unlock
  registry (19 functions), XP-to-next-unlock ratio, new-unlock toast

**Changed files**
- `engine/scripting.py` — `ScriptEngine` now accepts a `Progression`
  instance; all dispatched commands check `is_unlocked()` before
  executing and raise a descriptive locked-function error if blocked;
  XP awarded on every successful action; passive +1 XP every 10 moves
- `game/editor.py` — progress panel (62 px) between code area and
  status bar: shows level title, XP progress bar, next-unlock hint;
  `draw()` and `update()` accept `progression` parameter
- `engine/renderer.py` — `draw_level_hud()`: level badge + mini XP bar
  in the game panel top-right (below the energy bar)
- `engine/game.py` — instantiates `Progression`, wires it into
  `ScriptEngine`, `Editor.draw/update`, and `draw_level_hud()`
- `engine/constants.py` — `PROGRESS_PANEL_HEIGHT`, XP bar colors, level
  badge colors, lock/unlock text colors

**Unlock ladder (19 entries)**

| XP | Functions unlocked | Level title |
|---|---|---|
| 0 | `move`, `turn_left`, `turn_right`, `look` | Intern |
| 50 | `fix_bug`, `drink_coffee` | Junior Developer |
| 200 | `commit` | Developer |
| 500 | `deploy`, `answer_email` | Senior Dev |
| 1 000 | `run_tests`, `build_project` | Tech Lead |
| 2 000 | `refactor`, `scan` | Architect |
| 4 000 | `spawn_worker`, `use_ai` | Eng Manager |
| 8 000 | `docker_build`, `optimize` | CTO |
| 15 000 | `train_model`, `kubernetes_scale` | Fully Automated |

**XP sources**

| Action | XP |
|---|---|
| `move()` (every 10 steps) | +1 |
| `fix_bug()` (successful) | +10 |
| `drink_coffee()` | +3 |
| `commit()` | +20 |
| `deploy()` | +40 |
| `run_tests()` | +30 |
| `answer_email()` | +15 |
| `refactor()` | +25 |

**Features shipped**
- Calling a locked function stops the script immediately with a clear
  error: `"fix_bug() is locked  (need 50 XP, you have 12)"`
- New unlocks trigger a toast notification: `"UNLOCKED: fix_bug() -- Fix a bug"`
- Progress panel in the editor shows current level, XP bar toward the
  next unlock, and the next function name + XP gap
- Level badge HUD in game panel shows title + mini XP bar at a glance
- New scriptable actions: `deploy()`, `run_tests()`, `answer_email()`, `refactor()`
- Passive XP income from movement encourages exploration even without
  bugs to fix

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
---

## Phase 5 — Economy ✅

**New files**
- `game/economy.py` — Economy class: 5 currencies, passive salary tick,
  6 shop items with real mechanical upgrade effects

**Changed files**
- `engine/scripting.py` — awards economy currencies on every action;
  `_apply_upgrade_effects()` syncs upgrade effects (move speed, coffee
  restore, look range) to game state each frame; accepts `economy=`
- `game/player.py` — `move_duration` is now an instance variable so
  the Standing Desk upgrade can reduce it at runtime
- `game/editor.py` — Economy panel (60 px, 2-row) below the progression
  panel: salary, rep, git stars, coffee count, compute credits, salary
  tick progress bar, "[TAB] Shop" hint
- `engine/renderer.py` — `draw_shop_overlay()`: full-screen dimmed shop
  overlay with 6 items, affordability-colored costs, OWNED badges
- `engine/game.py` — instantiates Economy; Tab toggles shop; number
  keys 1-6 buy items when shop is open; economy wired into update/draw
- `engine/input.py` — `shop_toggle_pressed()`, `buy_item_index()`
- `engine/constants.py` — economy colors, tick interval, shop palette,
  ECONOMY_PANEL_HEIGHT

**Currencies**

| Icon | Currency | Earned by |
|---|---|---|
| $ | Salary | Passive tick (level-scaled) + task bonuses |
| Rep | Reputation | Fixing bugs, deploying, emails, refactoring |
| ★ | Git Stars | Committing and deploying |
| ☕ | Coffee count | drink_coffee() calls |
| CPU | Compute credits | deploy(), run_tests(), refactor() |

**Shop items (4 active in Phase 5)**

| Item | Cost | Effect |
|---|---|---|
| Better Coffee Machine | $50 | Coffee restores 40 energy (was 20) |
| Standing Desk | $120 | Robot moves 25% faster |
| Mechanical Keyboard | $250 | Script executes 25% faster |
| AI Code Assistant | $600 | look() sees 2 tiles ahead |
| CI/CD Pipeline | $1,200 | (Phase 6 teaser) |
| Cloud Servers | $3,000 | (Phase 6 teaser) |

**Controls added**
- **Tab** — open/close shop overlay
- **1–6** (while shop open) — buy item

