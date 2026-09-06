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

    Spikes only bite from the side they point at: the mounting bar they
    are welded to is inert, so `hurt_rect` (what main.py tests, not the
    sprite rect) covers the points alone. Pass flip=True for the
    ceiling-mounted variant, which hangs off the underside of a platform
    and points down instead of up.
    """

    PALETTE = RUST_PALETTE
    TAGS = frozenset({"damaging"})
    DRAW_LAYER = 2

    def __init__(self, x, y, width, height=16, damage=15, altitude=0, flip=False):
        super().__init__()
        self.damage = damage
        self.flip = flip
        # Thickness of the mounting bar - the one face that does no damage.
        # Kept in sync with the bar actually drawn below.
        self.bar_h = max(3, height // 4)
        art = tiles.render('hazard', altitude, width, height)
        self.custom_art = art is not None
        if self.custom_art:
            self.image = pygame.transform.flip(art, False, True) if flip else art
            self.rect = self.image.get_rect(topleft=(x, y))
            return
        outline, dark, body, cap_col, hi = self.PALETTE
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)

        # A mounting bar along the bottom, then shaded spikes on top of it.
        # Collision is the hurt_rect below, so this is purely about making
        # the thing legible - each spike gets a lit left facet and a dark
        # right one, which reads as a 3D point rather than a flat triangle.
        bar_h = self.bar_h
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
        # The down-pointing variant is the same art upended, so the two can
        # never drift apart visually.
        if flip:
            self.image = pygame.transform.flip(self.image, False, True)
        self.rect = self.image.get_rect(topleft=(x, y))

    @property
    def hurt_rect(self):
        """The spiked face only - the sprite rect minus the mounting bar,
        which sits at the bottom normally and at the top when flipped.
        Touching the bar side is safe, so a spike bed can be walked under
        (or a ceiling bank walked over) without taking a hit."""
        r = self.rect
        if self.flip:
            return pygame.Rect(r.x, r.y + self.bar_h, r.w, r.h - self.bar_h)
        return pygame.Rect(r.x, r.y, r.w, r.h - self.bar_h)

    def hurts(self, rect):
        return self.hurt_rect.colliderect(rect)

    @classmethod
    def from_spec(cls, spec, ground_y):
        """`h` is the height-above-ground of the platform surface this
        hazard is anchored to. Normally the hazard's bottom sits flush with
        that surface (extending upward); with 'flip': True it hangs from the
        underside of that surface instead, extending downward."""
        x = spec['x']
        w = spec['w']
        h = spec.get('h', 0)
        height = spec.get('height', 16)
        damage = spec.get('damage', 15)
        flip = spec.get('flip', False)
        surface_y = ground_y - h
        y = surface_y if flip else surface_y - height
        return cls(x, y, w, height, damage, altitude=h, flip=flip)
