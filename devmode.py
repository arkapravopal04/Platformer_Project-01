"""Creative mode - an authoring-only sandbox layered on top of the game.

Toggled with F4. It exists to answer two questions quickly while building
segments:

  "Can I actually make that jump from here?"
      Press J. Every arc the player could fly from their current stance is
      drawn, and every platform in range is outlined in green (reachable in
      one hop) or red (not). No guessing, no repeated attempts.

  "Where exactly should this go?"
      Click to place, drag to move, right-click to delete - on new pieces
      AND on the segments already in the level. E saves, reloads and drops
      you straight into what you just saved.

Nothing here runs unless creative mode is on, and saving writes a normal
segment module - so anything built with it is plain hand-editable Python
afterwards, not a binary level format.
"""

import os

import pygame

import reach
from entities import ENTITY_TYPES
from entities.trapdoor import TILE_W as TRAPDOOR_W, TILE_H as TRAPDOOR_H
from platforms import build_entities

# The authoring palette: (type name, label, default width, extra spec fields).
#
# These are VARIANTS, not just types - one entity type can appear several
# times with different defaults. That is how the vertical lift gets its own
# slot: it is the same 'moving' entity as the horizontal mover, distinguished
# only by axis='y', so keying the palette off the type registry alone left it
# unreachable. Anything registered in entities/ but not covered here is
# appended automatically, so a newly registered type is still placeable
# without editing this list.
PALETTE_VARIANTS = [
    ('platform', 'platform',  140, {}),
    ('moving',   'mover-LR',  120, {'axis': 'x', 'travel': 60, 'period': 110}),
    ('moving',   'lift-UD',   110, {'axis': 'y', 'travel': 40, 'period': 130}),
    ('wall',     'wall',       16, {'height': 60}),
    ('hazard',   'spikes',     40, {}),
    ('trapdoor', 'trapdoor',   TRAPDOOR_W, {'height': TRAPDOOR_H}),
    ('goal',     'goal',       26, {}),
]
FALLBACK_WIDTH = 100

# types whose spec carries no 'w' (they define their own width)
NO_WIDTH = {'wall'}

GRID_SIZES = [5, 10, 20, 25]
FLY_SPEED = 7
FLY_SPEED_FAST = 16

# overlay colours, kept clear of the earth/steel/stone/rust obstacle palettes
# so dev drawing never reads as part of the level
C_OK = (86, 214, 122)
C_NO = (224, 92, 78)
C_ARC_SPRINT = (255, 214, 92)
C_ARC_DASH = (120, 196, 255)
C_GRID = (255, 255, 255)
C_FLOOR = (255, 132, 216)
C_DRAFT = (255, 255, 255)

EXPORT_NAME = 'seg_99_draft'
SEGMENT_DIR = os.path.join(os.path.dirname(__file__), 'segments')


def placeable_types():
    """The full palette: every variant above whose type is registered, plus
    a plain entry for any registered type the list doesn't mention. So
    "all the blocks" means all of them, including ones added later."""
    out = [v for v in PALETTE_VARIANTS if v[0] in ENTITY_TYPES]
    covered = {v[0] for v in out}
    for name in sorted(t for t in ENTITY_TYPES if t not in covered):
        out.append((name, name, FALLBACK_WIDTH, {}))
    return out


def _snap(value, grid):
    return int(round(value / grid) * grid)


class DevMode:
    """Holds all creative-mode state. One instance lives for the whole run;
    `active` gates everything, so a normal play session never touches it."""

    def __init__(self, ground_y, world_width=reach.WORLD_WIDTH):
        self.ground_y = ground_y
        self.world_width = world_width
        self.active = False
        self.noclip = True        # fly by default - it's why you came here
        self.show_arcs = True
        self.show_grid = True
        self.blank = False        # hide every real segment: a clean canvas
        self.grid_index = 1
        self.types = placeable_types()
        self.type_index = 0
        self.width = self.types[0][2]
        # working copy of the selected variant's extra fields, so travel /
        # period can be tuned in-game before placing
        self.extras = dict(self.types[0][3])
        # draft specs carry ABSOLUTE h (above ground_y); saving converts to
        # segment-local h by subtracting floor_h
        self.draft = []
        self.floor_h = 0
        self.preview_entities = []
        self._groups = None       # tower.groups, so drafts become solid
        # when set, the draft IS an existing segment opened for editing, and
        # saving writes back over that file instead of the scratch draft
        self.editing = None       # module short name, e.g. 'seg_03_spike_alley'
        self.editing_doc = None
        self._drag = None
        # set by save(); main.py picks it up, reloads the tower and warps the
        # player into what was just saved - otherwise a new segment lands
        # several hundred metres up and saving looks like it did nothing
        self.pending_reload = None
        self.message = ''
        self.message_until = 0

    # -- helpers ---------------------------------------------------------
    @property
    def grid(self):
        return GRID_SIZES[self.grid_index % len(GRID_SIZES)]

    @property
    def current(self):
        return self.types[self.type_index % len(self.types)]

    def notify(self, text):
        self.message = text
        self.message_until = pygame.time.get_ticks() + 3200
        print(f'[creative] {text}')   # also to the console, so nothing is missed

    def world_mouse(self, camera):
        mx, my = pygame.mouse.get_pos()
        return mx - camera.offset.x, my - camera.offset.y

    def select_type(self, index):
        self.type_index = index % len(self.types)
        self.width = self.current[2]
        self.extras = dict(self.current[3])
        self.notify(f'placing {self.current[1]}')

    def nudge_period(self, delta):
        """Adjust how long a full out-and-back cycle takes, in frames."""
        if 'period' not in self.extras:
            self.notify(f'{self.current[1]} has no period to adjust')
            return
        self.extras['period'] = max(20, self.extras['period'] + delta)
        secs = self.extras['period'] / 60.0
        self.notify(f'period {self.extras["period"]} frames ({secs:.1f}s a cycle)')

    def cycle_phase(self):
        """Step the placed mover's starting point through the cycle in
        eighths. Movers left un-phased are auto-offset from their position
        so they don't share a clock; setting it explicitly is how you time
        two of them against each other - 0.5 makes a pair exactly opposed.
        """
        if 'travel' not in self.extras:
            self.notify(f'{self.current[1]} has no phase to set')
            return
        current = self.extras.get('phase', 0.0)
        nxt = round((current + 0.125) % 1.0, 3)
        self.extras['phase'] = nxt
        self.notify(f'phase {nxt} ({int(nxt * 360)} deg into the cycle)')

    def nudge_travel(self, delta):
        """Adjust the selected mover's travel distance before placing it.
        No-op for types that don't travel."""
        if 'travel' not in self.extras:
            self.notify(f'{self.current[1]} has no travel to adjust')
            return
        self.extras['travel'] = max(0, self.extras['travel'] + delta)
        axis = self.extras.get('axis', 'x')
        self.notify(f'travel {self.extras["travel"]}px '
                    f'({"up/down" if axis == "y" else "left/right"})')

    # -- lifecycle -------------------------------------------------------
    def toggle(self, player, tower):
        self.active = not self.active
        self._groups = tower.groups
        if self.active:
            player_h = max(0, self.ground_y - player.rect.bottom)
            self.floor_h = tower.segment_base_at(player_h)
            self.notify(f'creative ON - floor h={self.floor_h} '
                        f'(repeats hidden; O edits, E saves)')
        else:
            self.notify('creative OFF')

    def fly(self, player):
        """Free movement with gravity and collision bypassed."""
        keys = pygame.key.get_pressed()
        speed = FLY_SPEED_FAST if keys[pygame.K_LSHIFT] else FLY_SPEED
        if keys[pygame.K_a]:
            player.rect.x -= speed
            player.direction = 'left'
        if keys[pygame.K_d]:
            player.rect.x += speed
            player.direction = 'right'
        if keys[pygame.K_w]:
            player.rect.y -= speed
        if keys[pygame.K_s]:
            player.rect.y += speed
        # Stay inside the map. Without this you can fly off the side into
        # empty space, and turning noclip back off drops you somewhere the
        # level does not exist.
        player.rect.left = max(0, player.rect.left)
        player.rect.right = min(self.world_width, player.rect.right)
        player.rect.bottom = min(self.ground_y, player.rect.bottom)
        player.vertical_momentum = 0
        player.is_on_ground = True
        player.is_jump = False
        player.standing_platform = None
        player.status = 'idle'
        player.animation_state()

    # -- draft editing ---------------------------------------------------
    def place(self, camera):
        wx, wy = self.world_mouse(camera)
        grid = self.grid
        name = self.current[0]
        spec = {'type': name,
                'x': _snap(wx - self.width / 2, grid),
                'h': _snap(self.ground_y - wy, grid)}
        if name not in NO_WIDTH:
            spec['w'] = self.width
        spec.update(self.extras)
        self.draft.append(spec)
        self._rebuild_preview()

    def draft_index_at(self, camera):
        wx, wy = self.world_mouse(camera)
        point = (int(wx), int(wy))
        for i in range(len(self.preview_entities) - 1, -1, -1):
            if self.preview_entities[i].rect.collidepoint(point):
                return i
        return None

    def delete_at(self, camera, tower, player):
        """Delete the piece under the cursor. If it belongs to a real segment
        rather than the draft, that segment is opened for editing first - so
        right-click erases level geometry too, not only things placed this
        session."""
        index = self.draft_index_at(camera)
        if index is not None:
            del self.draft[index]
            self._rebuild_preview()
            return
        wx, wy = self.world_mouse(camera)
        hit = tower.entity_at((int(wx), int(wy)))
        if hit is None:
            self.notify('nothing under the cursor')
            return
        _entity, plan_index = hit
        if self.editing is None:
            self.adopt(tower, player, plan_index=plan_index)
        again = self.draft_index_at(camera)
        if again is not None:
            del self.draft[again]
            self._rebuild_preview()

    def start_drag(self, camera, index):
        wx, wy = self.world_mouse(camera)
        spec = self.draft[index]
        self._drag = (index, spec['x'] - wx, spec['h'] - (self.ground_y - wy))

    def drag_to(self, camera):
        if self._drag is None:
            return
        index, off_x, off_h = self._drag
        wx, wy = self.world_mouse(camera)
        spec = self.draft[index]
        new_x = _snap(wx + off_x, self.grid)
        new_h = _snap((self.ground_y - wy) + off_h, self.grid)
        if (new_x, new_h) != (spec['x'], spec['h']):
            # only rebuild sprites when the snapped cell actually changes, so
            # a drag doesn't re-render the whole draft on every mouse event
            spec['x'], spec['h'] = new_x, new_h
            self._rebuild_preview()

    def end_drag(self):
        self._drag = None

    def undo(self):
        if self.draft:
            self.draft.pop()
            self._rebuild_preview()
        else:
            self.notify('nothing to undo')

    # -- editing a real segment -------------------------------------------
    def adopt(self, tower, player, plan_index=None):
        """Open a real segment for editing: load its ENTITIES into the draft
        and hide the original, so what you see and drag around IS that
        segment. Saving then writes back over its own file."""
        if self.editing is not None and plan_index is None:
            self.release(tower)
            return
        if plan_index is None:
            h = max(0, self.ground_y - player.rect.bottom)
            plan_index = tower.plan_index_at(h)
        if plan_index is None:
            self.notify('no segment here to edit')
            return
        base_h, _top_h, module_index = tower._plan[plan_index]
        module = tower._module_for_index(module_index)
        # segment ENTITIES carry LOCAL h; the draft works in absolute h
        self.draft = [dict(spec, h=spec.get('h', 0) + base_h)
                      for spec in module.ENTITIES]
        self.floor_h = base_h
        self.editing = module.__name__.rsplit('.', 1)[-1]
        self.editing_doc = module.__doc__
        tower.suppress(plan_index)
        self._rebuild_preview()
        self.notify(f'editing {self.editing} - {len(self.draft)} pieces, E to save')

    def release(self, tower):
        name = self.editing
        self.editing = None
        self.editing_doc = None
        self.draft = []
        self._rebuild_preview()
        tower.unsuppress_all()
        self.notify(f'closed {name} without saving' if name else 'draft cleared')

    def toggle_blank(self, tower):
        """Hide (or restore) every real segment, for building on an empty
        canvas. Nothing is deleted from disk - F5 brings it all back."""
        self.blank = not self.blank
        if self.blank:
            tower.suppress_all()
            self.notify('level hidden - blank canvas (Delete again to restore)')
        else:
            tower.unsuppress_all()
            self.notify('level restored')

    def _rebuild_preview(self):
        for entity in self.preview_entities:
            entity.kill()
        self.preview_entities = []
        if not self.draft:
            return
        entities, by_tag = build_entities(self.draft, self.ground_y)
        self.preview_entities = entities
        # make the draft immediately solid, so you can jump on what you just
        # placed instead of saving and reloading to try it
        if self._groups is not None:
            for tag, group in by_tag.items():
                self._groups.setdefault(tag, pygame.sprite.Group()).add(group)

    # -- saving ------------------------------------------------------------
    def save(self):
        plats = [s for s in self.draft if s['type'] in ('platform', 'moving')]
        if not plats:
            self.notify('need at least one platform before saving')
            return None
        local = [dict(s, h=s['h'] - self.floor_h) for s in self.draft]
        below = [s for s in local if s['h'] < 0]
        if below:
            self.notify(f'{len(below)} piece(s) below the draft floor - '
                        'press F where the segment should start')
            return None

        name = self.editing or EXPORT_NAME
        target = os.path.join(SEGMENT_DIR, f'{name}.py')
        top = max(s['h'] for s in local if s['type'] in ('platform', 'moving'))
        ordered = sorted((s for s in local if s['type'] in ('platform', 'moving')),
                         key=lambda s: s['h'])
        first, last = ordered[0], ordered[-1]

        if self.editing:
            doc = (self.editing_doc or f'Segment {name}.').strip()
            header = ['"""' + doc, '',
                      'Rewritten by creative mode (F4 -> E) as a flat spec list.',
                      '"""']
        else:
            header = ['"""Draft segment saved from creative mode (F4 -> E).', '',
                      'Rename this file to slot it into the difficulty order - as',
                      'seg_99 it sorts last and lands in the repeating tail.',
                      'Check it with `python lint_segments.py`.',
                      '"""']

        order = {'platform': 0, 'moving': 1, 'wall': 2, 'hazard': 3}
        lines = header + ['',
                          f'ENTRY = ({first["x"]}, {first["x"] + first.get("w", 16)})',
                          '', 'ENTITIES = [']
        for spec in sorted(local, key=lambda s: (order.get(s['type'], 9), s['h'])):
            fields = ', '.join(f"'{k}': {v!r}" for k, v in spec.items() if k != 'type')
            lines.append(f"    {{'type': '{spec['type']}', {fields}}},")
        lines += [']', '',
                  f'HEIGHT = {top}',
                  f'EXIT = ({last["x"]}, {last["x"] + last.get("w", 16)})', '']

        with open(target, 'w') as f:
            f.write('\n'.join(lines))
        self.notify(f'SAVED {len(local)} pieces -> {name}.py (reloading)')
        # main.py picks this up, reloads and warps us into it
        self.pending_reload = name
        return target

    # -- input -------------------------------------------------------------
    def handle_event(self, event, player, camera, tower):
        """Consume a creative-mode event. Returns True if handled, so main.py
        skips its normal binding for that key."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                index = self.draft_index_at(camera)
                if index is None:
                    self.place(camera)
                else:
                    self.start_drag(camera, index)
            elif event.button == 3:
                self.delete_at(camera, tower, player)
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.end_drag()
            return True
        if event.type == pygame.MOUSEMOTION:
            if self._drag is None:
                return False
            self.drag_to(camera)
            return True
        if event.type != pygame.KEYDOWN:
            return False

        key = event.key
        shift = pygame.key.get_pressed()[pygame.K_LSHIFT]
        if key == pygame.K_n:
            self.noclip = not self.noclip
            self.notify(f'noclip {"on" if self.noclip else "off"}')
        elif key == pygame.K_j:
            self.show_arcs = not self.show_arcs
        elif key == pygame.K_g:
            if shift:
                self.grid_index += 1
                self.notify(f'grid {self.grid}px')
            else:
                self.show_grid = not self.show_grid
        elif key == pygame.K_f:
            self.floor_h = max(0, self.ground_y - player.rect.bottom)
            self.notify(f'draft floor set to h={self.floor_h}')
        elif key == pygame.K_o:
            self.adopt(tower, player)
        elif key == pygame.K_e:
            self.save()
        elif key == pygame.K_DELETE:
            self.toggle_blank(tower)
        elif key == pygame.K_x:
            self.release(tower)
        elif key == pygame.K_BACKSPACE:
            self.undo()
        elif key == pygame.K_LEFTBRACKET:
            self.width = max(16, self.width - 10)
        elif key == pygame.K_RIGHTBRACKET:
            self.width = min(600, self.width + 10)
        elif key == pygame.K_SEMICOLON:
            self.nudge_travel(-10)
        elif key == pygame.K_QUOTE:
            self.nudge_travel(10)
        elif key == pygame.K_MINUS:
            self.nudge_period(-10)
        elif key == pygame.K_EQUALS:
            self.nudge_period(10)
        elif key == pygame.K_SLASH:
            self.cycle_phase()
        elif key == pygame.K_COMMA:
            self.select_type(self.type_index - 1)
        elif key == pygame.K_PERIOD:
            self.select_type(self.type_index + 1)
        elif pygame.K_1 <= key <= pygame.K_9:
            index = key - pygame.K_1
            if index < len(self.types):
                self.select_type(index)
        else:
            return False
        return True

    # -- drawing -----------------------------------------------------------
    def draw_world(self, screen, camera):
        if self.show_grid:
            self._draw_grid(screen, camera)
        floor_y = self.ground_y - self.floor_h + camera.offset.y
        if -20 < floor_y < screen.get_height() + 20:
            pygame.draw.line(screen, C_FLOOR, (0, floor_y),
                             (screen.get_width(), floor_y), 2)
        for entity in self.preview_entities:
            pygame.draw.rect(screen, C_DRAFT, camera.apply(entity.rect).inflate(4, 4), 1)

    def _draw_grid(self, screen, camera):
        w, h = screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        step = self.grid
        while step < 24:
            step *= 2
        for sx in range(-(int(-camera.offset.x) % step), w, step):
            pygame.draw.line(overlay, (*C_GRID, 22), (sx, 0), (sx, h))
        for sy in range(-(int(-camera.offset.y) % step), h, step):
            pygame.draw.line(overlay, (*C_GRID, 22), (0, sy), (w, sy))
        screen.blit(overlay, (0, 0))

    def draw_overlay(self, screen, camera, player, tower, font):
        if self.show_arcs:
            self._draw_arcs(screen, camera, player)
            self._draw_reachability(screen, camera, player, tower)
        self._draw_cursor(screen, camera)
        self._draw_panel(screen, font, player)

    def _draw_arcs(self, screen, camera, player):
        ox, oy = player.rect.centerx, player.rect.bottom
        for label, _direction, points in reach.standard_arcs():
            colour = C_ARC_DASH if label == 'dash' else C_ARC_SPRINT
            pts = [(ox + dx + camera.offset.x, oy + dy + camera.offset.y)
                   for dx, dy in points]
            pts = [p for p in pts if -2000 < p[1] < 3000]
            if len(pts) > 1:
                pygame.draw.lines(screen, colour, False, pts, 1)

    def _draw_reachability(self, screen, camera, player, tower):
        ox, oy = player.rect.centerx, player.rect.bottom
        candidates = list(tower.groups.get('landable', [])) + [
            e for e in self.preview_entities if 'landable' in type(e).TAGS]
        for entity in candidates:
            rect = entity.rect
            if abs(rect.centerx - ox) > 620 or not (-420 < rect.top - oy < 260):
                continue
            if rect.top >= oy and abs(rect.top - oy) < 4:
                continue
            hits = reach.reachable_from(ox, oy, rect)
            r = camera.apply(rect)
            pygame.draw.rect(screen, C_OK if hits else C_NO, r.inflate(6, 6), 2)
            if hits == {'dash'}:
                pygame.draw.circle(screen, C_ARC_DASH, (r.centerx, r.top - 9), 3)

    def _draw_cursor(self, screen, camera):
        wx, wy = self.world_mouse(camera)
        name = self.current[0]
        w = 16 if name in NO_WIDTH else self.width
        h = 60 if name in NO_WIDTH else 20
        x = _snap(wx - w / 2, self.grid)
        y = self.ground_y - _snap(self.ground_y - wy, self.grid)
        ghost = pygame.Rect(x + camera.offset.x, y + camera.offset.y, w, h)
        if name in NO_WIDTH:
            ghost.bottom = y + camera.offset.y
        pygame.draw.rect(screen, C_DRAFT, ghost, 1)
        pygame.draw.line(screen, C_DRAFT, (ghost.centerx - 6, ghost.centery),
                         (ghost.centerx + 6, ghost.centery))
        pygame.draw.line(screen, C_DRAFT, (ghost.centerx, ghost.centery - 6),
                         (ghost.centerx, ghost.centery + 6))

    def _draw_panel(self, screen, font, player):
        h_now = max(0, self.ground_y - player.rect.bottom)
        target = self.editing or f'{EXPORT_NAME} (new)'
        palette = '  '.join(
            f'{i + 1}:{label}' for i, (_n, label, _w, _e) in enumerate(self.types))
        detail = ''
        if 'travel' in self.extras:
            axis = 'up/down' if self.extras.get('axis') == 'y' else 'left/right'
            phase = self.extras.get('phase')
            phase_txt = f' phase={phase}' if phase is not None else ' phase=auto'
            detail = (f'  travel={self.extras["travel"]} {axis}'
                      f' period={self.extras.get("period", "-")}{phase_txt}')
        rows = [
            f'CREATIVE   saving to: {target}',
            f'[{self.current[1]}]  w={self.width}  grid={self.grid}px{detail}'
            f'{"   BLANK CANVAS" if self.blank else ""}',
            f'h={h_now}   floor h={self.floor_h}   pieces={len(self.draft)}',
            'showing each segment once - repeats resume on F4 off',
            palette,
            'N fly  J arcs  G grid  F floor  O edit segment  Del blank',
            "; ' travel   - = period   / phase",
            'click place/drag  rclick erase  bksp undo  X close  E save',
        ]
        if self.message and pygame.time.get_ticks() < self.message_until:
            rows.append(self.message)
        pad = 6
        surfaces = [font.render(r, True, (255, 255, 255)) for r in rows]
        box_w = max(s.get_width() for s in surfaces) + pad * 2
        box_h = sum(s.get_height() for s in surfaces) + pad * 2
        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill((10, 10, 16, 205))
        pygame.draw.rect(panel, C_FLOOR, panel.get_rect(), 1)
        y = pad
        for s in surfaces:
            panel.blit(s, (pad, y))
            y += s.get_height()
        screen.blit(panel, (screen.get_width() - box_w - 8, 34))
