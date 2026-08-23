import pygame
import math
import random


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
    rng = random.Random(seed)
    for _ in range(max(3, (width * height) // 70)):
        sx = rng.randrange(width)
        sy = rng.randrange(cap_h + 1, height) if height > cap_h + 1 else cap_h
        surf.set_at((sx, sy), _mix(body, dark, 0.75))

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


class Platform(pygame.sprite.Sprite):
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

    def __init__(self, x, y, width, height=20):
        super().__init__()
        # seed off the position so each slab gets its own stable grain
        self.image = _render_ledge(width, height, self.PALETTE, seed=(x * 31 + y))
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

    def update(self):
        """No-op for static platforms. Present so main.py can call
        obstacle_platforms.update() uniformly across the whole group
        without needing to know which platforms move and which don't."""
        pass


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

    def __init__(self, x, y, width, height=20,
                 axis='x', travel=80, period_frames=120):
        super().__init__(x, y, width, height)
        # Steel palette (from PALETTE above) plus travel-direction chevrons,
        # so "this one moves, and along this axis" is readable from the
        # sprite alone without having to stand on it and find out.
        self._draw_direction_marks(width, height, axis)
        self.axis = axis            # 'x' or 'y'
        self.travel = travel        # +/- pixels from base position
        self.period_frames = period_frames
        self._t = 0
        self.delta_x = 0
        self.delta_y = 0


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
        phase = (self._t / self.period_frames) * 2 * math.pi
        offset = self.travel * math.sin(phase)
        if self.axis == 'x':
            self.rect.x = int(self.base_x + offset)
        else:
            self.rect.y = int(self.base_y + offset)
        self.delta_x = self.rect.x - prev_x
        self.delta_y = self.rect.y - prev_y


class Wall(pygame.sprite.Sprite):
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

    Not a Platform subclass - the player never lands ON TOP of a wall in
    the normal sense (its top edge isn't meant to be a resting surface,
    though nothing stops a player from landing there if a jump happens
    to clear it exactly - it's simply not the intended path). Purely
    horizontal-collision, handled by Player._clamp_to_walls(), which
    main.py wires up via player.set_walls(course['walls']).
    """

    PALETTE = STONE_PALETTE

    def __init__(self, x, y, width=16, height=120):
        super().__init__()
        outline, dark, body, cap_col, hi = self.PALETTE
        self.image = _render_ledge(width, height, self.PALETTE,
                                   seed=(x * 17 + y), cap=False)

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

    def update(self):
        pass


class Hazard(pygame.sprite.Sprite):
    """A stationary damage source (spikes). Purely a collision target -
    Player doesn't currently check hazards on its own, so main.py's game
    loop is responsible for testing player/hazard overlap each frame and
    calling player.get_hit(amount) when they intersect (the same pattern
    already used for the debug 'H' key). Kept separate from Platform:
    hazards are never landable, so they're deliberately not a Platform
    subclass and won't get treated as ground by apply_gravity's
    platform-landing check.
    """

    PALETTE = RUST_PALETTE

    def __init__(self, x, y, width, height=16, damage=15):
        super().__init__()
        self.damage = damage
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

    def update(self):
        pass


class Goal(pygame.sprite.Sprite):
    """The finish marker at the summit of the course.

    Purely a collision target, same arrangement as Hazard: main.py tests it
    against the player each frame and raises the win state. It animates a
    gentle bob so the eye is drawn to it from a distance - it is the only
    thing in the level that is meant to say "come here".
    """

    def __init__(self, x, y, width=26, height=44):
        super().__init__()
        self.base_y = float(y)
        self._t = 0
        self.frames = [self._render(width, height, phase) for phase in range(4)]
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=(x, y))

    @staticmethod
    def _render(width, height, phase):
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pole_x = 3
        pygame.draw.rect(surf, (70, 62, 58), (pole_x, 0, 3, height))
        pygame.draw.line(surf, (150, 140, 132), (pole_x, 0), (pole_x, height - 1))

        # the banner ripples by shifting its trailing notch per phase
        wave = (0, 1, 0, -1)[phase]
        pygame.draw.polygon(surf, (240, 196, 60), [
            (pole_x + 3, 3),
            (width - 2, 9 + wave),
            (pole_x + 3, 20),
        ])
        pygame.draw.polygon(surf, (255, 232, 150), [
            (pole_x + 3, 3),
            (width - 8, 7 + wave),
            (pole_x + 3, 11),
        ])
        pygame.draw.circle(surf, (255, 244, 200), (pole_x + 1, 1), 2)
        return surf

    def update(self):
        self._t += 1
        self.image = self.frames[(self._t // 10) % 4]
        self.rect.y = int(self.base_y + math.sin(self._t / 22.0) * 2)


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


def create_obstacle_course(spawn_x, ground_y, world_width=None):
    LEFT_MARGIN = 60
    RIGHT_MARGIN = 60

    hops0 = [(80, 180, 0), (45, 170, 55), (50, 170, 55), (50, 180, 55)]
    leg0, ref, h = _build_leg(spawn_x, 1, hops0, 0)

    # walk/sprint gap, rises, near RIGHT edge 
    turn1_gap, turn1_w = 90, 30
    turn1_h = h + 55
    turn1_x = ref + turn1_gap
    turn1 = (turn1_x, turn1_w, turn1_h)

    #LEFT, sprint-jump gaps, one level up 
    hops1 = [(130, 170, 20), (130, 160, 20), (125, 170, 20)]
    leg1, ref, h = _build_leg(turn1_x, -1, hops1, turn1_h)

    # dash-jump gap, rises, near LEFT edge 
    turn2_gap, turn2_w = 120, 40
    turn2_h = h + 55
    turn2_right = ref - turn2_gap
    turn2_x = turn2_right - turn2_w
    turn2 = (turn2_x, turn2_w, turn2_h)

    #  RIGHT, dash/sprint-jump mix, higher up 
    hops2 = [(230, 190, 25), (155, 190, 25)]
    leg2, ref, h = _build_leg(turn2_x + turn2_w, 1, hops2, turn2_h)

    # dash-jump gap, rises, near RIGHT edge 
    turn3_gap, turn3_w = 225, 40
    turn3_h = h + 55
    turn3_x = ref + turn3_gap
    turn3 = (turn3_x, turn3_w, turn3_h)

    # LEFT, moving platform is its own hop 
    mp_travel = 45
    hops3a = [(205, 190, 25)]
    leg3a, ref, h = _build_leg(turn3_x, -1, hops3a, turn3_h)

    mp_gap, mp_w = 180, 110
    mp_h = h + 25
    mp_x = (ref - mp_gap) - mp_w
    leg3_moving = (mp_x, mp_w, mp_h)
    hops3b = [(145, 190, 25)]
    leg3b, ref, h = _build_leg(mp_x - mp_travel, -1, hops3b, mp_h)

    # short breather gap, rises, near LEFT edge 
    turn4_gap, turn4_w = 85, 30
    turn4_h = h + 60
    turn4_right = ref - turn4_gap
    turn4_x = turn4_right - turn4_w
    turn4 = (turn4_x, turn4_w, turn4_h)

    # RIGHT, dash-jump gap
    hops4 = [(295, 200, 30)]
    leg4, ref, h = _build_leg(turn4_x + turn4_w, 1, hops4, turn4_h)

    # final dash-jump gap to the summit near map top 
    gate_gap, gate_w = 295, 200
    gate_h = h + 40
    gate_x = ref + gate_gap
    gate = (gate_x, gate_w, gate_h)

    
    hazard_specs = [
        # (x, width, height_above_ground) - height_above_ground matches
        # the platform the hazard sits on, so it renders flush with that
        # platform's own top surface
        (leg0[1][0] + 10, 40, leg0[1][2]),
        (leg1[1][0] + leg1[1][1] - 50, 40, leg1[1][2]),
        (leg2[0][0] + 10, 40, leg2[0][2]),
        (leg3a[0][0] + leg3a[0][1] - 50, 40, leg3a[0][2]),
        (leg4[0][0] + leg4[0][1] - 50, 40, leg4[0][2]),
    ]

    wall_specs = [
        (turn1_x - 74, turn1_h, 69),               
        (turn2_x + turn2_w + 74, turn2_h, 69),     
        (turn3_x - 74, turn3_h, 69),               
        (turn4_x + turn4_w + 74, turn4_h, 69),   
    ]

    static_entries = (
        list(leg0) + [turn1] + list(leg1) + [turn2] + list(leg2) + [turn3]
        + list(leg3a) + list(leg3b) + [turn4] + list(leg4) + [gate]
    )
    moving_entries = [
        (leg3_moving[0], leg3_moving[1], leg3_moving[2],
         {'axis': 'x', 'travel': mp_travel, 'period_frames': 100}),
    ]

    all_x = [x for x, w, hh in static_entries] + [x for x, w, hh, extra in moving_entries]
    all_right = [x + w for x, w, hh in static_entries] + [x + w for x, w, hh, extra in moving_entries]
    natural_left = min(all_x)
    natural_right = max(all_right)
    natural_span = natural_right - natural_left

    scale = 1.0
    if world_width is not None:
        available = world_width - LEFT_MARGIN - RIGHT_MARGIN
        if available < natural_span:
            scale = max(0.4, available / natural_span)

    def scaled_x(x):
        if scale >= 1.0:
            return int(x)
        return int(LEFT_MARGIN + (x - natural_left) * scale)

    def scaled_w(width):
        return int(width * scale) if scale < 1.0 else width

    platforms = pygame.sprite.Group()
    hazards = pygame.sprite.Group()
    walls = pygame.sprite.Group()

    for x, w, height_above_ground in static_entries:
        px = scaled_x(x)
        py = ground_y - height_above_ground
        pw = scaled_w(w)
        platforms.add(Platform(px, py, pw))

    for x, w, height_above_ground, extra in moving_entries:
        px = scaled_x(x)
        py = ground_y - height_above_ground
        pw = scaled_w(w)
        travel = int(extra['travel'] * scale) if scale < 1.0 else extra['travel']
        platforms.add(MovingPlatform(
            px, py, pw,
            axis=extra['axis'], travel=travel, period_frames=extra['period_frames'],
        ))

    for x, w, height_above_ground in hazard_specs:
        hx = scaled_x(x)
        hw = scaled_w(w)
        hazard_height = 16
        # sit the spike strip ON TOP of the platform's own surface
        # (bottom of the hazard flush with the platform's top), not
        # embedded partway into it
        hy = ground_y - height_above_ground - hazard_height
        hazards.add(Hazard(hx, hy, hw, height=hazard_height))

    for x, height_above_ground, wall_height in wall_specs:
        wx = scaled_x(x)
        w_h = int(wall_height * scale) if scale < 1.0 else wall_height
        wy_bottom = ground_y - height_above_ground
        wy_top = wy_bottom - w_h
        walls.add(Wall(wx, wy_top, height=w_h))

    # finish marker, planted on top of the summit platform
    gate_px, gate_pw = scaled_x(gate[0]), scaled_w(gate[1])
    goal = Goal(gate_px + gate_pw // 2 - 13, ground_y - gate[2] - 44)

    return {'platforms': platforms, 'hazards': hazards, 'walls': walls,
            'goal': goal}