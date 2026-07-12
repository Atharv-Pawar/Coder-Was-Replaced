# grid_sweep.py
# Sweeps the whole office in a snake (boustrophedon) pattern.
# Finds every bug systematically.
#
# Covers a 22×12 region — adjust COLS/ROWS if the map changes.
# Useful for "Debug Session" and "Sprint Complete" missions.

COLS = 22
ROWS = 12

for row in range(ROWS):
    for col in range(COLS):
        if look() == BUG:
            fix_bug()
        if col < COLS - 1:
            move()

    # End of each row: step down one tile and reverse direction
    if row < ROWS - 1:
        if row % 2 == 0:
            turn_right()
            move()
            turn_right()
        else:
            turn_left()
            move()
            turn_left()
