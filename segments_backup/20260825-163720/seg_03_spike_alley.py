"""Segment 3 - spike alley.

Difficulty: medium-hard. The gaps and rises are ordinary sprint-jump
distances; what makes this one bite is that every ledge is half spikes.
Each platform has a 40px spike bank on the side you arrive from, so you
have to clear the spikes as well as the gap - the effective landing zone
is the far ~60% of each slab, and overshooting is as bad as undershooting.

Walls sit on the two middle ledges to stop a big dash-jump from skipping
a platform entirely and cheesing the whole alley in two hops.

Enters on the right (matching seg_02's exit) and leaves on the left.
"""

ENTRY = (1010, 1160)

# built leftward from the entry ledge; (x, w, h)
p1 = (770, 130, 50)
p2 = (530, 120, 105)
p3 = (280, 140, 160)

ENTITIES = [
    {'type': 'platform', 'x': p1[0], 'w': p1[1], 'h': p1[2]},
    {'type': 'platform', 'x': p2[0], 'w': p2[1], 'h': p2[2]},
    {'type': 'platform', 'x': p3[0], 'w': p3[1], 'h': p3[2]},

    # spikes on the right-hand (arrival) edge of every ledge, since the
    # whole segment travels leftward
    {'type': 'hazard', 'x': p1[0] + p1[1] - 44, 'w': 40, 'h': p1[2]},
    {'type': 'hazard', 'x': p2[0] + p2[1] - 44, 'w': 40, 'h': p2[2]},
    {'type': 'hazard', 'x': p3[0] + p3[1] - 44, 'w': 40, 'h': p3[2]},

    # a second spike bank on the far edge of the middle ledge - this is
    # the one that punishes a too-strong dash-jump
    {'type': 'hazard', 'x': p2[0] + 4, 'w': 36, 'h': p2[2]},

    # pillars that close the "skip a whole ledge" line
    {'type': 'wall', 'x': p1[0] - 30, 'h': p1[2], 'height': 62},
    {'type': 'wall', 'x': p2[0] - 30, 'h': p2[2], 'height': 62},
]

# next segment's floor sits on the topmost ledge
HEIGHT = p3[2]
EXIT = (p3[0], p3[0] + p3[1])
