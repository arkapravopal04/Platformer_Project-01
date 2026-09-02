import pygame

from entities import ENTITY_TYPES


def build_entities(specs, ground_y):
    """Instantiate a flat list of entity specs (each a dict with at least
    {'type': <name registered in ENTITY_TYPES>}) into live sprites,
    grouped by tag rather than by concrete class - see entities.Entity.TAGS.

    Returns (entities, by_tag): `entities` is every sprite in spec order;
    `by_tag` maps each tag string to a pygame.sprite.Group of everything
    carrying that tag (an entity with multiple tags lands in each group).
    """
    entities = []
    by_tag = {}
    for spec in specs:
        cls = ENTITY_TYPES[spec['type']]
        entity = cls.from_spec(spec, ground_y)
        entities.append(entity)
        for tag in cls.TAGS:
            by_tag.setdefault(tag, pygame.sprite.Group()).add(entity)
    return entities, by_tag


def _build_leg(ref, direction, hops, start_h):
    """Build one row of platforms that either climbs rightward
    (direction=+1) or leftward (direction=-1) across the map.

    ref: the x-coordinate to measure the FIRST hop's gap from - the
        previous platform's right edge for a rightward leg, or its left
        edge for a leftward leg.
    hops: list of (gap, width, rise) tuples, one per platform in this
        leg, in traversal order. gap is measured from the previous
        platform's edge (or from `ref` for the first hop); rise is added
        to height_above_ground for that hop (cumulative).
    start_h: height_above_ground of the reference point.

    Returns (platforms, new_ref, new_h) where platforms is a list of
    (x, width, height_above_ground) and new_ref/new_h describe the last
    platform's outer edge/height, ready to feed into the next leg or turn.

    This is the authoring helper segments/*.py use to lay out a zig-zag
    row of platforms without hand-computing every absolute x - see
    segments/seg_00_intro.py for the pattern.
    """
    plats = []
    h = start_h
    for gap, w, rise in hops:
        h += rise
        if direction == 1:
            left = ref + gap
            plats.append((left, w, h))
            ref = left + w
        else:
            right = ref - gap
            left = right - w
            plats.append((left, w, h))
            ref = left
    return plats, ref, h
