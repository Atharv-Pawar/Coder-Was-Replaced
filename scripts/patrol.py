# patrol.py
# The robot walks forward, fixes bugs, refuels at the coffee machine,
# and turns 180° when it hits a wall — indefinitely.
#
# Good starter script for "First Steps" and "Bug Hunt" missions.

while True:
    ahead = look()

    if ahead == BUG:
        fix_bug()
    elif ahead == COFFEE:
        drink_coffee()
    elif ahead == WALL or ahead == DESK:
        turn_right()
        turn_right()      # 180° turn
    else:
        move()
