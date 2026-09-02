"""Segment 4 - the long haul.

Difficulty: hard. This is the dash segment. The opening gap is 200px at a
25px rise, which is past what a sprint-jump covers (184px at that rise
inside the comfort margin) - you have to dash it or you drop the whole
segment. There is no spike anywhere here; the entire difficulty is reach
and timing, which makes it read differently from spike alley below it
even though both sit at a similar skill level.

The middle hop is a wide horizontal mover with a long 60px throw. It
closes most of the distance for you at the ends of its travel, so the
segment is generous if you wait and brutal if you jump on sight.

Enters on the left (matching seg_03's exit) and leaves on the right.
"""

ENTRY = (280, 420)

# (x, w, h). p1 is the forced dash-jump
p1 = (620, 140, 25)

# wide horizontal mover - sweeps x from 850 to 970 (its own left edge)
MOVER_X, MOVER_W, MOVER_H = 910, 120, 60
MOVER_TRAVEL, MOVER_PERIOD = 60, 120

p2 = (1240, 140, 105)

ENTITIES = [
    {'type': 'platform', 'x': p1[0], 'w': p1[1], 'h': p1[2]},

    {'type': 'moving', 'x': MOVER_X, 'w': MOVER_W, 'h': MOVER_H,
     'axis': 'x', 'travel': MOVER_TRAVEL, 'period': MOVER_PERIOD},

    {'type': 'platform', 'x': p2[0], 'w': p2[1], 'h': p2[2]},

    # a pillar on the launch ledge, set back from its right edge, so the
    # run-up into the opening dash has to start from a standstill on top
    # of it rather than from a full-speed sprint across the whole ledge
    {'type': 'wall', 'x': p1[0] + 30, 'h': p1[2], 'height': 58},
]

# next segment's floor sits on the topmost ledge
HEIGHT = p2[2]
EXIT = (p2[0], p2[0] + p2[1])
