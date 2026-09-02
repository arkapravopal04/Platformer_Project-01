import pygame

import tiles
from render import RUST_PALETTE
from .base import Entity, register


@register("hazard")
class Hazard(Entity):
    """A stationary damage source (spikes). Purely a collision target -
    Player doesn't currently check hazards on its own, so main.py's game
    loop is responsible for testing player/hazard overlap each frame and
    calling player.get_hit(amount) when they intersect (the same pattern
    already used for the debug 'H' key). Never landable, so apply_gravity's
    platform-landing check won't treat one as ground.
    """

    PALETTE = RUST_PALETTE
    TAGS = frozenset({"damaging"})
    DRAW_LAYER = 2

    def __init__(self, x, y, width, height=16, damage=15, altitude=0):
        super().__init__()
        self.damage = damage
        art = tiles.render('hazard', altitude, width, height)
        self.custom_art = art is not None
        if self.custom_art:
            self.image = art
            self.rect = self.image.get_rect(topleft=(x, y))
            return
        outline, dark, body, cap_col, hi = self.PALETTE
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)

        # A mounting bar along the bottom, then shaded spikes on top of it.
        # Collision is still the plain rect, so this is purely about making
        # the thing legible - each spike gets a lit left facet and a dark
        # right one, which reads as a 3D point rather than a flat triangle.
        bar_h = max(3, height // 4)
        pygame.draw.rect(self.image, dark, (0, height - bar_h, width, bar_h))
        pygame.draw.line(self.image, body, (0, height - bar_h), (width - 1, height - bar_h))

        spike_count = max(1, width // 14)
        spike_w = width / spike_count
        for i in range(spike_count):
            left = i * spike_w
            tip = (left + spike_w / 2, 0)
            base_y = height - bar_h + 1
            pygame.draw.polygon(self.image, body,
                                [(left, base_y), tip, (left + spike_w, base_y)])
            pygame.draw.polygon(self.image, cap_col,
                                [(left + 1, base_y), tip, (left + spike_w / 2, base_y)])
            pygame.draw.line(self.image, hi, (left + spike_w / 2 - 1, base_y - 2), tip)
            pygame.draw.line(self.image, outline, (left + spike_w, base_y), tip)
        self.rect = self.image.get_rect(topleft=(x, y))

    @classmethod
    def from_spec(cls, spec, ground_y):
        """`h` is the height-above-ground of the platform surface this
        hazard sits on; the hazard's own bottom is placed flush with that
        surface (its top extends upward by its own height)."""
        x = spec['x']
        w = spec['w']
        h = spec.get('h', 0)
        height = spec.get('height', 16)
        damage = spec.get('damage', 15)
        return cls(x, ground_y - h - height, w, height, damage, altitude=h)
