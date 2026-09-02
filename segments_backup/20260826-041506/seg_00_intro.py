"""Segment format (read this before writing a new one)
--------------------------------------------------------
A segment is a plain module, discovered automatically by tower.py in
filename order (seg_00_..., seg_01_..., seg_02_..., etc.) and stacked
bottom-to-top. They play through once in order, then the tower keeps
going by repeating only the hardest few - the last CYCLE_TAIL of them,
see tower.py. So adding a new, harder file at the end of the alphabetical
order is the entire job of making the climb harder further up.

Every segment module must define:

    HEIGHT   - int. Where the NEXT segment's floor sits, measured above
               this segment's own floor. Set it equal to your topmost
               platform's `h`: the next segment's h=0 then lands exactly
               on this segment's last surface, so its first platform at
               h=40 is a plain 40px hop up. Leaving dead air here instead
               (HEIGHT well above your top platform) makes the seam
               unjumpable - the player can only climb ~95px in one jump.
               `python lint_segments.py` checks this for you.
    ENTITIES - list of spec dicts, each {'type': ..., 'x': ..., 'h': ...,
               ...}. `h` is LOCAL to this segment - height above this
               segment's own floor, not the true ground_y - tower.py
               offsets it by the segment's cumulative base height before
               handing specs to platforms.build_entities(). See
               entities/*.py's from_spec() classmethods for what extra
               fields each type reads ('w' width, 'height', 'axis',
               'travel', 'period', 'damage', ...).

ENTRY/EXIT are optional and purely advisory - the x-range you arrive at
along this segment's own floor, and the x-range you leave from at its
ceiling. Nothing in tower.py enforces them; they exist so that when
you're designing the *next* segment, you know where the player will
actually be standing when it starts. Keep a new segment's ENTRY roughly
overlapping the previous segment's EXIT so the hop between them is
inside jump/dash range, the same way _build_leg's `gap` values already
have to be.

This file is segment 0: the original hand-built obstacle course,
unchanged in shape from when it was the game's only level.
"""

from platforms import _build_leg

SPAWN_X = 320  # matches Player.spawn_pos[0] in player_classes.py

hops0 = [(80, 180, 0), (45, 170, 55), (50, 170, 55), (50, 180, 55)]
leg0, ref, h = _build_leg(SPAWN_X, 1, hops0, 0)

# walk/sprint gap, rises, near RIGHT edge
turn1_gap, turn1_w = 90, 30
turn1_h = h + 55
turn1_x = ref + turn1_gap
turn1 = (turn1_x, turn1_w, turn1_h)

# LEFT, sprint-jump gaps, one level up
hops1 = [(130, 170, 20), (130, 160, 20), (125, 170, 20)]
leg1, ref, h = _build_leg(turn1_x, -1, hops1, turn1_h)

# dash-jump gap, rises, near LEFT edge
turn2_gap, turn2_w = 120, 40
turn2_h = h + 55
turn2_right = ref - turn2_gap
turn2_x = turn2_right - turn2_w
turn2 = (turn2_x, turn2_w, turn2_h)

# RIGHT, dash/sprint-jump mix, higher up
hops2 = [(230, 190, 25), (155, 190, 25)]
leg2, ref, h = _build_leg(turn2_x + turn2_w, 1, hops2, turn2_h)

# dash-jump gap, rises, near RIGHT edge
turn3_gap, turn3_w = 225, 40
turn3_h = h + 55
turn3_x = ref + turn3_gap
turn3 = (turn3_x, turn3_w, turn3_h)

# LEFT, moving platform is its own hop
mp_travel = 45
hops3a = [(205, 190, 25)]
leg3a, ref, h = _build_leg(turn3_x, -1, hops3a, turn3_h)

mp_gap, mp_w = 180, 110
mp_h = h + 25
mp_x = (ref - mp_gap) - mp_w
leg3_moving = (mp_x, mp_w, mp_h)
hops3b = [(145, 190, 25)]
leg3b, ref, h = _build_leg(mp_x - mp_travel, -1, hops3b, mp_h)

# short breather gap, rises, near LEFT edge
turn4_gap, turn4_w = 85, 30
turn4_h = h + 60
turn4_right = ref - turn4_gap
turn4_x = turn4_right - turn4_w
turn4 = (turn4_x, turn4_w, turn4_h)

# RIGHT, dash-jump gap
hops4 = [(295, 200, 30)]
leg4, ref, h = _build_leg(turn4_x + turn4_w, 1, hops4, turn4_h)

# summit platform - this segment's exit; the next segment's floor starts
# directly above it
summit_gap, summit_w = 295, 200
summit_h = h + 40
summit_x = ref + summit_gap
summit = (summit_x, summit_w, summit_h)

static_entries = (
    list(leg0) + [turn1] + list(leg1) + [turn2] + list(leg2) + [turn3]
    + list(leg3a) + list(leg3b) + [turn4] + list(leg4) + [summit]
)

hazard_specs = [
    # (x, width, height_above_ground) - height_above_ground matches the
    # platform the hazard sits on, so it renders flush with that
    # platform's own top surface
    (leg0[1][0] + 10, 40, leg0[1][2]),
    (leg1[1][0] + leg1[1][1] - 50, 40, leg1[1][2]),
    (leg2[0][0] + 10, 40, leg2[0][2]),
    (leg3a[0][0] + leg3a[0][1] - 50, 40, leg3a[0][2]),
    (leg4[0][0] + leg4[0][1] - 50, 40, leg4[0][2]),
]

wall_specs = [
    (turn1_x - 74, turn1_h, 69),
    (turn2_x + turn2_w + 74, turn2_h, 69),
    (turn3_x - 74, turn3_h, 69),
    (turn4_x + turn4_w + 74, turn4_h, 69),
]

ENTITIES = (
    [{'type': 'platform', 'x': x, 'w': w, 'h': hh} for x, w, hh in static_entries]
    + [{'type': 'moving', 'x': leg3_moving[0], 'w': leg3_moving[1], 'h': leg3_moving[2],
        'axis': 'x', 'travel': mp_travel, 'period': 100}]
    + [{'type': 'hazard', 'x': x, 'w': w, 'h': hh} for x, w, hh in hazard_specs]
    + [{'type': 'wall', 'x': x, 'h': hh, 'height': wall_height} for x, hh, wall_height in wall_specs]
)

# the next segment's floor sits exactly on the summit platform's surface
HEIGHT = summit_h
ENTRY = (SPAWN_X - 40, SPAWN_X + 220)
EXIT = (summit_x, summit_x + summit_w)
