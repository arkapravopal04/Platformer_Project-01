import math

import pygame

import tiles
from render import render_ledge_cached, _mix, EARTH_PALETTE, STEEL_PALETTE
from .base import Entity, register


@register("platform")
class Platform(Entity):
    """A solid, one-way platform: the player lands on top of it while
    falling, but passes through freely from below and the sides (classic
    "jump-through" platform behavior, not a solid block on all sides).

    Standing on one works exactly like standing on the ground floor -
    is_on_ground becomes True, jumping works normally, and the camera
    re-anchors its headroom around wherever the player is currently
    standing (see Camera._target_offset - it's based on rect.bottom, not
    a hardcoded ground_y, so this falls out for free).
    """

    PALETTE = EARTH_PALETTE
    TAGS = frozenset({"landable"})
    DRAW_LAYER = 0

    SPRITE_KIND = 'platform'

    def __init__(self, x, y, width, height=20, altitude=0):
        super().__init__()
        # Band sprite if the artist has supplied one for this altitude,
        # otherwise the hand-drawn slab. Purely additive: with no art in
        # tiles/ this is exactly the original rendering.
        art = tiles.render(self.SPRITE_KIND, altitude, width, height)
        self.custom_art = art is not None
        # seed off the position so each slab gets its own stable grain -
        # render_ledge_cached buckets this into a small set of reusable
        # variants rather than rendering one surface per placed platform
        self.image = art or render_ledge_cached(width, height, self.PALETTE,
                                                seed=int(x * 31 + y))
        self.rect = self.image.get_rect(topleft=(x, y))
        # base position this platform was created at - moving platforms
        # override update() to oscillate around this; static platforms
        # just leave it unused.
        self.base_x = float(x)
        self.base_y = float(y)
        # 0 for static platforms; MovingPlatform overrides these each
        # frame in update(). Present here so code that rides "whatever
        # platform the player is standing on" doesn't need to check the
        # platform's type first.
        self.delta_x = 0
        self.delta_y = 0

    @classmethod
    def from_spec(cls, spec, ground_y):
        """Build from a flat level spec. `h` is height above ground_y of
        this platform's own top (landable) surface - the same convention
        _build_leg uses - and is never affected by world-width scaling;
        only x/w carry a pre-applied scale factor by the time they reach
        here."""
        x = spec['x']
        w = spec['w']
        h = spec.get('h', 0)
        height = spec.get('height', 20)
        return cls(x, ground_y - h, w, height, altitude=h)


@register("moving")
class MovingPlatform(Platform):
    """A platform that oscillates back and forth along one axis. The
    player's horizontal collision (in Player.apply_gravity) is a
    swept top-surface check done in *world* space each frame, so a
    platform that has moved since last frame is picked up automatically -
    no special-casing needed on the player side. Riding one just means
    landing, then re-landing each frame as the platform's top keeps
    intercepting the player's falling rect.

    Exposes delta_x / delta_y, the change in position from last frame to
    this one. main.py uses this to carry a standing player along with the
    platform each frame - see Player.apply_gravity's standing_platform
    handling, which reads these deltas right after this platform's own
    update() has already run for the frame.
    """

    PALETTE = STEEL_PALETTE
    TAGS = frozenset({"landable", "moving"})
    DRAW_LAYER = 0

    @staticmethod
    def auto_phase(x, h):
        """A stable, well-spread phase for a mover that wasn't given one.

        Without this every mover sharing a period runs in perfect lockstep,
        because they all start at t=0 - a row of them reads as one clock
        rather than as separate machines. Derived from the mover's position
        WITHIN ITS SEGMENT (local h, not world height), so every copy of a
        repeated segment keeps identical timing and a jump you designed
        against one still works on all of them.
        """
        mixed = (int(x) * 73856093) ^ (int(h) * 19349663)
        return (mixed % 997) / 997.0

    def __init__(self, x, y, width, height=20,
                 axis='x', travel=80, period_frames=120, altitude=0,
                 phase=0.0):
        # a vertical lift looks for lift.png, a horizontal mover mover.png
        self.SPRITE_KIND = 'lift' if axis == 'y' else 'mover'
        super().__init__(x, y, width, height, altitude=altitude)
        # Steel palette (from PALETTE above) plus travel-direction chevrons,
        # so "this one moves, and along this axis" is readable from the
        # sprite alone without having to stand on it and find out. Skipped
        # when custom art is in use - the sprite is expected to say it.
        if not self.custom_art:
            # the base ledge is a shared cached surface (render_ledge_cached)
            # - copy it before stamping per-instance marks onto it, or every
            # platform of this size/palette would end up sharing the marks
            self.image = self.image.copy()
            self._draw_direction_marks(width, height, axis)
        self.axis = axis            # 'x' or 'y'
        self.travel = travel        # +/- pixels from base position
        self.period_frames = period_frames
        # where in its cycle this mover starts, 0..1 of a full period. This
        # is what lets a row of movers be timed against each other instead
        # of all swinging together.
        self.phase = float(phase) % 1.0
        self._t = 0
        self.delta_x = 0
        self.delta_y = 0
        # Start already at the right point in the cycle. update() would
        # correct this on the very next frame anyway, but placing it here
        # means a phased mover is never drawn once at the wrong position
        # before it starts running.
        start = self.travel * math.sin(self.phase * 2 * math.pi)
        if self.axis == 'x':
            self.rect.x = int(self.base_x + start)
        else:
            self.rect.y = int(self.base_y + start)

    def _draw_direction_marks(self, width, height, axis):
        """Stamp chevrons onto the slab pointing along its axis of travel."""
        outline, dark, body, cap_col, hi = self.PALETTE
        mark = _mix(cap_col, hi, 0.5)
        # Keep the marks inside the shaded body band, between the lit cap and
        # the bottom outline. A slab is only ~20px tall, so hardcoded offsets
        # ran the lower chevron straight off the edge - derive them instead.
        cap_h = min(6, max(3, height // 4))
        band_top, band_bottom = cap_h + 1, height - 2
        cx = width // 2
        cy = (band_top + band_bottom) // 2
        reach = max(2, min(5, (band_bottom - band_top) // 2 - 1))

        # skip on narrow slabs - the marks would collide with each other and
        # with the rivets, and read as noise rather than as direction
        if width >= 48:
            if axis == 'x':
                for sx in (cx - 12, cx + 12):
                    d = -4 if sx < cx else 4
                    pygame.draw.lines(self.image, mark, False,
                                      [(sx - d, cy - 4), (sx + d, cy), (sx - d, cy + 4)], 2)
            else:
                for tip, base in ((cy - reach, cy - reach + 3),
                                  (cy + reach, cy + reach - 3)):
                    pygame.draw.lines(self.image, mark, False,
                                      [(cx - 4, base), (cx, tip), (cx + 4, base)], 2)
        # rivets at both ends to sell it as a machined part
        for rx in (3, width - 4):
            pygame.draw.circle(self.image, dark, (rx, height - 5), 2)
            self.image.set_at((rx, height - 6), mark)

    def update(self):
        self._t += 1
        prev_x, prev_y = self.rect.x, self.rect.y
        # smooth sine oscillation rather than a linear back-and-forth -
        # eases in/out at the turnaround points instead of snapping
        # direction instantly, which reads better and is more predictable
        # to time a jump against.
        angle = ((self._t / self.period_frames) + self.phase) * 2 * math.pi
        offset = self.travel * math.sin(angle)
        if self.axis == 'x':
            self.rect.x = int(self.base_x + offset)
        else:
            self.rect.y = int(self.base_y + offset)
        self.delta_x = self.rect.x - prev_x
        self.delta_y = self.rect.y - prev_y

    @classmethod
    def from_spec(cls, spec, ground_y):
        x = spec['x']
        w = spec['w']
        h = spec.get('h', 0)
        height = spec.get('height', 20)
        # An explicit 'phase' wins; otherwise derive one from the mover's
        # position so movers don't silently share a clock. Set phase
        # deliberately (0, 0.5, ...) when you want them synchronised or
        # offset by an exact fraction of a cycle.
        phase = spec.get('phase')
        if phase is None:
            phase = cls.auto_phase(spec['x'], h)
        return cls(x, ground_y - h, w, height,
                   axis=spec.get('axis', 'x'),
                   travel=spec.get('travel', 80),
                   period_frames=spec.get('period', 120),
                   altitude=h,
                   phase=phase)
