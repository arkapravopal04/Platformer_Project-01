"""The player's movement envelope, modelled from the real physics.

One source of truth for "how far can the player actually jump", shared by
the offline checker (lint_segments.py) and the in-game creative mode
(devmode.py). Everything here is derived from the constants below, which
mirror player_classes.Player - retune the player and every budget, arc
and reachability test follows automatically.

No pygame import: this is pure arithmetic, so it stays runnable from a
plain terminal without a display.
"""

import functools

# --- mirrored from player_classes.Player.__init__ ------------------------
GRAVITY = 0.5
JUMP_V0 = -10          # negative is upward
WALK_SPEED = 3
SPRINT_SPEED = 6
DASH_SPEED = 16
DASH_FRAMES = 8
DASH_COOLDOWN_MS = 800

WORLD_WIDTH = 1504     # background image width; Player.set_world_bounds clamps to it
PLAYER_W = 32          # Player.hitbox_size[0]
PLAYER_H = 56          # Player.hitbox_size[1]

# Frame index at which a full-height jump reaches its apex: momentum runs
# JUMP_V0 -> 0 at GRAVITY per frame. Dashing here rather than at launch
# gives the flattest, furthest-reaching arc, so it's what the max-reach
# overlay draws.
APEX_FRAME = int(-JUMP_V0 / GRAVITY)

# How much of the theoretical maximum to actually trust. A jump that only
# clears a gap on the single best frame of the arc is not a jump a human
# lands repeatably, so anything beyond this fraction is flagged as tight.
COMFORT = 0.85


@functools.lru_cache(maxsize=None)
def _airtime_frames_at_height(rise):
    """How many GRAVITY frames the player spends at or above `rise` px
    during one full-height jump - the window in which they could land on
    a platform that high. 0 if the jump never gets there.

    Mirrors Player.apply_gravity exactly: momentum += GRAVITY, then
    position += momentum, once per frame.
    """
    v = float(JUMP_V0)
    height = 0.0
    frames = 0
    last_frame_at_or_above = 0
    while True:
        v += GRAVITY
        height -= v          # -v because negative momentum is upward
        frames += 1
        if height >= rise:
            last_frame_at_or_above = frames
        if height < 0 and v > 0:
            break            # fallen back below the starting level
        if frames > 400:
            break
    return last_frame_at_or_above


@functools.lru_cache(maxsize=None)
def max_gap(rise, sprint=True, dash=False):
    """Furthest horizontal gap (platform edge to platform edge) the player
    can clear while also gaining `rise` px of height."""
    frames = _airtime_frames_at_height(rise)
    if frames == 0:
        return 0
    speed = SPRINT_SPEED if sprint else WALK_SPEED
    reach = speed * frames
    if dash:
        # Player.apply_gravity returns early while is_dashing, so the dash's
        # frames do not advance the fall at all - they are extra airtime
        # bolted into the middle of the arc, each moving DASH_SPEED. They
        # ADD to the jump's reach rather than consuming frames from it.
        reach += DASH_SPEED * DASH_FRAMES
    return reach


@functools.lru_cache(maxsize=None)
def max_rise():
    """Highest platform top the player can still land on."""
    r = 0
    while _airtime_frames_at_height(r + 1) > 0:
        r += 1
    return r


@functools.lru_cache(maxsize=None)
def trajectory(direction=1, sprint=True, dash_at=None, frames=110, max_fall=1200):
    """Trace one jump as a list of (dx, dy) offsets from the launch point,
    in pygame screen convention: +dx right, +dy DOWN (so a rising jump has
    negative dy).

    direction: +1 right, -1 left.
    dash_at:   frame index to start a dash on, or None for no dash. Pass
               APEX_FRAME for the maximum-reach arc.

    Mirrors the real per-frame order in Player.update(): horizontal input
    first, then gravity - and while dashing, gravity is skipped entirely
    and horizontal movement comes from the dash instead.
    """
    speed = SPRINT_SPEED if sprint else WALK_SPEED
    v = float(JUMP_V0)
    x = y = 0.0
    points = [(0.0, 0.0)]
    dash_left = 0
    for f in range(frames):
        if dash_at is not None and f == dash_at:
            dash_left = DASH_FRAMES
        if dash_left > 0:
            x += DASH_SPEED * direction
            dash_left -= 1
        else:
            x += speed * direction
            v += GRAVITY
            y += v
        points.append((x, y))
        if y > max_fall:
            break
    return tuple(points)


@functools.lru_cache(maxsize=None)
def standard_arcs():
    """The four arcs worth drawing from any given stance: a plain
    sprint-jump and a maximum-reach dash-jump, in each direction.
    Returns [(label, direction, points), ...]."""
    out = []
    for direction in (1, -1):
        out.append(('sprint', direction,
                    trajectory(direction=direction, sprint=True)))
        out.append(('dash', direction,
                    trajectory(direction=direction, sprint=True, dash_at=APEX_FRAME)))
    return tuple(out)


def arc_lands_on(points, origin_x, origin_y, rect, player_w=PLAYER_W):
    """Does an arc launched from (origin_x, origin_y) - the player's
    midbottom - put them down on top of `rect`?

    Uses the same swept test as Player.apply_gravity: the player lands
    when their bottom crosses a platform's top edge while descending, with
    horizontal overlap at that moment.
    """
    half = player_w / 2.0
    top = rect.top
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if y1 <= y0:
            continue                       # rising or level: can't land
        by0, by1 = origin_y + y0, origin_y + y1
        if not (by0 <= top <= by1):
            continue                       # didn't cross this surface
        left = origin_x + x1 - half
        if left + player_w > rect.left and left < rect.right:
            return True
    return False


def reachable_from(origin_x, origin_y, rect, player_w=PLAYER_W):
    """Which of the standard arcs, if any, land on `rect`. Returns the set
    of labels that work - empty means unreachable in one hop from here."""
    hits = set()
    for label, _direction, points in standard_arcs():
        if arc_lands_on(points, origin_x, origin_y, rect, player_w):
            hits.add(label)
    return hits
