# Example: Patrol and maintain
# The robot walks in a straight line, fixing bugs and
# recharging at the coffee machine automatically.

while True:
    if look() == BUG:
        fix_bug()
    elif look() == COFFEE:
        drink_coffee()
    elif look() == WALL:
        turn_right()
        turn_right()   # 180 degree turn
    move()
