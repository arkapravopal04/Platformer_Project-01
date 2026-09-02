"""seg_01_stepping_up - second segment, noticeably harder than seg_00.

Rises now regularly push toward the ~95px max, gaps sit closer to the
sprint limit (a couple lean on a dash), platforms narrow a bit, and a
wall forces one particular platform to actually be used instead of being
sprint-jumped over. Still nothing that requires a frame-perfect dash -
those start later in the cycle.

Check with `python lint_segments.py` after editing.

Rewritten by creative mode (F4 -> E) as a flat spec list.

Rewritten by creative mode (F4 -> E) as a flat spec list.
"""

ENTRY = (660, 810)

ENTITIES = [
    {'type': 'platform', 'x': 660, 'h': 85, 'w': 150},
    {'type': 'platform', 'x': 900, 'h': 170, 'w': 140},
    {'type': 'platform', 'x': 670, 'h': 255, 'w': 130},
    {'type': 'platform', 'x': 430, 'h': 320, 'w': 150},
    {'type': 'platform', 'x': 420, 'h': 410, 'w': 170},
    {'type': 'platform', 'x': 950, 'h': 560, 'w': 130},
    {'type': 'platform', 'x': 700, 'h': 650, 'w': 110},
    {'type': 'platform', 'x': 650, 'h': 800, 'w': 150},
    {'type': 'platform', 'x': 900, 'h': 870, 'w': 130},
    {'type': 'platform', 'x': 650, 'h': 950, 'w': 190},
    {'type': 'moving', 'x': 700, 'h': 490, 'w': 110, 'axis': 'x', 'travel': 70, 'period': 100},
    {'type': 'moving', 'x': 480, 'h': 720, 'w': 110, 'axis': 'y', 'travel': 45, 'period': 110},
    {'type': 'hazard', 'x': 550, 'h': 410, 'w': 32, 'damage': 15},
]

HEIGHT = 950
EXIT = (650, 840)
