import importlib
import sys

import pygame

import segments
from platforms import build_entities

# Every segment module under segments/, in filename order - seg_00_...,
# seg_01_..., seg_02_..., etc. Loaded once at import time; add a new file
# and it slots into the cycle automatically, no registry to maintain (see
# segments.discover_names for the directory-listing/fallback split).
SEGMENT_MODULES = [
    importlib.import_module(f'segments.{name}')
    for name in segments.discover_names()
]

class _EmptySegment:
    """Stand-in used when segments/ holds no segment modules at all.

    A cleared level still has to run: the tower needs *something* to stack,
    or the cycle arithmetic divides by zero. This contributes pure empty
    space, so the world is just the ground floor plus sky - exactly the
    blank slate you want to start building into with creative mode (F4).
    """
    __name__ = 'segments.(empty)'
    HEIGHT = 400
    ENTITIES = []


# How far above the player to keep the tower materialised - must comfortably
# clear one screen height so nothing pops in on screen.
LOOKAHEAD = 900

# How far below the player to keep it materialised. Generous on purpose: the
# ratchet scoring means falling is meant to be recoverable, so the platforms
# you fell past have to still be there on the way back up.
CULL_MARGIN = 1200

# Extra slack, in px, kept beyond the [low_h, high_h] window before a live
# segment is torn down - see ensure_window. Small relative to CULL_MARGIN/
# LOOKAHEAD; only smooths teardown timing at the boundary.
CULL_HYSTERESIS = 150

# Once the authored segments have all been used once, the tower keeps going
# by cycling only the LAST `CYCLE_TAIL` of them - the hardest ones, since
# segments are ordered easiest-first by filename. Without this the climb
# would drop back to the tutorial segment every time it wrapped.
# Keep this EVEN if your segments alternate which side of the map they exit
# on, so the wrap lands on a segment whose ENTRY matches.
CYCLE_TAIL = 4

# Safety cap on how many segments one call may add to the plan, so a stray
# huge target can't stall a frame on an unbounded loop. Deliberate large
# jumps (the F3 warp) pass their own higher value.
MAX_BUILD_PER_CALL = 25


def reload_segments():
    """Re-import every segment module fresh from disk, picking up edits
    without restarting the game. Used by main.py's F5 hot-reload - call
    this, then Tower.rebuild(), to see a segment file's changes live.
    """
    global SEGMENT_MODULES
    # Without this, a segment file created since startup (e.g. one creative
    # mode just exported) is invisible to iter_modules - Python caches
    # directory listings per import path.
    importlib.invalidate_caches()
    fresh = []
    for name in segments.discover_names():
        mod_name = f'segments.{name}'
        if mod_name in sys.modules:
            fresh.append(importlib.reload(sys.modules[mod_name]))
        else:
            fresh.append(importlib.import_module(mod_name))
    SEGMENT_MODULES = fresh


class Tower:
    """Stitches segment modules end-to-end into one endless vertical course.

    Split into a *plan* and *live* entities. The plan - which segment sits
    at which height - is decided once and never thrown away; only the
    sprites are created and destroyed as the player moves. That is what
    makes descending work: a segment you climbed past and left behind is
    rebuilt identically when you come back down, instead of leaving a void
    to fall through.

    Owns one persistent pygame.sprite.Group per tag (see entities.Entity.TAGS)
    so callers can bind player.set_platforms(tower.groups['landable']) once
    and have it stay valid as segments stream in and out.
    """

    def __init__(self, ground_y):
        self.ground_y = ground_y
        self.groups = {
            'landable': pygame.sprite.Group(),
            'blocking': pygame.sprite.Group(),
            'damaging': pygame.sprite.Group(),
        }
        # the plan: [(base_h, top_h, module_index)], bottom-up, permanent
        self._plan = []
        # plan index -> [entities], only for the ones currently materialised
        self._live = {}
        # plan indices creative mode has taken over for editing; kept
        # dematerialised so the draft copy isn't drawn on top of the original
        self._suppressed = set()
        # Authoring aid: show each segment only where it FIRST appears, and
        # leave the repeats empty. The tower is endless by repeating the
        # authored segments, so a level with only one or two of them stacks
        # the same geometry over and over - while building that reads as
        # "my block got duplicated infinitely upward". Creative mode turns
        # this on so you see what you actually wrote, once.
        self.hide_repeats = False
        self.draw_list = []
        self.ensure_window(0, LOOKAHEAD)

    # -- plan ------------------------------------------------------------
    @staticmethod
    def _module_for_index(index):
        """Which segment to place at position `index` in the stack. The
        authored segments play through once in order, then only the top
        `CYCLE_TAIL` of them repeat - see CYCLE_TAIL."""
        count = len(SEGMENT_MODULES)
        if count == 0:
            return _EmptySegment          # cleared level - see _EmptySegment
        if index < count:
            return SEGMENT_MODULES[index]
        tail_start = max(0, count - CYCLE_TAIL)
        tail_len = count - tail_start
        return SEGMENT_MODULES[tail_start + (index - count) % tail_len]

    def _extend_plan_to(self, target_h, max_build):
        built = 0
        while (not self._plan or self._plan[-1][1] < target_h) and built < max_build:
            index = len(self._plan)
            base_h = self._plan[-1][1] if self._plan else 0
            module = self._module_for_index(index)
            self._plan.append((base_h, base_h + module.HEIGHT, index))
            built += 1

    # -- materialising ---------------------------------------------------
    def _materialise(self, plan_index):
        base_h, _top_h, module_index = self._plan[plan_index]
        module = self._module_for_index(module_index)
        specs = [dict(spec, h=spec.get('h', 0) + base_h) for spec in module.ENTITIES]
        entities, by_tag = build_entities(specs, self.ground_y)
        for tag, group in by_tag.items():
            self.groups.setdefault(tag, pygame.sprite.Group()).add(group)
        return entities

    def prewarm_render_cache(self):
        """Force-build every authored segment once, then immediately throw
        the entities away. Meant to run once at startup, before the game
        loop, so every block shape/size the tower will ever need is already
        in render.py's/tiles.py's surface caches - no play session pays a
        first-render cost mid-climb.

        Only the authored segments (not the endless cycled tail) need this:
        CYCLE_TAIL repeats them forever, so the full authored set is already
        every combination of block kind/size the tower can ever produce.
        Segments ensure_window() already made live (the real starting
        window) are left alone - this only touches ground not otherwise
        covered, and never changes what's actually live on screen.
        """
        total_authored = sum(module.HEIGHT for module in SEGMENT_MODULES)
        if total_authored <= 0:
            return
        start_len = len(self._plan)
        self._extend_plan_to(total_authored, max_build=len(SEGMENT_MODULES) + 1)
        for index in range(start_len, len(self._plan)):
            if index in self._live:
                continue
            for entity in self._materialise(index):
                entity.kill()

    def _dematerialise(self, plan_index):
        for entity in self._live.pop(plan_index, ()):
            entity.kill()   # removes it from every group it's in

    def ensure_window(self, low_h, high_h, max_build=MAX_BUILD_PER_CALL):
        """Make exactly the segments overlapping [low_h, high_h] live, and
        nothing else. Extends the plan upward as needed. Call this once a
        frame with the player's altitude band - it both streams in ahead and
        tears down behind, and correctly restores anything the player is
        descending back into.

        Returns True if anything was materialised or torn down this call -
        callers that only care about steady-state frame cost (e.g. a perf
        overlay) can use this to tell "a segment just streamed in" frames
        apart from plain frames."""
        self._extend_plan_to(high_h, max_build)
        first_only = self._first_occurrences() if self.hide_repeats else None
        # Cull with extra slack beyond [low_h, high_h] so a player hovering
        # right at the boundary (a bounce, a slow climb) doesn't tear a
        # segment down and immediately rebuild it every frame - build still
        # only happens strictly inside the window, this only delays teardown.
        keep_low = low_h - CULL_HYSTERESIS
        keep_high = high_h + CULL_HYSTERESIS
        changed = False
        for index, (base_h, top_h, _module_index) in enumerate(self._plan):
            allowed = (index not in self._suppressed
                       and (first_only is None or index in first_only))
            in_build_range = top_h >= low_h and base_h <= high_h
            in_keep_range = top_h >= keep_low and base_h <= keep_high
            live = index in self._live
            if in_build_range and allowed and not live:
                self._live[index] = self._materialise(index)
                changed = True
            elif live and (not in_keep_range or not allowed):
                self._dematerialise(index)
                changed = True
        if changed:
            self._refresh_draw_list()
        return changed

    def _first_occurrences(self):
        """Plan indices where each module appears for the first time. Used
        by hide_repeats so authoring shows one copy of each segment."""
        seen = set()
        out = set()
        for index, (_b, _t, module_index) in enumerate(self._plan):
            name = self._module_for_index(module_index).__name__
            if name not in seen:
                seen.add(name)
                out.add(index)
        return out

    def _refresh_draw_list(self):
        live = [e for index in sorted(self._live) for e in self._live[index]]
        live.sort(key=lambda e: e.DRAW_LAYER)
        self.draw_list = live

    # -- creative-mode support -------------------------------------------
    def suppress(self, plan_index):
        """Hide one planned segment - creative mode uses this while editing
        a copy of it, so the original isn't drawn underneath the draft."""
        self._suppressed.add(plan_index)
        self._dematerialise(plan_index)
        self._refresh_draw_list()

    def suppress_all(self):
        """Hide every planned segment - creative mode's blank canvas. The
        plan is untouched, so unsuppress_all() (or F5) brings it all back;
        nothing is removed from disk."""
        self._suppressed.update(range(len(self._plan)))
        for index in list(self._live):
            self._dematerialise(index)
        self._refresh_draw_list()

    def unsuppress_all(self):
        self._suppressed.clear()

    def entity_at(self, point):
        """(entity, plan_index) for the live level entity under a world
        point, or None. Lets creative mode right-click real geometry, not
        just things placed this session."""
        for index, entities in self._live.items():
            for entity in reversed(entities):
                if entity.rect.collidepoint(point):
                    return entity, index
        return None

    def find_segment_base(self, module_short_name, search_limit=60):
        """Height of the first planned segment using the named module,
        extending the plan if needed. Used after a save to warp the player
        into what they just saved."""
        for _ in range(search_limit):
            for base_h, _top_h, module_index in self._plan:
                if self._module_for_index(module_index).__name__.endswith(
                        module_short_name):
                    return base_h
            self._extend_plan_to(self._plan[-1][1] + 1 if self._plan else 1, 1)
        return None

    def plan_index_at(self, h):
        """Index into the plan of the segment containing height h, or None."""
        for index, (base_h, top_h, _m) in enumerate(self._plan):
            if base_h <= h < top_h:
                return index
        return None

    # -- queries ----------------------------------------------------------
    def segment_base_at(self, h):
        """The floor height of the segment containing h - i.e. the h=0 a
        segment file written for this position would be measured against."""
        index = self.plan_index_at(h)
        return self._plan[index][0] if index is not None else 0

    def segment_at(self, h):
        """Module name of the segment whose range contains h, or None."""
        index = self.plan_index_at(h)
        if index is None:
            return None
        return self._module_for_index(self._plan[index][2]).__name__

    def segment_seams(self, low_h, high_h):
        """(top_h, module_name) for every planned segment boundary between
        low_h and high_h - used by the F2 debug overlay."""
        return [(top_h, self._module_for_index(m).__name__)
                for _b, top_h, m in self._plan if low_h <= top_h <= high_h]

    # -- lifecycle ---------------------------------------------------------
    def extend_to(self, target_h, max_build=MAX_BUILD_PER_CALL):
        """Plan (and materialise) up to at least `target_h`. Used by the F3
        warp, which needs ground to exist before the player is moved."""
        self._extend_plan_to(target_h, max_build)
        self.ensure_window(target_h - CULL_MARGIN, target_h + LOOKAHEAD, max_build)

    def rebuild(self, target_h):
        """Throw away the plan and every live entity, and regenerate from
        the ground up against the current segment modules. Used by the F5
        hot-reload dev tool - call reload_segments() first, so edits to a
        segment file actually take effect."""
        for index in list(self._live):
            self._dematerialise(index)
        self._plan = []
        self._live = {}
        self._suppressed = set()
        self.draw_list = []
        self.ensure_window(0, target_h, max_build=10_000)
