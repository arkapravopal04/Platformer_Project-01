import pygame
import math


class Platform(pygame.sprite.Sprite):

    def __init__(self, x, y, width, height=20, color=(120, 90, 60)):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        pygame.draw.rect(self.image, (170, 140, 100), (0, 0, width, 4))
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.base_x = float(x)
        self.base_y = float(y)

    def update(self):
        pass


class MovingPlatform(Platform):
    

    def __init__(self, x, y, width, height=20, color=(90, 110, 150),
                 axis='x', travel=80, period_frames=120):
        super().__init__(x, y, width, height, color)
        self.axis = axis
        self.travel = travel  
        self.period_frames = period_frames
        self._t = 0

    def update(self):
        self._t += 1
        phase = (self._t / self.period_frames) * 2 * math.pi
        offset = self.travel * math.sin(phase)
        if self.axis == 'x':
            self.rect.x = int(self.base_x + offset)
        else:
            self.rect.y = int(self.base_y + offset)


class Hazard(pygame.sprite.Sprite):
   

    def __init__(self, x, y, width, height=16, damage=15, color=(180, 40, 40)):
        super().__init__()
        self.damage = damage
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
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

    hops0 = [(90, 180, 0), (50, 170, 55), (60, 170, 55), (60, 180, 55)]
    leg0, ref, h = _build_leg(spawn_x, 1, hops0, 0)

    turn1_gap, turn1_w = 100, 30
    turn1_h = h + 55
    turn1_x = ref + turn1_gap
    turn1 = (turn1_x, turn1_w, turn1_h)

    hops1 = [(150, 170, 20), (150, 160, 20), (140, 170, 20)]
    leg1, ref, h = _build_leg(turn1_x, -1, hops1, turn1_h)

    turn2_gap, turn2_w = 130, 40
    turn2_h = h + 55
    turn2_right = ref - turn2_gap
    turn2_x = turn2_right - turn2_w
    turn2 = (turn2_x, turn2_w, turn2_h)

    hops2 = [(240, 190, 25), (170, 190, 25)]
    leg2, ref, h = _build_leg(turn2_x + turn2_w, 1, hops2, turn2_h)
    turn3_gap, turn3_w = 235, 40
    turn3_h = h + 55
    turn3_x = ref + turn3_gap
    turn3 = (turn3_x, turn3_w, turn3_h)

    mp_travel = 45
    hops3a = [(210, 190, 25)]
    leg3a, ref, h = _build_leg(turn3_x, -1, hops3a, turn3_h)

    mp_gap, mp_w = 190, 110
    mp_h = h + 25
    mp_x = (ref - mp_gap) - mp_w
    leg3_moving = (mp_x, mp_w, mp_h)

    hops3b = [(150, 190, 25)]
    leg3b, ref, h = _build_leg(mp_x - mp_travel, -1, hops3b, mp_h)

    turn4_gap, turn4_w = 90, 30
    turn4_h = h + 60
    turn4_right = ref - turn4_gap
    turn4_x = turn4_right - turn4_w
    turn4 = (turn4_x, turn4_w, turn4_h)

    hops4 = [(300, 200, 30)]
    leg4, ref, h = _build_leg(turn4_x + turn4_w, 1, hops4, turn4_h)

    gate_gap, gate_w = 300, 200
    gate_h = h + 40
    gate_x = ref + gate_gap
    gate = (gate_x, gate_w, gate_h)

    hazard_specs = [
        (leg0[0][0] + leg0[0][1] + 10, 60, 0),
        (leg0[1][0] + leg0[1][1] + 10, 60, 0),
        (leg1[0][0] - 60, 70, leg1[0][2] - 40),
        (leg2[0][0] + leg2[0][1] + 15, 70, leg2[0][2] - 40),
        (leg3_moving[0] + leg3_moving[1] + 15, 70, leg3_moving[2] - 40),
        (leg4[0][0] - 70, 70, leg4[0][2] - 40),
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
        hy = ground_y - height_above_ground - 16
        hazards.add(Hazard(hx, hy, hw))

    return {'platforms': platforms, 'hazards': hazards}