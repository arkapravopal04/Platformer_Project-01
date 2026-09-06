import pygame

import tiles
from render import _mix, EARTH_PALETTE, RUST_PALETTE
from .base import Entity, register

# A single floor panel, not a stretchable slab like Platform - "1x1" in the
# sense of being one fixed-size tile rather than an arbitrary-width plank.
TILE_W = 40
TILE_H = 10

# Timing is deliberately twitchy: the door should feel like it snaps rather
# than sags. You get a brief tell (the flicker) and then it's gone - close
# to the near-instant Dead Cells trapdoor, with just enough warning frames
# to be readable and reactable at 60fps.
STAND_DELAY = 14        # frames standing before it gives way (~0.23s @ 60fps)
WARN_FRACTION = 0.35    # fraction of stand_delay after which it visibly shakes
OPEN_DURATION = 40      # frames it stays open before resetting shut (~0.66s)
SHAKE_PERIOD = 2        # frames between the two warning-flicker images


@register("trapdoor")
class TrapDoor(Entity):
    """A floor panel that gives way if you stand on it too long.

    Closed, it behaves exactly like a Platform - landable, solid, and the
    player rides/lands on it the same way. Stand on it CONTINUOUSLY past
    `stand_delay` frames - a short fuse, with a brief flicker over the last
    stretch as the only warning - and it snaps open in a single frame: it
    removes itself from every sprite group it was placed in, so the player
    falls through it exactly the way they'd fall through a gap - no
    special-casing needed in Player at all. It resets shut on its own after
    `open_duration` frames, whether or not anyone is still there.

    Standing time resets to zero the moment you step off - a quick tap
    never triggers it, only staying put does.

    Detecting "is the player standing on this" is main.py's job, not this
    class's: main.py checks `player.standing_platform is entity` once a
    frame for everything tagged "collapsible" and calls on_stand()/
    on_leave() accordingly, the same way hazard damage is main.py's job for
    everything tagged "damaging". This class never touches Player directly.
    """

    PALETTE = EARTH_PALETTE
    TAGS = frozenset({"landable", "collapsible"})
    DRAW_LAYER = 0

    def __init__(self, x, y, width=TILE_W, height=TILE_H,
                 stand_delay=STAND_DELAY, open_duration=OPEN_DURATION,
                 altitude=0):
        super().__init__()
        self.stand_delay = stand_delay
        self.open_duration = open_duration

        art = tiles.render('trapdoor', altitude, width, height)
        self.custom_art = art is not None
        if self.custom_art:
            # A custom sprite is expected to be a single "closed" image; we
            # can't assume the artist supplied warning/open frames too, so
            # those are derived from it rather than required.
            self._img_closed = art
            self._img_warn = [self._tinted(art, 90), self._tinted(art, 160)]
            self._img_open = self._punched(art, width, height)
        else:
            self._img_closed = self._render_closed(width, height)
            self._img_warn = [self._render_closed(width, height, warn=0.45),
                              self._render_closed(width, height, warn=0.9)]
            self._img_open = self._render_open(width, height)

        self.image = self._img_closed
        self.rect = self.image.get_rect(topleft=(x, y))

        # present so code that treats "whatever's in the landable group"
        # uniformly (e.g. a future moving trapdoor) doesn't need a type check
        self.base_x = float(x)
        self.base_y = float(y)
        self.delta_x = 0
        self.delta_y = 0

        self.state = 'closed'         # 'closed' | 'open'
        self._stand_timer = 0
        self._open_timer = 0
        self._saved_groups = None      # groups to rejoin when it resets shut

    # -- rendering (no dedicated sprite supplied) ---------------------------
    def _render_closed(self, width, height, warn=0.0):
        outline, dark, body, cap, hi = self.PALETTE
        if warn:
            body = _mix(body, RUST_PALETTE[2], warn * 0.55)
            cap = _mix(cap, RUST_PALETTE[3], warn * 0.65)
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        surf.fill(body)
        # The panel is only a few pixels tall, so every band has to earn its
        # row: a single lit cap line on top, a shadow line on the bottom,
        # and the detail sits in between rather than being stacked.
        pygame.draw.rect(surf, cap, (0, 0, width, max(1, height // 4)))
        pygame.draw.line(surf, dark, (1, height - 2), (width - 2, height - 2), 1)
        pygame.draw.rect(surf, outline, (0, 0, width, height), 1)
        # seam down the middle plus two pull-nubs - reads as a hinged
        # double-door, not a plain platform, even at a glance
        mid = width // 2
        pygame.draw.line(surf, dark, (mid, 1), (mid, height - 2), 1)
        nub_y = max(2, height - 4)
        for hx in (width * 0.28, width * 0.72):
            pygame.draw.line(surf, dark, (int(hx) - 1, nub_y), (int(hx) + 1, nub_y), 1)
            surf.set_at((int(hx), max(1, nub_y - 1)), hi)
        return surf

    def _render_open(self, width, height):
        outline, dark, body, _cap, _hi = self.PALETTE
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        # Open reads as a hole, not a shape: the pit fills the whole tile and
        # only the two hinge stubs at the ends are left of the panel, which
        # at this thickness is all there's room for anyway.
        surf.fill((14, 11, 9))
        pygame.draw.rect(surf, (6, 5, 4), (0, 0, width, max(1, height // 3)))
        stub = max(2, width // 8)
        for sx in (0, width - stub):
            pygame.draw.rect(surf, body, (sx, 0, stub, height))
            pygame.draw.line(surf, dark, (sx, height - 2), (sx + stub - 1, height - 2), 1)
        pygame.draw.rect(surf, outline, (0, 0, width, height), 1)
        return surf

    # -- rendering (custom sprite supplied) ---------------------------------
    @staticmethod
    def _tinted(surf, alpha):
        out = surf.copy()
        overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        overlay.fill((*RUST_PALETTE[2], alpha))
        out.blit(overlay, (0, 0))
        return out

    @staticmethod
    def _punched(surf, width, height):
        out = surf.copy()
        inset = 1 if height < 12 else 2
        pygame.draw.rect(out, (10, 8, 6, 235),
                         (2, inset, max(0, width - 4), max(0, height - inset * 2)))
        return out

    # -- state machine, driven by main.py's per-frame occupancy check ------
    def on_stand(self):
        """Call once per frame while the player is standing on this door."""
        if self.state != 'closed':
            return
        self._stand_timer += 1
        if self._stand_timer >= self.stand_delay:
            self._open()
        elif self._stand_timer >= self.stand_delay * WARN_FRACTION:
            self.image = self._img_warn[(self._stand_timer // SHAKE_PERIOD) % 2]

    def on_leave(self):
        """Call once per frame while the player is NOT standing on this
        door. Harmless no-op once it has already opened."""
        if self.state == 'closed' and self._stand_timer:
            self._stand_timer = 0
            self.image = self._img_closed

    def _open(self):
        self.state = 'open'
        self._open_timer = 0
        self.image = self._img_open
        # Leave every group it was placed in - landable, collapsible, and
        # anything else a future tag combination might add - so the player
        # falls through it exactly like a gap, with no special case in
        # Player.apply_gravity, and main.py's collapsible scan stops
        # calling on_stand/on_leave until it resets shut.
        self._saved_groups = list(self.groups())
        self.remove(*self._saved_groups)

    def _close(self):
        self.state = 'closed'
        self._stand_timer = 0
        self.image = self._img_closed
        if self._saved_groups:
            self.add(*self._saved_groups)
        self._saved_groups = None

    def update(self):
        if self.state == 'open':
            self._open_timer += 1
            if self._open_timer >= self.open_duration:
                self._close()

    @classmethod
    def from_spec(cls, spec, ground_y):
        x = spec['x']
        h = spec.get('h', 0)
        width = spec.get('w', TILE_W)
        height = spec.get('height', TILE_H)
        return cls(x, ground_y - h, width, height,
                   stand_delay=spec.get('stand_delay', STAND_DELAY),
                   open_duration=spec.get('open_duration', OPEN_DURATION),
                   altitude=h)
