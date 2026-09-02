"""Windowed / fullscreen switching, in one place for both build targets.

The game is authored for a fixed 640x360 surface - the camera framing, the
HUD offsets and the segment layouts all assume it - so neither mode changes
that. What changes is only how big that surface gets drawn:

  * desktop, windowed - the 640x360 surface *is* the display, exactly the
    window the game has always opened. present() is a bare flip().
  * desktop, fullscreen - the display is opened at the monitor's own
    resolution and the game keeps drawing to an offscreen 640x360 surface,
    which present() scales up by a whole-number factor and centres. Whole
    numbers keep the pixel art crisp; the leftover edge stays black, so the
    aspect ratio never stretches. (pygame's SCALED flag does the same job in
    the driver, but only when it's set on the *first* set_mode call - asking
    for it on a later one fails with "failed to create renderer".)
  * web - pygbag already stretches its canvas over the whole viewport with
    CSS, so fullscreen is its default and needs nothing from us. Windowed
    injects a stylesheet pinning the canvas to 640x360. Its rules are
    !important because pygbag's resize handler assigns canvas.style.width
    and .height directly, and an important rule in a stylesheet is the one
    thing that outranks an element's own inline style.

Nothing here is allowed to take the game down: a driver that refuses a mode
switch, or a pygbag runtime whose JS interop doesn't have the shape we
expect, leaves the player in the mode they were already in.

Known limit: pygame reports mouse positions in display coordinates, so
clicks land offset from the cursor in fullscreen. That only affects
devmode's creative-mode authoring clicks (desktop-only, and authoring is
done in a window), not anything in normal play, which is keyboard-only.
"""

import sys
import pygame

WEB = sys.platform == 'emscripten'

# id of the <style> element we own on the web build, so repeated toggles
# reuse the one element instead of stacking new ones up in <head>
_STYLE_ID = 'rustbound-screen-mode'

# Applied on the web build in windowed mode; see the module docstring on why
# these are !important. inset + auto margins centre the fixed-size canvas,
# and the black page behind it keeps the letterboxing unobtrusive.
_WINDOWED_CSS = """
canvas#canvas {{
    width: {w}px !important;
    height: {h}px !important;
    position: absolute !important;
    inset: 0 !important;
    margin: auto !important;
    image-rendering: pixelated;
}}
html, body {{ background: #000 !important; }}
"""


def _style_element():
    """Our <style> element in the page's <head>, created on first use.
    None if the DOM isn't reachable (i.e. we aren't really on the web)."""
    try:
        import platform
        document = platform.document
        element = document.getElementById(_STYLE_ID)
        if element is None:
            element = document.createElement('style')
            element.id = _STYLE_ID
            document.head.appendChild(element)
        return element
    except Exception:
        return None


class ScreenMode:
    """Owns the display and which mode it's showing in.

    Opens windowed on desktop and fullscreen on web, where filling the
    browser tab is what the page already did before this existed. Draw to
    `.surface` (always 640x360) and call `.present()` in place of
    pygame.display.flip(); re-read `.surface` after every toggle(), since a
    desktop mode switch replaces it.
    """

    def __init__(self, size):
        self.size = size
        self.fullscreen = WEB
        self.display = pygame.display.set_mode(size)
        self.surface = self.display
        self._dest = None       # scaled-up rect the game is drawn into
        if WEB:
            self._apply_web_css()

    # --- desktop ---------------------------------------------------------

    def _open_windowed(self):
        self.display = pygame.display.set_mode(self.size)
        self.surface = self.display
        self._dest = None

    def _open_fullscreen(self):
        """Display at the monitor's resolution, game on its own surface."""
        try:
            self.display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        except pygame.error:
            # window manager refused - stay windowed rather than leaving the
            # game with no usable display
            self.fullscreen = False
            self._open_windowed()
            return
        self.surface = pygame.Surface(self.size).convert()
        game_w, game_h = self.size
        display_w, display_h = self.display.get_size()
        # whole-number scale so every game pixel stays a crisp square; a
        # display smaller than 640x360 falls back to fitting what it can
        scale = min(display_w // game_w, display_h // game_h) or 1
        width, height = game_w * scale, game_h * scale
        self._dest = pygame.Rect(0, 0, width, height)
        self._dest.center = (display_w // 2, display_h // 2)

    # --- web -------------------------------------------------------------

    def _apply_web_css(self):
        element = _style_element()
        if element is None:
            return
        try:
            element.innerHTML = '' if self.fullscreen else _WINDOWED_CSS.format(
                w=self.size[0], h=self.size[1])
        except Exception:
            pass

    # --- public ----------------------------------------------------------

    def toggle(self):
        """Flip between fullscreen and the fixed-size window, and return the
        surface to draw on from here on."""
        self.fullscreen = not self.fullscreen
        if WEB:
            self._apply_web_css()
        elif self.fullscreen:
            self._open_fullscreen()
        else:
            self._open_windowed()
        return self.surface

    def present(self):
        """Put this frame on screen - flip(), plus the scale-and-centre step
        when the game surface isn't the display itself."""
        if self._dest is not None:
            self.display.fill((0, 0, 0))
            self.display.blit(
                pygame.transform.scale(self.surface, self._dest.size),
                self._dest)
        pygame.display.flip()
