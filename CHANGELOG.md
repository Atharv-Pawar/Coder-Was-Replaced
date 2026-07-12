# Changelog

---

## Phase 6 — Missions ✅

**New files**
- `game/missions.py` — `Objective`, `Mission`, `MissionTracker`, 10-mission catalog, cycle scaling

**Changed files**
- `engine/scripting.py` — `_notify_mission(action)` called after every successful command; `mission_tracker` constructor param
- `engine/renderer.py` — `draw_mission_hud()` (bottom-right HUD box with objectives + progress bars + timer + reward preview); `draw_mission_complete_overlay()` (full-screen completion/fail banner, fades over 4 s)
- `engine/game.py` — instantiates `MissionTracker`; calls `missions.update(dt)` each frame; draws mission HUD and overlay
- `engine/constants.py` — mission palette: `COLOR_MISSION_*`, `COLOR_COMPLETE_*`, `COLOR_FAIL_*`, `MISSION_HUD_W`, `MISSION_HUD_MARGIN`
- `scripts/` — four example scripts added: `patrol.py`, `grid_sweep.py`, `deploy_pipeline.py`, `deadline_crunch.py`

**Missions (10 total, 3 tiers)**

| Tier | Mission | Objectives | Timed? |
|---|---|---|---|
| 0 Intern | First Steps | Move 20 tiles | No |
| 0 Intern | Coffee Run | Drink coffee ×2 | No |
| 0 Intern | Bug Hunt | Fix 3 bugs | No |
| 1 Junior | Commit Streak | Git commit ×3 | No |
| 1 Junior | Debug Session | Fix 5 + commit 1 | No |
| 1 Junior | Inbox Zero | Answer 3 emails | No |
| 1 Junior | Monday Standup | 3 emails + move 10 | **75 s** |
| 2 Senior | Deploy Day | Fix 2 + commit 2 + deploy 1 | No |
| 2 Senior | Deadline Crunch | Fix 5 + deploy 1 | **120 s** |
| 3 Tech Lead | Sprint Complete | Fix 4 + commit 3 + test + deploy | No |

**Mission mechanics**
- Missions cycle: when all available missions are done once, cycle increments and targets scale +50%
- Rewards scale +30% per cycle (salary, XP, reputation, git stars)
- Timed missions show a countdown timer in the HUD, turning orange below 50% and red below 25%
- Completing a mission shows a 4-second "MISSION COMPLETE" banner with reward breakdown
- Failing a timed mission shows "MISSION FAILED", costs 3 Reputation, loads the next mission
- New missions auto-unlock as `Progression.level_index` rises (tier-gated)

---

## Phase 5 — Economy ✅

**New files**
- `game/economy.py` — 5 currencies, passive salary tick, 6 shop items, upgrade effects

**Features**
- Currencies: Salary ($), Reputation, Git Stars, Coffee count, Compute Credits
- Passive salary tick every 8 s, rate scales with level (Intern $1 → CTO $60)
- Shop (TAB): 4 active upgrades with real mechanical effects
  - Better Coffee Machine $50 → +40 energy
  - Standing Desk $120 → 25% faster movement
  - Mechanical Keyboard $250 → 25% faster script execution
  - AI Assistant $600 → `look()` sees 2 tiles ahead
- Economy panel in editor (2-row): all currencies + salary tick bar

---

## Phase 4 — Unlock System ✅

**New files**
- `game/progression.py` — XP engine, 9-level ladder, 19-entry unlock registry

**Features**
- Calling a locked function stops the script with a clear error message
- New unlocks trigger a toast notification
- Progress panel in editor: level title, XP bar, next-unlock hint
- Level badge HUD in game panel

---

## Phase 3 — Python Scripting Engine ✅

**New files**
- `engine/scripting.py` — thread-based Python executor with sandbox, `sys.settrace` line tracking
- `game/editor.py` — split-screen code editor with syntax highlighting, cursor, line numbers, run/stop buttons

**Features**
- Split-screen: 490 px editor left, 790 px game right
- 6-token syntax highlighting (keywords, engine API, constants, strings, comments, numbers)
- Live line highlighting via `sys.settrace`
- Speed control: 0.5× / 0.75× / 1× / 2×
- Auto-indent on Enter; click-to-place cursor; Ctrl+Backspace word-delete
- Safe sandbox: no `__import__`, no file I/O

---

## Phase 2 — Office World ✅

**New files**
- `engine/events.py` — toast notification queue
- `game/objects.py` — 9 interactable object types

**Features**
- Objects block movement like walls
- `[E]` context prompt when facing an interactable
- Energy bar, coffee restores energy, bugs consumed on fix

---

## Phase 1 — Engine Foundation ✅

**Features**
- 60 FPS fixed-timestep game loop
- Logical-resolution renderer (1280×720), scales to any window
- Procedural placeholder tilemap with collision
- Smooth tile-to-tile movement with ease-out-quad tween
- Exponential-smoothing camera, bounded to map
- Arrow keys / WASD movement; F3 debug overlay; Esc quit
