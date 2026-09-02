"""seg_05_collapse_gauntlet - sixth segment: the tower's first trapdoors,
and by design the most damaging stretch built so far.

Everything earlier (seg_00-seg_04) reappears here at once - dash-forcing
walls, mixed-axis movers, hazards - but the new hazard is the trapdoor
(entities/trapdoor.py): it behaves like a normal platform for as long as
you keep moving, but stand on one for more than ~0.75s (it visibly shakes
first) and it swings open, dropping you into the spike bed underneath.
Sprinting across a run of them is safe; landing on one after a fumbled
jump and pausing to get your bearings is exactly the moment it gives way.
That's the intended failure mode this segment is tuned around - it should
eat more attempts than anything before it.

There are two trapdoor stretches:
  - a short, flush BRIDGE (~h 250) - a row of trapdoors placed edge to
    edge over a spike pit. Walking straight across never triggers them;
    a fast dash can even skip the whole thing.
  - a longer set of separated ISLANDS (~h 950-1080) - real jumps between
    individual trapdoor tiles, each one only safe to touch briefly, over
    a much wider spike bed. This is the segment's centerpiece and the
    reason it runs noticeably longer than seg_00-seg_04.

Known lint gap: lint_segments.py's reachability model only tracks
'platform' and 'moving' entities (see its `plats` filter) - trapdoors
aren't in it. The bridge stretch is built so the real platforms flanking
it are ALSO in direct dash range, so lint reads it as reachable with no
special-casing needed. The islands stretch can't satisfy that (the gap
end to end is ~430px, well past the ~360px absolute dash max) since the
whole point is that you land on the islands in between - so lint reports
that landing as an UNREACHABLE error. Each individual island-to-island
hop is a small, ordinary gap (see the comments inline); the error is the
checker not knowing trapdoors exist, not a broken jump. Leaving it
reported rather than fudging the numbers to silence it.

Check with `python lint_segments.py` after editing.

Rewritten by creative mode (F4 -> E) as a flat spec list.
"""

ENTRY = (790, 930)

ENTITIES = [
    {'type': 'platform', 'x': 790, 'h': 80, 'w': 140},
    {'type': 'platform', 'x': 700, 'h': 490, 'w': 130},
    {'type': 'platform', 'x': 980, 'h': 640, 'w': 130},
    {'type': 'platform', 'x': 780, 'h': 790, 'w': 140},
    {'type': 'platform', 'x': 650, 'h': 870, 'w': 140},
    {'type': 'platform', 'x': 650, 'h': 950, 'w': 140},
    {'type': 'platform', 'x': 1180, 'h': 950, 'w': 150},
    {'type': 'platform', 'x': 950, 'h': 1105, 'w': 130},
    {'type': 'platform', 'x': 720, 'h': 1180, 'w': 190},
    {'type': 'moving', 'x': 630, 'h': 150, 'w': 110, 'axis': 'y', 'travel': 40, 'period': 130},
    {'type': 'moving', 'x': 900, 'h': 335, 'w': 110, 'axis': 'x', 'travel': 65, 'period': 90},
    {'type': 'moving', 'x': 700, 'h': 410, 'w': 100, 'axis': 'y', 'travel': 45, 'period': 100},
    {'type': 'moving', 'x': 950, 'h': 560, 'w': 110, 'axis': 'x', 'travel': 70, 'period': 85},
    {'type': 'moving', 'x': 780, 'h': 715, 'w': 110, 'axis': 'y', 'travel': 50, 'period': 95},
    {'type': 'moving', 'x': 950, 'h': 1030, 'w': 110, 'axis': 'y', 'travel': 45, 'period': 100},
    {'type': 'wall', 'x': 894, 'h': 80, 'w': 16, 'height': 90},
    {'type': 'wall', 'x': 684, 'h': 490, 'w': 16, 'height': 90},
    {'type': 'wall', 'x': 914, 'h': 790, 'w': 16, 'height': 90},
    {'type': 'wall', 'x': 1064, 'h': 1105, 'w': 16, 'height': 90},
    {'type': 'hazard', 'x': 850, 'h': 80, 'w': 40},
    {'type': 'hazard', 'x': 780, 'h': 490, 'w': 32, 'damage': 20},
    {'type': 'hazard', 'x': 860, 'h': 880, 'w': 320, 'damage': 25},
    {'type': 'hazard', 'x': 1250, 'h': 950, 'w': 32, 'damage': 20},
    {'type': 'trapdoor', 'x': 830, 'h': 230, 'w': 40, 'height': 20},
    {'type': 'trapdoor', 'x': 960, 'h': 270, 'w': 40, 'height': 20},
    {'type': 'trapdoor', 'x': 850, 'h': 1000, 'w': 40},
    {'type': 'trapdoor', 'x': 1090, 'h': 1000, 'w': 40},
    {'type': 'trapdoor', 'x': 970, 'h': 1030, 'w': 40},
]

HEIGHT = 1180
EXIT = (720, 910)
