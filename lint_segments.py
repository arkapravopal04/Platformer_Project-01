"""Static reachability check for segments/*.py.

Run it before playing a newly-authored segment:

    python lint_segments.py

It simulates the player's actual jump arc using the constants defined in
player_classes.Player (gravity, jump velocity, walk/sprint speed, dash
speed and duration) rather than hardcoding a guess, so if the physics is
retuned the budgets here follow automatically.

What it checks per segment:
  * every entity's x stays inside the world bounds
  * every platform is reachable from some platform below it (or from the
    previous segment's top platforms, for the lowest ones)
  * hazards/walls are anchored to a platform that actually exists
It reports, not fixes - a WARN is a prompt to go look, since a segment can
be legitimately hard in ways a point-mass model doesn't capture.
"""

import importlib

import segments
from reach import (
    COMFORT, DASH_FRAMES, DASH_SPEED, GRAVITY, JUMP_V0, PLAYER_W,
    SPRINT_SPEED, WALK_SPEED, WORLD_WIDTH,
    _airtime_frames_at_height, max_gap, max_rise,
)

# The physics model lives in reach.py so this checker and the in-game
# creative-mode overlay (devmode.py) can never disagree about what the
# player can actually clear.

# Every entity type that can be stood on for reachability purposes.
# 'trapdoor' is included because it's landable while closed - the linter has
# no notion of standing duration, so it treats one exactly like a platform;
# a trap whose only purpose is to eventually open is still a legitimate link
# in a jump chain right up until it does.
LANDABLE_TYPES = ('platform', 'moving', 'trapdoor')


def entity_width(spec):
    if spec['type'] == 'wall':
        return spec.get('w', 16)
    if spec['type'] == 'goal':
        return spec.get('w', 26)
    return spec['w']


def check_segment(name, mod, prev_tops):
    """Returns (errors, warnings, tops) - `tops` being this segment's
    platforms expressed in the NEXT segment's coordinate space (i.e.
    h - HEIGHT), ready to seed the next segment's reachability check."""
    errors, warnings = [], []
    ents = mod.ENTITIES
    plats = [e for e in ents if e['type'] in LANDABLE_TYPES]

    if not plats:
        errors.append("no platforms at all")
        return errors, warnings, []

    # --- world bounds ---
    for e in ents:
        left, right = e['x'], e['x'] + entity_width(e)
        if left < 0 or right > WORLD_WIDTH:
            errors.append(
                f"{e['type']} at x={e['x']} spans {left}..{right}, outside 0..{WORLD_WIDTH}")

    # --- HEIGHT sanity ---
    # Convention: HEIGHT == the topmost platform's h, so the next segment's
    # floor (its own h=0) lands exactly on this segment's last surface. Set
    # it lower and the next segment sinks into this one; set it much higher
    # and the seam becomes an unjumpable gap - which the reachability pass
    # below would catch anyway, but the message is clearer here.
    top_plat_h = max(p['h'] for p in plats)
    if mod.HEIGHT < top_plat_h:
        errors.append(
            f"HEIGHT={mod.HEIGHT} is below the topmost platform (h={top_plat_h}); "
            "the next segment would overlap this one")
    elif mod.HEIGHT > top_plat_h + max_rise():
        errors.append(
            f"HEIGHT={mod.HEIGHT} leaves {mod.HEIGHT - top_plat_h}px of dead air above "
            f"the topmost platform (h={top_plat_h}), more than the {max_rise()}px "
            "max jump - the next segment would be unreachable")

    # --- reachability ---
    # A platform is reachable if some platform below it (or a carried-over
    # platform from the previous segment) is within jump range. Moving
    # platforms get credit for their full travel in both directions.
    def span(p):
        travel = p.get('travel', 0) if p['type'] == 'moving' else 0
        if p['type'] == 'moving' and p.get('axis', 'x') != 'x':
            travel = 0
        return p['x'] - travel, p['x'] + p['w'] + travel

    def reach_h(p):
        # a vertically-moving platform can be boarded at its lowest point
        if p['type'] == 'moving' and p.get('axis', 'x') == 'y':
            return p['h'] - p.get('travel', 0)
        return p['h']

    # NB: the in-segment sources must be the SAME dict objects as `plats`,
    # not copies - the `src is target` guard below is what stops a platform
    # from being judged reachable from itself (rise 0, gap 0, always true).
    sources = list(prev_tops) + list(plats)
    if not prev_tops:
        # the very first segment launches off the flat ground floor, which
        # spans the whole map at h=0 and isn't a Platform anywhere
        sources.append({'type': 'platform', 'x': 0, 'w': WORLD_WIDTH, 'h': 0})
    for target in sorted(plats, key=lambda p: p['h']):
        t_left, t_right = span(target)
        t_h = reach_h(target)
        best = None
        for src in sources:
            if src is target:
                continue
            s_h = src['h']
            if s_h > t_h:
                continue           # only climb from at-or-below
            rise = t_h - s_h
            s_left, s_right = span(src)
            # horizontal gap between the two platforms' nearest edges
            if s_right <= t_left:
                gap = t_left - s_right
            elif t_right <= s_left:
                gap = s_left - t_right
            else:
                gap = 0            # they overlap horizontally
            limit_plain = max_gap(rise, sprint=True, dash=False)
            limit_dash = max_gap(rise, sprint=True, dash=True)
            if limit_dash <= 0:
                continue
            if gap <= limit_plain * COMFORT:
                best = ('sprint', gap, limit_plain)
                break
            if gap <= limit_dash * COMFORT:
                if best is None or best[0] != 'sprint':
                    best = ('dash', gap, limit_dash)
            elif gap <= limit_dash:
                if best is None:
                    best = ('tight', gap, limit_dash)
        if best is None:
            errors.append(
                f"platform x={target['x']} w={target['w']} h={target['h']} "
                f"is UNREACHABLE from anything below it")
        elif best[0] == 'tight':
            warnings.append(
                f"platform x={target['x']} h={target['h']} needs a near-perfect "
                f"dash-jump (gap {best[1]}, absolute max {best[2]})")

    # --- hazards/walls should sit on a real platform surface ---
    plat_hs = {p['h'] for p in plats}
    for e in ents:
        if e['type'] in ('hazard', 'wall') and e['h'] not in plat_hs:
            warnings.append(
                f"{e['type']} at x={e['x']} h={e['h']} isn't flush with any "
                f"platform in this segment (floating?)")

    # carry this segment's platforms into the next one's coordinate space
    tops = []
    for p in plats:
        if p['h'] >= top_plat_h - max_rise():
            q = dict(p)
            q['h'] = p['h'] - mod.HEIGHT
            tops.append(q)
    return errors, warnings, tops


def main():
    print("player reach budget (derived from player_classes constants)")
    print(f"  max rise:            {max_rise()} px")
    for rise in (0, 25, 50, 75, 90):
        g = max_gap(rise, sprint=False)
        s = max_gap(rise, sprint=True)
        d = max_gap(rise, sprint=True, dash=True)
        print(f"  rise {rise:>3}px -> walk {g:>4}  sprint {s:>4}  sprint+dash {d:>4}")
    print(f"  (comfort threshold: {int(COMFORT * 100)}% of max)")
    print()

    mods = [(name, importlib.import_module(f'segments.{name}'))
            for name in segments.discover_names()]

    if not mods:
        print('segments/ is empty - the level has been cleared.')
        print('Run the game, press F4 and build, or restore with:')
        print('    python clear_level.py --restore')
        return 0

    total_err = 0
    prev_tops = []
    for name, mod in mods:
        errors, warnings, prev_tops = check_segment(name, mod, prev_tops)
        total_err += len(errors)
        status = "FAIL" if errors else ("warn" if warnings else "ok")
        n_plats = len([e for e in mod.ENTITIES if e['type'] in LANDABLE_TYPES])
        print(f"[{status:>4}] {name}  HEIGHT={mod.HEIGHT}  platforms={n_plats}")
        for e in errors:
            print(f"         ERROR: {e}")
        for w in warnings:
            print(f"         warn:  {w}")

    # --- ENTRY/EXIT continuity, including the CYCLE_TAIL wrap ----------
    # A segment's ENTRY says where the player arrives along its floor; the
    # previous segment's EXIT says where they left. If those bands don't
    # overlap, the seam between the two is a blind hop sideways.
    print()
    print("segment seams (previous EXIT vs next ENTRY):")
    from tower import CYCLE_TAIL

    def seam(a_name, a_mod, b_name, b_mod, label=""):
        exit_band = getattr(a_mod, 'EXIT', None)
        entry_band = getattr(b_mod, 'ENTRY', None)
        if exit_band is None or entry_band is None:
            print(f"  [ -- ] {a_name} -> {b_name}: missing EXIT/ENTRY, skipped")
            return 0
        lo = max(exit_band[0], entry_band[0])
        hi = min(exit_band[1], entry_band[1])
        if hi > lo:
            print(f"  [  ok] {a_name} -> {b_name}{label}: overlap {hi - lo}px")
            return 0
        print(f"  [FAIL] {a_name} -> {b_name}{label}: EXIT {exit_band} does not "
              f"overlap ENTRY {entry_band}")
        return 1

    seam_err = 0
    for (an, am), (bn, bm) in zip(mods, mods[1:]):
        seam_err += seam(an, am, bn, bm)
    # the wrap: after the last segment, the tower restarts at the tail
    if len(mods) > 1:
        tail_start = max(0, len(mods) - CYCLE_TAIL)
        seam_err += seam(mods[-1][0], mods[-1][1],
                         mods[tail_start][0], mods[tail_start][1],
                         label="  (CYCLE_TAIL wrap)")
    total_err += seam_err

    print()
    print("all segments reachable and seams line up" if total_err == 0
          else f"{total_err} error(s)")
    return 1 if total_err else 0


if __name__ == '__main__':
    raise SystemExit(main())
