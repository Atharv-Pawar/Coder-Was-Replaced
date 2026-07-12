# deadline_crunch.py
# Optimised for timed missions: "Monday Standup" and "Deadline Crunch".
#
# Uses a helper function to scan in all four directions at each tile
# so no bug gets missed on a single pass.
#
# Requires: fix_bug (50 XP), answer_email (500 XP) unlocked.

DIRECTIONS = 4   # scan all four orientations per tile

def scan_and_act():
    """Check all four faces and act on whatever we find."""
    for _ in range(DIRECTIONS):
        target = look()
        if target == BUG:
            fix_bug()
            return True
        turn_right()
    return False

# Main timed loop — move as fast as possible
steps = 0
bugs_fixed = 0
emails_done = 0

while True:
    acted = scan_and_act()
    if acted:
        bugs_fixed = bugs_fixed + 1
    else:
        # Nothing adjacent — keep moving, bounce off walls
        if look() == WALL or look() == DESK or look() == SERVER:
            turn_right()
        else:
            move()
            steps = steps + 1
