import pygame

import tiles
from render import render_ledge_cached, _mix, STONE_PALETTE
from .base import Entity, register


@register("wall")
class Wall(Entity):
    """A vertical blocking obstacle: stops horizontal movement (walking,
    sprinting, dashing) but has NO effect on vertical movement - the
    player can jump over the top of one freely, same as clearing any
    other platform edge. It exists purely to make a specific gap
    un-skippable: without one, a sprint-jump or dash-jump with enough
    horizontal reach could sail straight past an intermediate platform
    that's meant to be a required step, since gap distance alone doesn't
    stop a strong jump from overshooting. A wall physically closes that
    gap at a height low enough to force landing on the intended platform
    first, tall enough that going over it means using the platform (not
    just ducking under an edge).

    Not landable in the normal sense (its top edge isn't meant to be a
    resting surface, though nothing stops a player from landing there if
    a jump happens to clear it exactly - it's simply not the intended
    path). Purely horizontal-collision, handled by
    Player._clamp_to_walls(), which main.py wires up via
    player.set_walls(course['walls']).
    """

    PALETTE = STONE_PALETTE
    TAGS = frozenset({"blocking"})
    DRAW_LAYER = 1

    def __init__(self, x, y, width=16, height=120, altitude=0):
        super().__init__()
        art = tiles.render('wall', altitude, width, height)
        self.custom_art = art is not None
        if self.custom_art:
            self.image = art
            self.rect = self.image.get_rect(topleft=(x, y))
            return
        outline, dark, body, cap_col, hi = self.PALETTE
        # .copy(): the base ledge is a shared cached surface (see
        # render_ledge_cached) - the masonry detailing drawn below is
        # per-instance and must not mutate the surface other walls reuse
        self.image = render_ledge_cached(width, height, self.PALETTE,
                                         seed=int(x * 17 + y), cap=False).copy()

        # stacked masonry courses - a pillar reads as "climb over me", which
        # is exactly the intended interaction, whereas the old flat slab with
        # vertical grooves read as a platform stood on its end
        course_h = 14
        for row in range(course_h, height - 2, course_h):
            pygame.draw.line(self.image, _mix(dark, outline, 0.5), (1, row), (width - 2, row))
            pygame.draw.line(self.image, _mix(body, hi, 0.18), (1, row + 1), (width - 2, row + 1))

        # a capstone on top, lit, so the height you have to clear is obvious
        pygame.draw.rect(self.image, cap_col, (0, 0, width, 5))
        pygame.draw.line(self.image, hi, (1, 0), (width - 2, 0))
        pygame.draw.line(self.image, outline, (0, 5), (width - 1, 5))
        pygame.draw.rect(self.image, outline, (0, 0, width, height), 1)
        self.rect = self.image.get_rect(topleft=(x, y))

    @classmethod
    def from_spec(cls, spec, ground_y):
        """`h` is the height-above-ground of the gap floor this wall
        guards, matching the corresponding platform's own `h` - the wall's
        bottom sits flush with that surface and it extends upward by its
        own `height`."""
        x = spec['x']
        h = spec.get('h', 0)
        wall_height = spec.get('height', 120)
        width = spec.get('w', 16)
        y_bottom = ground_y - h
        return cls(x, y_bottom - wall_height, width, wall_height, altitude=h)
