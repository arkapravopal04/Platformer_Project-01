"""Segment 1 - a short leftward zig-zag climb, and the gentlest thing in
the tower. See seg_00_intro.py's module docstring for the segment format.

Difficulty: easy. Three wide ledges, 60px rises, gaps of 120 - all well
inside a plain sprint-jump, no dash needed anywhere. It exists to give
the player a breather right after seg_00's tight summit dash, and to be
the file you copy when you want the simplest possible starting point for
a new segment.

Enters on the right (on top of seg_00's summit) and leaves on the left.
"""

from platforms import _build_leg

ENTRY = (960, 1160)

# (gap, width, rise) per hop, travelling leftward from x=1160
hops = [(60, 170, 45), (120, 160, 60), (120, 170, 60)]
leg, ref, h = _build_leg(1160, -1, hops, 0)

# spikes on the arrival edge of the middle ledge
hazard_x = leg[1][0] + leg[1][1] - 44
# a pillar on the first ledge, so the run at the middle gap has to start
# from on top of it rather than from a flat sprint
wall_x = leg[0][0] - 28

ENTITIES = (
    [{'type': 'platform', 'x': x, 'w': w, 'h': hh} for x, w, hh in leg]
    + [{'type': 'hazard', 'x': hazard_x, 'w': 40, 'h': leg[1][2]}]
    + [{'type': 'wall', 'x': wall_x, 'h': leg[0][2], 'height': 58}]
)

# next segment's floor sits on the topmost ledge
HEIGHT = leg[-1][2]
EXIT = (leg[-1][0], leg[-1][0] + leg[-1][1])
