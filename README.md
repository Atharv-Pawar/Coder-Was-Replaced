# Coder Was Replaced

> You are the last software engineer in a company that has automated everything.
> Instead of writing code yourself, you program an AI coding bot to survive office life.

An original automation/idle game inspired by *The Farmer Was Replaced* and *Human Resource Machine*, built from scratch in Python + Pygame.

---

## Status: Phase 7 — AI Employees ✅

Phases 1–7 complete, running at 60 FPS on Windows / Linux / macOS.

---

## Running it

```bash
pip install -r requirements.txt
python main.py
```

**Requires:** Python 3.12+ and pygame-ce ≥ 2.5.0

---

## Controls

| Key | Action |
|---|---|
| Arrow keys / WASD | Move robot manually |
| **E** / Space | Interact with object you're facing |
| **F5** / Run button | Execute your script |
| **F6** / Stop button | Stop execution |
| **TAB** | Open / close shop |
| **1–6** (shop open) | Buy item |
| `<` `>` buttons | Adjust execution speed |
| **F3** | Toggle debug overlay |
| **Esc** | Quit |

---

## Script API

Write Python in the left panel. The robot executes each command live with smooth animations.

```python
# Movement
move()          # step forward (direction = robot's current facing)
turn_left()     # rotate 90° counter-clockwise
turn_right()    # rotate 90° clockwise

# Sensing
look()          # returns what's directly ahead: EMPTY / WALL / BUG / COFFEE / ...

# Actions (unlocked progressively with XP)
fix_bug()       # fix the bug you're facing          (+10 XP, +$5)
drink_coffee()  # use the coffee machine             (+3 XP)
commit()        # commit to the git repo             (+20 XP, +$3, +1 Star)
deploy()        # deploy to the server rack          (+40 XP, +$20, +3 Stars)
run_tests()     # run the test suite                 (+30 XP, +$5)
answer_email()  # clear the inbox                   (+15 XP, +$8)
refactor()      # refactor code                     (+25 XP, +$10)
```

### World constants
`EMPTY`  `WALL`  `BUG`  `COFFEE`  `DESK`  `SERVER`  `JIRA`  `GIT`  `WIFI`  `MEETING`  `LAPTOP`

### Example scripts

```python
# Patrol loop — fixes bugs and refuels automatically
while True:
    if look() == BUG:
        fix_bug()
    elif look() == COFFEE:
        drink_coffee()
    elif look() == WALL:
        turn_right()
    else:
        move()
```

```python
# Grid sweep — covers every tile systematically
for row in range(12):
    for col in range(22):
        if look() == BUG:
            fix_bug()
        if col < 21:
            move()
    if row < 11:
        if row % 2 == 0:
            turn_right(); move(); turn_right()
        else:
            turn_left(); move(); turn_left()
```

---

## Unlock system

Functions are gated behind XP thresholds earned by doing real work:

| XP | Unlocks | Level |
|---|---|---|
| 0 | `move` `turn_left` `turn_right` `look` | Intern |
| 50 | `fix_bug` `drink_coffee` | Junior Developer |
| 200 | `commit` | Developer |
| 500 | `deploy` `answer_email` | Senior Dev |
| 1 000 | `run_tests` `build_project` | Tech Lead |
| 2 000 | `refactor` `scan` | Architect |
| 4 000 | `spawn_worker` `use_ai` | Eng Manager |
| 8 000 | `docker_build` `optimize` | CTO |
| 15 000 | `train_model` `kubernetes_scale` | Fully Automated |

---

## Economy & Shop

Earn five currencies through scripted actions:

| Currency | Earned by |
|---|---|
| **$ Salary** | Passive ticks (level-scaled) + task bonuses |
| **Rep** | Fixing bugs, deploying, emails |
| **Stars** | Committing and deploying |
| **Coffee** | `drink_coffee()` calls |
| **CPU Credits** | `deploy()`, `run_tests()`, `refactor()` |

Spend salary in the **Shop (TAB)**:

| Upgrade | Cost | Effect |
|---|---|---|
| Better Coffee Machine | $50 | +40 energy per coffee (was 20) |
| Standing Desk | $120 | Robot moves 25% faster |
| Mechanical Keyboard | $250 | Script executes 25% faster |
| AI Code Assistant | $600 | `look()` sees 2 tiles ahead |

---

## Missions

Structured objectives that tie everything together. Active mission shown bottom-right of the game view. Progress auto-updates as your script runs.

**10 missions across 3 tiers:**

| Mission | Objectives | Timed? |
|---|---|---|
| First Steps | Move 20 tiles | No |
| Coffee Run | Drink coffee ×2 | No |
| Bug Hunt | Fix 3 bugs | No |
| Commit Streak | Git commit ×3 | No |
| Debug Session | Fix 5 bugs + commit | No |
| Inbox Zero | Answer 3 emails | No |
| Monday Standup | 3 emails + stay active | **75s** |
| Deploy Day | Fix 2 + commit 2 + deploy | No |
| Deadline Crunch | Fix 5 bugs + deploy | **120s** |
| Sprint Complete | Fix 4 + commit 3 + test + deploy | No |

Missions cycle with targets scaling +50% per full cycle. Completing earns XP, salary, reputation, and git stars. Failing a timed mission costs 3 Rep.

---

## Project structure

```
CWR/
├── main.py
├── engine/
│   ├── constants.py     all tunable values
│   ├── game.py          main loop + wiring
│   ├── renderer.py      all draw calls
│   ├── camera.py        smoothed camera, split-screen offset
│   ├── tilemap.py       grid map + collision
│   ├── animation.py     Vec2Tween easing
│   ├── input.py         keyboard/mouse
│   ├── events.py        toast notification queue
│   └── scripting.py     thread-based Python execution engine
├── game/
│   ├── player.py        robot entity
│   ├── objects.py       9 office object types
│   ├── office.py        tilemap + objects + camera
│   ├── editor.py        split-screen code editor
│   ├── progression.py   XP, levels, unlock registry
│   ├── economy.py       currencies, passive income, shop
│   └── missions.py      10-mission catalog + tracker
├── scripts/             example scripts
└── data/                future JSON config
```

---

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| 1 | Engine: window, loop, renderer, camera, tilemap, input | ✅ |
| 2 | Office world: objects, collision, interaction, HUD | ✅ |
| 3 | Scripting engine: editor, syntax highlighting, execution | ✅ |
| 4 | Unlock system: XP gating, level ladder, progress panel | ✅ |
| 5 | Economy: currencies, passive income, shop, upgrades | ✅ |
| 6 | Missions: 10 objectives, timed missions, rewards | ✅ |
| 7 | AI employees: hire interns → architects, each with own thread | ✅ |
| 8 | Procedural offices + real Tiled `.tmx` maps | 🔜 Next |
| 9 | Polish: audio, achievements, settings, packaging | ⏳ |
