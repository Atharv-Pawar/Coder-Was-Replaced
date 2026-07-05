# Example: Grid sweep
# Sweeps every reachable tile in a boustrophedon (snake) pattern.
# Useful for finding all bugs in a region systematically.

COLS = 22
ROWS = 12

for row in range(ROWS):
    for col in range(COLS):
        if look() == BUG:
            fix_bug()
        if col < COLS - 1:
            move()

    # At the end of each row: turn, step, turn to go the other way
    if row < ROWS - 1:
        if row % 2 == 0:
            turn_right()
            move()
            turn_right()
        else:
            turn_left()
            move()
            turn_left()
