"""Draft segment saved from creative mode (F4 -> E).

Rename this file to slot it into the difficulty order - as
seg_99 it sorts last and lands in the repeating tail.
Check it with `python lint_segments.py`.

Rewritten by creative mode (F4 -> E) as a flat spec list.
"""

ENTRY = (370, 510)

ENTITIES = [
    {'type': 'platform', 'x': 370, 'h': 40, 'w': 140},
    {'type': 'platform', 'x': 550, 'h': 100, 'w': 140},
    {'type': 'platform', 'x': 780, 'h': 170, 'w': 140},
    {'type': 'platform', 'x': 960, 'h': 250, 'w': 140},
    {'type': 'platform', 'x': 1240, 'h': 280, 'w': 140},
    {'type': 'platform', 'x': 1000, 'h': 370, 'w': 140},
    {'type': 'platform', 'x': 790, 'h': 460, 'w': 140},
    {'type': 'platform', 'x': 570, 'h': 550, 'w': 140},
    {'type': 'platform', 'x': 340, 'h': 640, 'w': 140},
    {'type': 'platform', 'x': 20, 'h': 660, 'w': 140},
    {'type': 'platform', 'x': 770, 'h': 720, 'w': 140},
    {'type': 'platform', 'x': 390, 'h': 750, 'w': 140},
    {'type': 'platform', 'x': 1110, 'h': 810, 'w': 140},
    {'type': 'platform', 'x': 40, 'h': 1070, 'w': 140},
    {'type': 'platform', 'x': 360, 'h': 1160, 'w': 140},
    {'type': 'platform', 'x': 910, 'h': 1330, 'w': 140},
    {'type': 'moving', 'x': 850, 'h': 900, 'w': 120, 'axis': 'x', 'travel': 60, 'period': 120},
    {'type': 'moving', 'x': 600, 'h': 990, 'w': 120, 'axis': 'x', 'travel': 60, 'period': 120},
    {'type': 'moving', 'x': 300, 'h': 1020, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'moving', 'x': 550, 'h': 1160, 'w': 120, 'axis': 'x', 'travel': 60, 'period': 110},
    {'type': 'moving', 'x': 770, 'h': 1220, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
]

HEIGHT = 1330
EXIT = (910, 1050)
