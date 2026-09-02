"""seg_04_dash_line - fifth segment: the cycle's first real dash-jumps.

Everything so far (seg_00-seg_03) stayed within sprint range or a
comfortable dash. This is the first segment that leans on the dash as a
required tool rather than a comfort margin: a couple of gaps only close
with sprint+dash, one mover-to-mover crossing has no static platform
between the two movers at all, and walls keep reappearing to stop the
now-longer dash reach from skipping the intended step.

Once a 5th segment exists, CYCLE_TAIL=4 drops seg_00 out of the repeating
tail (see tower.py) - this is meant to sit at the harder end of that
tail, not to be anyone's first climb.

Check with `python lint_segments.py` after editing.

Rewritten by creative mode (F4 -> E) as a flat spec list.

Rewritten by creative mode (F4 -> E) as a flat spec list.

Rewritten by creative mode (F4 -> E) as a flat spec list.

Rewritten by creative mode (F4 -> E) as a flat spec list.
"""

ENTRY = (700, 850)

ENTITIES = [
    {'type': 'platform', 'x': 700, 'h': 80, 'w': 150},
    {'type': 'platform', 'x': 1050, 'h': 480, 'w': 130},
    {'type': 'platform', 'x': 460, 'h': 650, 'w': 130},
    {'type': 'platform', 'x': 780, 'h': 730, 'w': 120},
    {'type': 'platform', 'x': 750, 'h': 890, 'w': 190},
    {'type': 'moving', 'x': 550, 'h': 170, 'w': 120, 'axis': 'x', 'travel': 60, 'period': 110},
    {'type': 'moving', 'x': 750, 'h': 240, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'moving', 'x': 780, 'h': 330, 'w': 110, 'axis': 'x', 'travel': 70, 'period': 90},
    {'type': 'moving', 'x': 1050, 'h': 400, 'w': 100, 'axis': 'x', 'travel': 65, 'period': 85},
    {'type': 'moving', 'x': 760, 'h': 565, 'w': 110, 'axis': 'y', 'travel': 55, 'period': 90},
    {'type': 'moving', 'x': 950, 'h': 810, 'w': 100, 'axis': 'x', 'travel': 60, 'period': 90},
    {'type': 'wall', 'x': 834, 'h': 80, 'w': 16, 'height': 90},
    {'type': 'wall', 'x': 444, 'h': 650, 'w': 16, 'height': 90},
    {'type': 'hazard', 'x': 790, 'h': 80, 'w': 40},
]

HEIGHT = 890
EXIT = (750, 940)
