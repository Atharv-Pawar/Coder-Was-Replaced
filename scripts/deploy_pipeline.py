# deploy_pipeline.py
# A complete automation pipeline:
#   1. Sweep for bugs and fix them
#   2. Walk to the git repo and commit
#   3. Walk to the server and deploy
#
# Earns XP for fix_bug (+10), commit (+20), deploy (+40)
# and advances "Deploy Day" and "Sprint Complete" missions.
#
# Requires: fix_bug (50 XP), commit (200 XP), deploy (500 XP) unlocked.
# Starting position: top-left area of the office.

BUG_SWEEP_STEPS = 10   # steps to scan before heading to infra

# --- Phase 1: fix nearby bugs ---
for _ in range(BUG_SWEEP_STEPS):
    if look() == BUG:
        fix_bug()
    elif look() == WALL or look() == DESK:
        turn_right()
    else:
        move()

# --- Phase 2: commit to git repo (far right column) ---
# Turn to face right and walk toward the infra corner
turn_right()     # now facing right (assuming we started facing down)
for _ in range(10):
    if look() == GIT:
        commit()
        break
    elif look() == WALL or look() == SERVER:
        turn_left()
        move()
        turn_right()
    else:
        move()

# --- Phase 3: deploy to server rack ---
for _ in range(5):
    if look() == SERVER:
        deploy()
        break
    elif look() == WALL:
        turn_left()
    else:
        move()
