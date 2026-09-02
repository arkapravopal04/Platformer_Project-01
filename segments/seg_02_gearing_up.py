"""seg_02_gearing_up - third segment, harder again, movers everywhere.

Where seg_01 introduced two movers as occasional set-pieces, this segment
leans on them as the default way up: five movers on mixed axes and
tighter periods, with plain platforms mostly relegated to anchor points
between them. Rises keep pushing toward the max and a couple of the
mover-to-mover gaps only work because the mover's travel is credited on
top of a sprint jump - still no gap that needs a dash on its own.

Check with `python lint_segments.py` after editing.
"""

ENTRY = (650, 820)

ENTITIES = [
    # -- anchor off the seg_01 landing, straight into a fast mover ------
    {'type': 'platform', 'x': 660, 'h': 80, 'w': 150},
    {'type': 'moving', 'x': 880, 'h': 165, 'w': 110, 'axis': 'x',
     'travel': 65, 'period': 95},

    {'type': 'platform', 'x': 660, 'h': 250, 'w': 130},

    # -- a lift straight up, then a fast horizontal hop off its top -----
    {'type': 'moving', 'x': 700, 'h': 330, 'w': 110, 'axis': 'y',
     'travel': 50, 'period': 105},
    {'type': 'platform', 'x': 460, 'h': 400, 'w': 130},

    # -- hazard on the anchor before the two-mover crossing -------------
    {'type': 'hazard', 'x': 560, 'h': 400, 'w': 32, 'damage': 15},
    {'type': 'moving', 'x': 650, 'h': 470, 'w': 100, 'axis': 'x',
     'travel': 60, 'period': 90},
    {'type': 'moving', 'x': 880, 'h': 545, 'w': 100, 'axis': 'x',
     'travel': 60, 'period': 90},

    {'type': 'platform', 'x': 650, 'h': 620, 'w': 140},

    # -- vertical lift with a short travel, near-max rise on exit -------
    {'type': 'moving', 'x': 460, 'h': 695, 'w': 110, 'axis': 'y',
     'travel': 40, 'period': 115},
    {'type': 'platform', 'x': 650, 'h': 770, 'w': 130},

    # -- wall keeps the last mover from just being sprint-jumped past ---
    {'type': 'wall', 'x': 838, 'h': 770, 'w': 16, 'height': 90},
    {'type': 'moving', 'x': 900, 'h': 840, 'w': 100, 'axis': 'x',
     'travel': 55, 'period': 100},

    {'type': 'platform', 'x': 650, 'h': 910, 'w': 130},
    {'type': 'platform', 'x': 540, 'h': 990, 'w': 200},
]

HEIGHT = 990
EXIT = (540, 740)
