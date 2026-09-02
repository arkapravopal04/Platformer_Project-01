"""Segment 2 - narrow ledges and the first vertical lift.

Difficulty: medium. The platforms get noticeably smaller (100-120px, down
from the 160-200px slabs below), so landings have to be aimed rather than
just cleared. The rises stay inside sprint-jump range the whole way, so
nothing here needs a dash - the pressure is precision, not reach.

The one new idea is the steel lift near the top: a vertically-moving
platform (axis='y'). The last ledge sits 90px above the lift's LOWEST
point, which is out of reach from the ledge below it, so the only way up
is to board the lift and ride it. Wait for it, or miss it.

Enters on the left (matching seg_01's exit) and leaves on the right.
"""

# wide enough to cover both the seg_01 hand-off and the seg_05 wrap-around
ENTRY = (300, 530)

# (x, w, h) - h is height above this segment's own floor
p1 = (540, 120, 40)
p2 = (770, 110, 95)
p3 = (1000, 100, 150)

# the lift: oscillates +/-35px vertically, so its top surface sweeps
# between h=160 and h=230
LIFT_X, LIFT_W, LIFT_H = 1160, 110, 195
LIFT_TRAVEL, LIFT_PERIOD = 35, 130

# the payoff ledge - 90px above the lift's lowest point, and only 100px
# above p3 but directly overhead it, so you cannot simply jump up from p3
p4 = (1010, 150, 250)

ENTITIES = [
    {'type': 'platform', 'x': p1[0], 'w': p1[1], 'h': p1[2]},
    {'type': 'platform', 'x': p2[0], 'w': p2[1], 'h': p2[2]},
    {'type': 'platform', 'x': p3[0], 'w': p3[1], 'h': p3[2]},

    {'type': 'moving', 'x': LIFT_X, 'w': LIFT_W, 'h': LIFT_H,
     'axis': 'y', 'travel': LIFT_TRAVEL, 'period': LIFT_PERIOD},

    {'type': 'platform', 'x': p4[0], 'w': p4[1], 'h': p4[2]},

    # spikes eating the near edge of each narrow ledge, so the usable
    # landing strip is only ~70px wide
    {'type': 'hazard', 'x': p2[0] + 4, 'w': 40, 'h': p2[2]},
    {'type': 'hazard', 'x': p3[0] + p3[1] - 44, 'w': 40, 'h': p3[2]},

    # pillar on p1 - blocks a flat sprint straight down the ledge, forcing
    # a hop up onto it before the run at p2
    {'type': 'wall', 'x': p1[0] + p1[1] - 20, 'h': p1[2], 'height': 55},
]

# next segment's floor sits on the payoff ledge
HEIGHT = p4[2]
EXIT = (p4[0], p4[0] + p4[1])
