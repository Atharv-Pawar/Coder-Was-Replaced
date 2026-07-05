# Example: Energy-aware bug hunter
# Uses look() to navigate toward known targets and
# manages energy by seeking out the coffee machine.
#
# This is a taste of the kind of logic unlock in Phase 4+
# (energy() and get_position() are not yet available).

bugs_fixed = 0
steps = 0

while True:
    ahead = look()

    if ahead == BUG:
        fix_bug()
        bugs_fixed = bugs_fixed + 1

    elif ahead == COFFEE:
        drink_coffee()

    elif ahead == WALL or ahead == DESK:
        # Can't go forward — try turning right first
        turn_right()

    else:
        move()
        steps = steps + 1
