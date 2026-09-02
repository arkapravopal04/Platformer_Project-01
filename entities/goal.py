import math

import pygame

from .base import Entity, register


@register("goal")
class Goal(Entity):
    """The finish marker at the summit of the course.

    Purely a collision target, same arrangement as Hazard: main.py tests it
    against the player each frame and raises the win state. It animates a
    gentle bob so the eye is drawn to it from a distance - it is the only
    thing in the level that is meant to say "come here".
    """

    TAGS = frozenset({"trigger"})
    DRAW_LAYER = 3

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

    @classmethod
    def from_spec(cls, spec, ground_y):
        """`x` is expected to already be the goal's own final top-left x
        (callers typically center it on a platform's rect themselves,
        since that centering depends on the platform's post-scale width);
        `h` is the height-above-ground of the surface it stands on."""
        x = spec['x']
        h = spec.get('h', 0)
        width = spec.get('w', 26)
        height = spec.get('height', 44)
        return cls(x, ground_y - h - height, width, height)
