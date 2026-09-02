"""The backdrop: sky gradient, then an animated background that changes as
you climb.

Two things are configurable here and nothing else needs touching:

    BACKGROUND_BANDS  - which artwork appears at which altitude
    FRAME_COUNT / FRAME_MS - how many frames each background has, and how
                             fast they play

Drop art into backgrounds/<folder>/frame_1.png ... frame_3.png and it is
picked up automatically. Any band with no art on disk renders a labelled
placeholder instead, so the band boundaries and the animation are visible
and testable before a single asset exists.
"""

import os

import pygame

# --- sky gradient ---------------------------------------------------------
# Altitude (world pixels above the starting ground) -> colour. Colours
# interpolate between consecutive stops, so the climb reads as one
# continuous gradient. The altitude-0 stop matches the flat '#4c76a5' fill
# the game used before this existed, so nothing changes near the ground.
SKY_STOPS = [
    (0,      (76, 118, 165)),
    (3000,   (54, 88, 130)),
    (8000,   (28, 46, 82)),
    (16000,  (12, 16, 40)),
    (26000,  (3, 4, 14)),
    (40000,  (0, 0, 4)),
]

BAND_COUNT = 24   # horizontal strips used to fake a per-pixel gradient


# --- animated backgrounds -------------------------------------------------
# (start_altitude, name, folder). Sorted by altitude, lowest first. A band
# runs from its own start_altitude up to the next one's. Add, remove or
# re-order freely - the only rule is that the first entry starts at 0.
#
# Art goes in backgrounds/<folder>/frame_1.png, frame_2.png, frame_3.png.
# Any size works (it is scaled to the screen height and tiled), but
# 640x360 or 1280x720 matches the game's aspect exactly.
BACKGROUND_BANDS = [
    (0,      'ground',  '01_ground'),
    (2500,   'cliffs',  '02_cliffs'),
    (7000,   'clouds',  '03_clouds'),
    (14000,  'storm',   '04_storm'),
    (24000,  'void',    '05_void'),
]

FRAME_COUNT = 3      # frames per background
FRAME_MS = 200       # ms per frame, so 3 frames = 600ms a loop
FADE_HEIGHT = 700    # px over which one band cross-fades into the next
PARALLAX = 0.35      # 0 = pinned to the screen, 1 = moves with the world

BACKGROUND_DIR = os.path.join(os.path.dirname(__file__), 'backgrounds')

# distinct hues for the placeholder art, one per band, so an unstyled build
# still makes it obvious which band you are in
_PLACEHOLDER_HUES = [
    (96, 116, 82), (112, 96, 76), (92, 108, 132), (70, 68, 96), (40, 38, 56),
]


def band_at(altitude):
    """Index into BACKGROUND_BANDS for this altitude. Module-level because
    the platform tilesets key off the same bands - one definition of "which
    level am I in" drives both the backdrop and the block art."""
    index = 0
    for i, (start, _name, _folder) in enumerate(BACKGROUND_BANDS):
        if altitude >= start:
            index = i
        else:
            break
    return index


def band_folder(index):
    """Folder name for a band, e.g. '02_cliffs'. Shared by backgrounds/ and
    tiles/, so one theme is one folder name in both places."""
    return BACKGROUND_BANDS[index % len(BACKGROUND_BANDS)][2]


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _sky_colour(altitude):
    if altitude <= SKY_STOPS[0][0]:
        return SKY_STOPS[0][1]
    if altitude >= SKY_STOPS[-1][0]:
        return SKY_STOPS[-1][1]
    for (a0, c0), (a1, c1) in zip(SKY_STOPS, SKY_STOPS[1:]):
        if a0 <= altitude <= a1:
            return _lerp(c0, c1, (altitude - a0) / (a1 - a0))
    return SKY_STOPS[-1][1]


def draw_sky(screen, ground_y, camera):
    """Vertical gradient keyed to world altitude, banded rather than
    per-pixel for speed. Drawn first, behind everything."""
    width, height = screen.get_size()
    band_h = max(1, -(-height // BAND_COUNT))     # ceil, so no gaps
    for top in range(0, height, band_h):
        world_y = top - camera.offset.y
        pygame.draw.rect(screen, _sky_colour(max(0, ground_y - world_y)),
                         (0, top, width, band_h))


def _placeholder(name, index, frame, size):
    """Stand-in art for a band with no files yet: a flat tinted panel, the
    band's name, and a moving marker so the animation is visibly running."""
    width, height = size
    surf = pygame.Surface(size).convert()
    base = _PLACEHOLDER_HUES[index % len(_PLACEHOLDER_HUES)]
    surf.fill(base)

    # soft horizon band so it doesn't read as a solid colour
    pygame.draw.rect(surf, _lerp(base, (255, 255, 255), 0.10),
                     (0, int(height * 0.62), width, int(height * 0.38)))
    for i in range(0, width, 96):
        pygame.draw.line(surf, _lerp(base, (0, 0, 0), 0.18),
                         (i, 0), (i, height))

    font = pygame.font.Font(None, 30)
    label = font.render(f'{name}  [{frame + 1}/{FRAME_COUNT}]', True,
                        _lerp(base, (255, 255, 255), 0.65))
    surf.blit(label, label.get_rect(center=(width // 2, height // 2 - 14)))

    small = pygame.font.Font(None, 19)
    hint = small.render(f'backgrounds/{name}/frame_{frame + 1}.png', True,
                        _lerp(base, (255, 255, 255), 0.40))
    surf.blit(hint, hint.get_rect(center=(width // 2, height // 2 + 12)))

    # marker that steps across per frame - unmistakably animating
    step = width // (FRAME_COUNT + 1)
    pygame.draw.circle(surf, _lerp(base, (255, 255, 255), 0.8),
                       (step * (frame + 1), int(height * 0.78)), 7)
    return surf


class Backdrop:
    """Loads, animates and draws the banded background.

    Frames are loaded once on first use and cached per band, so a band you
    never reach costs nothing. Call update() once a frame and draw() before
    the level is blitted.
    """

    def __init__(self, ground_y, screen_size):
        self.ground_y = ground_y
        self.screen_size = screen_size
        self._frames = {}        # band index -> [Surface] * FRAME_COUNT
        self._elapsed = 0
        self.frame = 0

    # -- loading ---------------------------------------------------------
    def _load_band(self, index):
        """Frames for one band: real art if present, placeholders if not."""
        _start, name, folder = BACKGROUND_BANDS[index]
        directory = os.path.join(BACKGROUND_DIR, folder)
        frames = []
        for n in range(FRAME_COUNT):
            path = os.path.join(directory, f'frame_{n + 1}.png')
            image = None
            if os.path.isfile(path):
                try:
                    image = pygame.image.load(path).convert()
                except pygame.error:
                    image = None      # unreadable file: fall back, don't crash
            if image is None:
                image = _placeholder(folder, index, n, self.screen_size)
            else:
                image = self._fit(image)
            frames.append(image)
        return frames

    def _fit(self, image):
        """Scale art to the screen height, keeping its aspect ratio. Width is
        whatever it becomes - draw() tiles horizontally to cover."""
        screen_w, screen_h = self.screen_size
        if image.get_height() == screen_h:
            return image
        scale = screen_h / image.get_height()
        return pygame.transform.smoothscale(
            image, (max(1, int(image.get_width() * scale)), screen_h))

    def frames_for(self, index):
        if index not in self._frames:
            self._frames[index] = self._load_band(index)
        return self._frames[index]

    def reload(self):
        """Drop cached art so newly added files are picked up. Wired to F5
        alongside the segment hot-reload."""
        self._frames.clear()

    # -- band selection ---------------------------------------------------
    band_at = staticmethod(band_at)

    def _blend_at(self, altitude):
        """(index, next_index, t) - t is how far the current band has faded
        into the next one, 0..1. t stays 0 except in the FADE_HEIGHT window
        just below a boundary."""
        index = self.band_at(altitude)
        if index + 1 >= len(BACKGROUND_BANDS):
            return index, index, 0.0
        next_start = BACKGROUND_BANDS[index + 1][0]
        distance = next_start - altitude
        if distance > FADE_HEIGHT:
            return index, index, 0.0
        return index, index + 1, max(0.0, min(1.0, 1.0 - distance / FADE_HEIGHT))

    # -- drawing -----------------------------------------------------------
    def update(self, dt_ms):
        self._elapsed += dt_ms
        if self._elapsed >= FRAME_MS:
            self._elapsed %= FRAME_MS
            self.frame = (self.frame + 1) % FRAME_COUNT

    def _tile(self, screen, image, camera, alpha=None):
        screen_w, screen_h = screen.get_size()
        image_w, image_h = image.get_size()
        if alpha is not None:
            image = image.copy()
            image.set_alpha(alpha)
        # parallax: the backdrop drifts a fraction of the camera's movement,
        # so it reads as distance rather than as a sticker on the screen
        ox = int(-camera.offset.x * PARALLAX) % image_w - image_w
        oy = int(-camera.offset.y * PARALLAX) % image_h - image_h
        y = oy
        while y < screen_h:
            x = ox
            while x < screen_w:
                screen.blit(image, (x, y))
                x += image_w
            y += image_h

    def draw(self, screen, camera):
        """Sky gradient, then the current band (cross-fading into the next
        near a boundary). Call before drawing the level."""
        draw_sky(screen, self.ground_y, camera)
        altitude = max(0, self.ground_y - (-camera.offset.y + self.screen_size[1]))
        index, next_index, t = self._blend_at(altitude)
        self._tile(screen, self.frames_for(index)[self.frame], camera)
        if t > 0 and next_index != index:
            self._tile(screen, self.frames_for(next_index)[self.frame],
                       camera, alpha=int(t * 255))

    # -- authoring aid -----------------------------------------------------
    def describe(self, altitude):
        """'cliffs -> clouds 42%' for the debug overlay."""
        index, next_index, t = self._blend_at(altitude)
        name = BACKGROUND_BANDS[index][1]
        if t > 0 and next_index != index:
            return f'{name} -> {BACKGROUND_BANDS[next_index][1]} {int(t * 100)}%'
        return name
