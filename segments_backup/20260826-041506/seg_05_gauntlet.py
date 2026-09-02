"""Segment 5 - the gauntlet. Currently the hardest segment authored, and
the last one, so this is what the tower cycles on forever once the run
gets high enough (see CYCLE_TAIL in tower.py).

Difficulty: hard. Everything at once - two forced dash-jumps onto small
100-110px ledges, spikes on both of them, and a vertical lift you have to
board to finish, all travelling leftward. The two opening gaps (200 and
190) are both past sprint range for their rises, so this segment cannot
be done without the dash coming off cooldown twice on the way up.

Enters on the right (matching seg_04's exit) and exits on the left,
landing inside seg_02's entry band so the CYCLE_TAIL wrap back to
seg_02 is a clean hop rather than a leap of faith.
"""

ENTRY = (1240, 1380)

# (x, w, h) - both of these need a dash to reach
p1 = (930, 110, 30)
p2 = (640, 100, 85)

# the finishing lift: top surface sweeps between h=95 and h=185
LIFT_X, LIFT_W, LIFT_H = 450, 110, 140
LIFT_TRAVEL, LIFT_PERIOD = 45, 110

# the exit ledge, 75px above the lift's lowest point
p3 = (230, 150, 170)

ENTITIES = [
    {'type': 'platform', 'x': p1[0], 'w': p1[1], 'h': p1[2]},
    {'type': 'platform', 'x': p2[0], 'w': p2[1], 'h': p2[2]},

    {'type': 'moving', 'x': LIFT_X, 'w': LIFT_W, 'h': LIFT_H,
     'axis': 'y', 'travel': LIFT_TRAVEL, 'period': LIFT_PERIOD},

    {'type': 'platform', 'x': p3[0], 'w': p3[1], 'h': p3[2]},

    # spikes on the arrival edge of both dash ledges - landing a 190px
    # dash-jump is not enough, it has to be landed past the spikes
    {'type': 'hazard', 'x': p1[0] + p1[1] - 42, 'w': 38, 'h': p1[2]},
    {'type': 'hazard', 'x': p2[0] + p2[1] - 42, 'w': 38, 'h': p2[2]},

    # and one on the exit ledge's far side, so overshooting the dismount
    # off the lift still costs you
    {'type': 'hazard', 'x': p3[0] + 4, 'w': 38, 'h': p3[2]},

    # pillar on the second ledge, closing the line that would let a single
    # huge dash-jump skip the lift entirely
    {'type': 'wall', 'x': p2[0] - 28, 'h': p2[2], 'height': 64},
]

# next segment's floor sits on the exit ledge
HEIGHT = p3[2]
EXIT = (p3[0], p3[0] + p3[1])
