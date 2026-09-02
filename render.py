import random

import pygame


# --- shared look-and-feel -------------------------------------------------
# Each palette is (outline, dark, body, cap, highlight), darkest first. They
# exist so the different obstacle types read apart instantly at a glance:
# earth = safe to stand on, steel = it moves, stone = it blocks you,
# rust = it hurts.
EARTH_PALETTE = ((46, 32, 22), (78, 56, 38), (112, 84, 56), (168, 134, 92), (214, 186, 138))
STEEL_PALETTE = ((26, 34, 54), (52, 68, 100), (80, 104, 144), (124, 156, 196), (178, 210, 240))
STONE_PALETTE = ((28, 28, 38), (52, 52, 64), (80, 80, 94), (112, 112, 128), (152, 152, 170))
RUST_PALETTE = ((60, 12, 12), (120, 26, 26), (176, 44, 44), (214, 86, 70), (250, 170, 140))


def _mix(a, b, t):
    """Blend two RGB colours; t=0 gives a, t=1 gives b."""
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def _render_ledge(width, height, palette, seed=0, cap=True):
    """Draw a chunky platform slab: lit cap on top, body shading to dark at
    the bottom, bevelled sides and a hard outline.

    The top few pixels are deliberately the brightest thing on the sprite -
    that edge is the only part the player can actually land on, so it should
    be the part the eye finds first. Speckles come from a seeded RNG so a
    given platform looks the same on every frame (an unseeded one would
    crawl with static).
    """
    outline, dark, body, cap_col, hi = palette
    surf = pygame.Surface((width, height), pygame.SRCALPHA)

    cap_h = min(6, max(3, height // 4)) if cap else 0

    # body, shading downward
    for row in range(cap_h, height):
        t = (row - cap_h) / max(1, height - cap_h - 1)
        pygame.draw.line(surf, _mix(body, dark, t * 0.85), (0, row), (width - 1, row))

    # speckled grain, skipping the cap so the landing edge stays clean
    speckle_col = _mix(body, dark, 0.75)
    rng = random.Random(seed)
    for _ in range(max(3, (width * height) // 70)):
        sx = rng.randrange(width)
        sy = rng.randrange(cap_h + 1, height) if height > cap_h + 1 else cap_h
        surf.set_at((sx, sy), speckle_col)

    if cap_h:
        pygame.draw.rect(surf, cap_col, (0, 0, width, cap_h))
        pygame.draw.line(surf, hi, (0, 0), (width - 1, 0))
        pygame.draw.line(surf, _mix(cap_col, dark, 0.5), (0, cap_h), (width - 1, cap_h))

    # bevel: lit left edge, shaded right edge
    pygame.draw.line(surf, _mix(body, hi, 0.25), (0, cap_h), (0, height - 1))
    pygame.draw.line(surf, dark, (width - 1, cap_h), (width - 1, height - 1))
    pygame.draw.rect(surf, outline, (0, 0, width, height), 1)

    # knock the corners off so slabs don't read as perfect rectangles
    for cx, cy in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        surf.set_at((cx, cy), (0, 0, 0, 0))
    return surf


# How many distinct grain patterns _render_ledge_cached hands out per
# (width, height, palette, cap). The tower is built from a small, fixed set
# of block sizes that repeats forever (see segments/), so without this every
# platform/wall would re-run the speckle loop on its own unique seed even
# though most of them are geometrically identical - this bounds the cache to
# a handful of surfaces per size instead of one per placed entity, while
# still keeping visible variety between neighbours.
_LEDGE_VARIANTS = 8
_ledge_cache = {}


def render_ledge_cached(width, height, palette, seed=0, cap=True):
    """Same output as _render_ledge, but memoised per (size, palette, cap,
    seed bucket). Callers keep passing a per-instance seed (e.g. derived
    from position) for grain variety - it's just folded into a small,
    reusable bucket rather than used verbatim."""
    key = (width, height, palette, cap, seed % _LEDGE_VARIANTS)
    cached = _ledge_cache.get(key)
    if cached is None:
        cached = _render_ledge(width, height, palette, seed=key[-1], cap=cap)
        _ledge_cache[key] = cached
    return cached
