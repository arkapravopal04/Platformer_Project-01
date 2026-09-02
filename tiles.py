"""Per-band sprite art for the blocks.

The mirror of background.py, for the things you stand on instead of the
thing behind them. Both key off the same altitude bands, so one theme is
one folder name in both places:

    backgrounds/02_cliffs/frame_1.png   <- what's behind you
    tiles_art/02_cliffs/platform.png    <- what you stand on

Drop a sprite in and it is used automatically. Any block with no art for
its band keeps the existing hand-drawn look (render.py's _render_ledge and
friends), so this is purely additive - nothing changes until you add files.

(The folder is tiles_art/ rather than tiles/ so it cannot shadow this
module on the import path.)

Blocks are arbitrary sizes, so a sprite is never simply stretched:
platforms are 3-sliced horizontally (left cap, tiled middle, right cap),
walls 3-sliced vertically, and spikes tiled. That keeps corners crisp and
detail at a constant scale however wide a platform is.
"""

import os

import pygame

from background import band_at, band_folder

TILE_DIR = os.path.join(os.path.dirname(__file__), 'tiles_art')

# Which file each block looks for. A vertical lift falls back to mover.png
# if there's no lift.png, so one mover sprite covers both if you want.
SPRITE_FILES = {
    'platform': ['platform.png'],
    'mover':    ['mover.png', 'platform.png'],
    'lift':     ['lift.png', 'mover.png', 'platform.png'],
    'wall':     ['wall.png'],
    'hazard':   ['hazard.png'],
    'goal':     ['goal.png'],
    'trapdoor': ['trapdoor.png', 'platform.png'],
}

# 3-slice cap size in pixels: how much of each end of the sprite is a fixed
# "corner" that never stretches. The middle between the caps is what tiles.
# Raise it if your art has chunky end pieces.
CAP = 8

_cache = {}       # (kind, band, w, h) -> Surface
_source = {}      # (kind, band) -> Surface or None


def reload():
    """Drop cached art so newly added files are picked up. Wired to F5
    alongside the segment and background reloads."""
    _cache.clear()
    _source.clear()


def _load_source(kind, band):
    """The raw sprite for a block kind in a band, or None if there is no
    art - in which case the caller keeps its procedural drawing."""
    key = (kind, band)
    if key in _source:
        return _source[key]
    folder = os.path.join(TILE_DIR, band_folder(band))
    found = None
    for filename in SPRITE_FILES.get(kind, []):
        path = os.path.join(folder, filename)
        if os.path.isfile(path):
            try:
                found = pygame.image.load(path).convert_alpha()
                break
            except pygame.error:
                found = None      # unreadable file: fall through, don't crash
    _source[key] = found
    return found


def _scaled(image, size):
    if image.get_size() == size:
        return image
    return pygame.transform.scale(image, size)


def _slice_h(image, width, height):
    """Left cap + tiled middle + right cap, at the requested size."""
    src_w, src_h = image.get_size()
    image = _scaled(image, (src_w, height)) if src_h != height else image
    src_w = image.get_width()
    cap = min(CAP, max(1, src_w // 3), max(1, width // 3))

    out = pygame.Surface((width, height), pygame.SRCALPHA)
    middle_src = image.subsurface(
        pygame.Rect(cap, 0, max(1, src_w - cap * 2), height))
    span = width - cap * 2
    x = cap
    while x < cap + span:
        chunk = min(middle_src.get_width(), cap + span - x)
        out.blit(middle_src, (x, 0), pygame.Rect(0, 0, chunk, height))
        x += chunk
    out.blit(image, (0, 0), pygame.Rect(0, 0, cap, height))
    out.blit(image, (width - cap, 0),
             pygame.Rect(src_w - cap, 0, cap, height))
    return out


def _slice_v(image, width, height):
    """Top cap + tiled middle + bottom cap - for walls."""
    src_w, src_h = image.get_size()
    image = _scaled(image, (width, src_h)) if src_w != width else image
    src_h = image.get_height()
    cap = min(CAP, max(1, src_h // 3), max(1, height // 3))

    out = pygame.Surface((width, height), pygame.SRCALPHA)
    middle_src = image.subsurface(
        pygame.Rect(0, cap, width, max(1, src_h - cap * 2)))
    span = height - cap * 2
    y = cap
    while y < cap + span:
        chunk = min(middle_src.get_height(), cap + span - y)
        out.blit(middle_src, (0, y), pygame.Rect(0, 0, width, chunk))
        y += chunk
    out.blit(image, (0, 0), pygame.Rect(0, 0, width, cap))
    out.blit(image, (0, height - cap),
             pygame.Rect(0, src_h - cap, width, cap))
    return out


def _tile_h(image, width, height):
    """Repeat the sprite across the width at a constant scale - for spikes,
    where each repeat is one tooth and stretching would look wrong."""
    src_w, src_h = image.get_size()
    if src_h != height:
        scale = height / src_h
        image = pygame.transform.scale(
            image, (max(1, int(src_w * scale)), height))
        src_w = image.get_width()
    out = pygame.Surface((width, height), pygame.SRCALPHA)
    x = 0
    while x < width:
        out.blit(image, (x, 0), pygame.Rect(0, 0, min(src_w, width - x), height))
        x += src_w
    return out


# how each kind is fitted to its block's size
_FIT = {
    'platform': _slice_h,
    'mover': _slice_h,
    'lift': _slice_h,
    'wall': _slice_v,
    'hazard': _tile_h,
    'goal': lambda img, w, h: _scaled(img, (w, h)),
}


def render(kind, altitude, width, height):
    """Sprite for a block of this kind at this altitude, fitted to
    width x height - or None if the band has no art, meaning the caller
    should keep its own procedural drawing.

    Results are cached per (kind, band, size), so the repeated segments of
    a tall tower reuse one surface rather than re-slicing every time.
    """
    if width <= 0 or height <= 0:
        return None
    band = band_at(altitude)
    key = (kind, band, width, height)
    if key in _cache:
        return _cache[key]
    source = _load_source(kind, band)
    if source is None:
        _cache[key] = None
        return None
    fitted = _FIT.get(kind, _FIT['platform'])(source, width, height)
    _cache[key] = fitted
    return fitted


def has_art(kind, altitude):
    return _load_source(kind, band_at(altitude)) is not None
