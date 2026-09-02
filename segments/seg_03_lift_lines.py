"""seg_03_lift_lines - fourth segment: wall-jumps across a wide zig-zag.

"Wall-jump" here means what the engine actually supports (see
entities/wall.py - purely a horizontal blocker, never landable, no effect
on vertical movement, no wall-jump mechanic to bounce off of): a wall
sits right at the take-off edge of almost every platform, so clearing it
means an actual jump arc up and over rather than a flat sprint through.
Combined with alternating left/right placement, that turns the climb into
a wide zig-zag across the region instead of a straight line up the
middle - each leg reverses direction, and a couple of vertical lifts are
folded into the crossing itself rather than treated as separate set-pieces.

Check with `python lint_segments.py` after editing.

Rewritten by creative mode (F4 -> E) as a flat spec list.

Rewritten by creative mode (F4 -> E) as a flat spec list.

Rewritten by creative mode (F4 -> E) as a flat spec list.
"""

ENTRY = (540, 690)

ENTITIES = [
    {'type': 'platform', 'x': 540, 'h': 80, 'w': 150},
    {'type': 'platform', 'x': 900, 'h': 160, 'w': 140},
    {'type': 'platform', 'x': 630, 'h': 245, 'w': 140},
    {'type': 'platform', 'x': 970, 'h': 330, 'w': 130},
    {'type': 'platform', 'x': 980, 'h': 500, 'w': 130},
    {'type': 'platform', 'x': 620, 'h': 580, 'w': 130},
    {'type': 'platform', 'x': 600, 'h': 745, 'w': 130},
    {'type': 'platform', 'x': 700, 'h': 830, 'w': 190},
    {'type': 'moving', 'x': 710, 'h': 140, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'moving', 'x': 1130, 'h': 220, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'moving', 'x': 1180, 'h': 420, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'moving', 'x': 850, 'h': 570, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'moving', 'x': 470, 'h': 610, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'moving', 'x': 300, 'h': 670, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'moving', 'x': 470, 'h': 790, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'wall', 'x': 674, 'h': 80, 'w': 16, 'height': 90},
    {'type': 'wall', 'x': 900, 'h': 160, 'w': 16, 'height': 90},
    {'type': 'wall', 'x': 614, 'h': 245, 'w': 16, 'height': 90},
    {'type': 'wall', 'x': 970, 'h': 330, 'w': 16, 'height': 90},
    {'type': 'wall', 'x': 980, 'h': 500, 'w': 16, 'height': 90},
    {'type': 'wall', 'x': 584, 'h': 745, 'w': 16, 'height': 90},
    {'type': 'hazard', 'x': 1060, 'h': 500, 'w': 32, 'damage': 15},
    {'type': 'hazard', 'x': 660, 'h': 745, 'w': 32, 'damage': 15},
]

HEIGHT = 830
EXIT = (700, 890)
