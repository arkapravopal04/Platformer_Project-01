import pygame
import math


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

    def __init__(self, x, y, width, height=20, color=(120, 90, 60)):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        # lighter strip along the top so the landable surface reads clearly
        # at a glance, even as a plain placeholder color
        pygame.draw.rect(self.image, (170, 140, 100), (0, 0, width, 4))
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

    def __init__(self, x, y, width, height=20, color=(90, 110, 150),
                 axis='x', travel=80, period_frames=120):
        super().__init__(x, y, width, height, color)
        # a distinct color from static platforms so the player can tell
        # at a glance which ones move
        self.axis = axis            # 'x' or 'y'
        self.travel = travel        # +/- pixels from base position
        self.period_frames = period_frames
        self._t = 0
        self.delta_x = 0
        self.delta_y = 0

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

    def __init__(self, x, y, width=16, height=120, color=(70, 70, 80)):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        # a couple of darker vertical grooves so it reads as a solid
        # obstacle/pillar rather than another platform lying on its side
        groove_color = (45, 45, 52)
        pygame.draw.rect(self.image, groove_color, (width * 0.25, 0, max(2, width // 8), height))
        pygame.draw.rect(self.image, groove_color, (width * 0.65, 0, max(2, width // 8), height))
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

    def __init__(self, x, y, width, height=16, damage=15, color=(180, 40, 40)):
        super().__init__()
        self.damage = damage
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        # simple triangular spike strip so it reads as "don't touch"
        # rather than another platform
        spike_count = max(1, width // 14)
        spike_w = width / spike_count
        for i in range(spike_count):
            p1 = (i * spike_w, height)
            p2 = (i * spike_w + spike_w / 2, 0)
            p3 = ((i + 1) * spike_w, height)
            pygame.draw.polygon(self.image, color, [p1, p2, p3])
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self):
        pass


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

    return {'platforms': platforms, 'hazards': hazards, 'walls': walls}