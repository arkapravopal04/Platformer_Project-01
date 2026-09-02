"""seg_00_first_steps - the tower's opening segment.

Easiest segment in the cycle (segments play through in filename order, so
this is the player's very first climb). Wide platforms, small rises, one
gentle horizontal mover introduced only after a few plain jumps, and a
single low-damage hazard so the player learns to watch for spikes without
real risk of dying to one. No dash-jumps required anywhere in here.

Check with `python lint_segments.py` after editing.
"""

ENTRY = (620, 780)

ENTITIES = [
    # -- warm-up: short, wide hops straight up the middle --------------
    {'type': 'platform', 'x': 620, 'h': 90, 'w': 180},
    {'type': 'platform', 'x': 420, 'h': 170, 'w': 180},
    {'type': 'platform', 'x': 660, 'h': 250, 'w': 180},

    # -- widen out a bit, still all plain walk/sprint jumps -------------
    {'type': 'platform', 'x': 900, 'h': 330, 'w': 160},
    {'type': 'platform', 'x': 680, 'h': 410, 'w': 160},
    {'type': 'platform', 'x': 420, 'h': 470, 'w': 160},

    # -- a spike patch on a wide, otherwise-safe landing ----------------
    {'type': 'platform', 'x': 620, 'h': 550, 'w': 220},
    {'type': 'hazard', 'x': 700, 'h': 550, 'w': 32, 'damage': 10},

    # -- first mover: short, slow, easy to time -------------------------
    {'type': 'moving', 'x': 380, 'h': 630, 'w': 140, 'axis': 'x',
     'travel': 50, 'period': 150},

    {'type': 'platform', 'x': 700, 'h': 700, 'w': 160},

    # -- second mover, this time a gentle lift up the last stretch ------
    {'type': 'moving', 'x': 500, 'h': 770, 'w': 130, 'axis': 'y',
     'travel': 35, 'period': 160},

    {'type': 'platform', 'x': 620, 'h': 850, 'w': 200},
]

HEIGHT = 850
EXIT = (620, 820)
