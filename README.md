# rustbound

**[Play it in your browser](https://arkapravopal04.github.io/Platformer_Project-01/)** — no install needed.

A 2D platformer built with pygame — my first big project, recovered and cleaned up.
Climb an endless tower of jump-through platforms, moving platforms, blocking walls and
spike hazards, using walking, sprinting, variable-height jumps and a dash. There's no
finish line — your score is the highest altitude you've reached, and it only ever goes
up. Falling costs you time, not your score.

## Running it

```bash
pip install -r requirements.txt
python main.py
```

Run from the repository root — asset paths are relative to the working directory.

## Controls

| Key | Action |
| --- | --- |
| `A` / `D` | Move left / right |
| `Shift` | Sprint (2x speed) |
| `Space` | Jump — release early for a shorter hop |
| `C` | Dash (horizontal burst, gravity suspended, 800 ms cooldown) |
| `P` | Pause |
| `R` | Restart, once dead |
| `H` | Take 10 damage (debug) |
| `F1` | Toggle hitbox / camera debug boxes |
| `F2` | Toggle the segment-authoring overlay (seams, current segment, mouse world coords) |
| `F3` | Warp to the next altitude preset (see `ALTITUDE_WARPS` in `main.py`) |
| `F4` | Toggle **creative mode** — fly, jump-arc overlay, mouse level editor (see below) |
| `F5` | Hot-reload `segments/*.py` and regenerate the tower from the ground up |
| `F6` | Toggle the frame-time perf overlay (rolling p50/p99/max ms) |

`F1`-`F6` and creative mode are desktop-only — the browser build disables them, since
several of those keys are reserved by the browser itself (`F5` refreshes the page, etc).

## Layout

| File | Contents |
| --- | --- |
| `main.py` | Game loop, input events, pause / death / restart, score, HUD, draw order |
| `player_classes.py` | `Player` — physics, collision, animation, health, i-frames, dash |
| `render.py` | Shared pixel-art rendering helpers (`_render_ledge`, palettes) |
| `entities/` | `Platform`, `MovingPlatform`, `Wall`, `Hazard`, `Goal` — one file each, tagged (see below) |
| `platforms.py` | `_build_leg` (relative hop-chain authoring helper) and `build_entities` (spec → sprite loader) |
| `segments/` | Hand-authored vertical chunks of the tower — see `seg_00_intro.py`'s docstring for the format |
| `tower.py` | `Tower` — stitches segments end-to-end, streams them in/out, repeats the hardest few once exhausted |
| `reach.py` | The movement model — jump arcs, max rise, max gap. Shared by the checker and creative mode |
| `clear_level.py` | Wipe or restore the whole level (moves segments to a timestamped backup) |
| `lint_segments.py` | Reachability checker — proves every platform and seam is jumpable before you play it |
| `devmode.py` | Creative mode — free flight, live reachability overlay, mouse placement, segment export |
| `background.py` | Sky gradient plus the animated per-altitude backdrop |
| `backgrounds/` | Background art, one folder per altitude band — see its README |
| `tiles.py` | Per-band block sprites: loading, 3-slicing, caching |
| `tiles_art/` | Block art, one folder per band — see its README |
| `save_data.py` | Persists the all-time best altitude to `save_data.json` |
| `camera.py` | Trailing follow-camera; clamped at the bottom (ground), unclamped going up |
| `enemy.py` | `Enemy` stub — not wired into the game yet |

Sprites live in `player_animations/`; the background and other loose art are in
`random_images_not_sorted/`.

## How a few things work

**Platform collision** is a swept check against each platform's *top* surface, using
last frame's `bottom` as well as this frame's, so a fast fall can't tunnel through a
thin platform in a single step. Landing is only considered while falling, so jumping
up through a platform from below passes cleanly instead of snagging on its underside.

**Walls** block horizontal movement only — you can always jump over one. They exist to
close gaps that a sprint- or dash-jump could otherwise overshoot, forcing a landing on
the platform that was meant to be a required step.

**The tower streams both ways.** `tower.py` keeps a permanent *plan* of which segment
sits at which height, and materialises sprites only for the band around the player. The
plan is never discarded, so a segment you climbed past is rebuilt identically when you
come back down — falling lands you on the platforms you fell past, not in a void.

**The tower is built from segments.** Each file under `segments/` is a self-contained
vertical chunk with its own `HEIGHT` and a flat `ENTITIES` list (see
`segments/seg_00_intro.py`'s module docstring for the exact format). `tower.py` discovers
every segment module in filename order and stacks them bottom-to-top. They play through
once in order, then only the last `CYCLE_TAIL` (currently 4) repeat forever — so the climb
is infinite immediately, it stays hard once it wraps instead of dropping back to the
tutorial, and adding a new, harder file further down the alphabet is the entire job of
extending it. Segments stream in ahead of the player and get torn down well behind, so
the live entity count stays bounded (~50 platforms) no matter how long a run goes.

`HEIGHT` is where the *next* segment's floor sits, and should equal your topmost
platform's `h` — the next segment then starts exactly on your last surface. Leave dead air
there instead and the seam becomes unjumpable, since the player can only climb ~95px in a
single jump. `lint_segments.py` checks this, along with every gap in the segment, against
the player's real physics constants.

**Entities are tagged, not type-checked.** `entities.Entity.TAGS` classifies what a thing
*does* — `{"landable"}`, `{"blocking"}`, `{"damaging"}` — and `Tower.groups` / `player.set_platforms(...)`
key off those tags rather than concrete classes, so a new entity that combines behaviors
(e.g. a moving hazard) needs no changes anywhere else. `entities.ENTITY_TYPES` maps a
level spec's `"type"` string to its class; each class's `from_spec()` classmethod knows
how to build itself from a flat `{'type', 'x', 'h', ...}` dict.

**Scoring is a ratchet.** Altitude (`ground_y - player.rect.bottom`) is measured every
frame; the session best only ever increases, and the all-time best persists to
`save_data.json`. Falling doesn't cost you anything except the climb back up.

**Obstacles are colour-coded** so their behaviour is readable before you touch them:
earth-brown slabs are static, steel-blue ones move (with chevrons showing which axis),
grey masonry pillars block you horizontally, and rust-red spikes hurt.

**Jump feel** uses the two standard platformer forgiveness mechanics. *Coyote time*
gives 6 frames of grace after walking off a ledge during which a jump still counts, and
*jump buffering* remembers a jump pressed up to 6 frames before landing and fires it on
touchdown. Both are invisible when you are on rhythm and stop the controls feeling
like they dropped inputs when you are slightly off it.

**The jump animation is driven by vertical momentum**, not a timer — see
`Player._airborne_frame`. The 7-frame arc runs anticipation → launch → rise → apex →
fall, and momentum picks the pose, so it stays correct for any jump height and reads
right when falling off a ledge without jumping at all.

**The player's collision rect is a fixed 32x56**, deliberately decoupled from the
sprite. Animation frames vary from 32x50 to 40x56, so rebuilding the rect per frame
made the hitbox pulse as the animation played. `Player.draw()` aligns the sprite to the
hitbox by midbottom instead.

**`Player.update()` order is deliberate**: gravity runs before the dash timer is
decremented, so no stray frame of gravity slips in on a dash's final frame; animation
runs last so the sprite re-anchors to the frame's final position.

## The segments

| File | Difficulty | Idea |
| --- | --- | --- |
| `seg_00_intro` | easy | The original hand-built course — long zig-zag climb, ending on a tight dash-jump to the summit |
| `seg_01_zigzag` | easy | A breather. Wide ledges, 60px rises, no dash needed anywhere |
| `seg_02_narrow_ledges` | medium | Ledges shrink to ~100px; introduces the vertical lift you have to ride to finish |
| `seg_03_spike_alley` | medium-hard | Every ledge is half spikes, so the landing strip is the far 60% of each slab |
| `seg_04_long_haul` | hard | Pure reach. A forced 200px dash-jump and a wide horizontal mover; no spikes at all |
| `seg_05_gauntlet` | hard | Everything at once — two forced dash-jumps onto small spiked ledges, then a lift |

`seg_02`–`seg_05` are the four that repeat once the tower wraps.

## Backgrounds

The backdrop is a sky gradient with an animated background layered over it, and the
background changes as you climb. Five bands ship wired up:

| Band | From | Folder |
| --- | --- | --- |
| ground | 0 | `backgrounds/01_ground/` |
| cliffs | 2 500 | `backgrounds/02_cliffs/` |
| clouds | 7 000 | `backgrounds/03_clouds/` |
| storm | 14 000 | `backgrounds/04_storm/` |
| void | 24 000 | `backgrounds/05_void/` |

Each wants three frames — `frame_1.png`, `frame_2.png`, `frame_3.png` — played as a
600 ms loop, and each band cross-fades into the next over the last 700 px. **Any folder
without art renders a labelled placeholder**, so the bands and the animation are visible
and testable right now; drop real files in and they are picked up with no code change.
Frames are independent, so a folder with only `frame_1.png` uses it plus two placeholders.

`backgrounds/README.md` has the art spec (sizes, tiling, what reads well behind
gameplay). The altitude table and the animation speed, fade distance and parallax
strength are the constants at the top of `background.py`. <kbd>F5</kbd> reloads art along
with the segments, and <kbd>F2</kbd> shows the current band and frame.

## Block sprites

The same idea as the backgrounds, for the things you stand on. One folder per band,
matching the background folders, so a theme is one name in both places:

```
backgrounds/02_cliffs/frame_1.png   <- what's behind you
tiles_art/02_cliffs/platform.png    <- what you stand on
```

`platform.png`, `mover.png`, `lift.png`, `wall.png`, `hazard.png`, `goal.png`.
**Anything you don't supply keeps the current hand-drawn look**, so you can theme one
band, or one block type, and leave everything else alone — adding art changes nothing
you haven't replaced.

Sprites are never simply stretched. Platforms and movers are 3-sliced horizontally (the
end caps stay fixed, the middle tiles), walls 3-sliced vertically, and spikes tiled at
constant scale. A **48×20** platform sprite renders correctly at any width from 40px to
600px. Full spec in `tiles_art/README.md`.

A block's band is fixed by the altitude it sits at, so unlike the backgrounds there's no
cross-fade — blocks swap cleanly at the boundary. <kbd>F5</kbd> reloads sprites along with
the segments and backgrounds.

## Starting from an empty level

```bash
python clear_level.py
```

Moves every segment out of `segments/` into a timestamped folder under
`segments_backup/`, leaving the tower as blank space — just the ground floor and sky.
Nothing is deleted, because segment files aren't tracked by git and an outright delete
would be unrecoverable. `--restore` puts the most recent backup back, `--list` shows
what exists.

With `segments/` empty the game still runs: `tower._EmptySegment` supplies the empty
space the stacker needs. Press <kbd>F4</kbd> and build.

## Creative mode

Press <kbd>F4</kbd>. It exists to answer the two questions that otherwise cost the most
time when building segments.

**"Can I actually make that jump?"** — the overlay draws every arc the player can fly
from where they're standing (yellow = sprint-jump, blue = maximum-reach dash-jump) and
outlines every nearby platform in **green if it's reachable in one hop** or **red if it
isn't**. A blue dot above a platform means it's only reachable by spending the dash. No
guessing and no repeated attempts — you can see the answer.

**"Where exactly should this go?"** — click to place platforms, movers, walls and spikes.
They snap to a grid and become solid the instant they exist, so you can jump on a piece
straight after placing it. <kbd>E</kbd> writes the whole draft out as a real segment file.

| Key | Action |
| --- | --- |
| `N` | Toggle free flight (on by default). `W`/`A`/`S`/`D` to fly, `Shift` for fast |
| `J` | Toggle jump arcs and the reachability tint |
| `G` | Toggle the grid — `Shift+G` cycles 5 / 10 / 20 / 25px |
| `O` | **Open the segment you're standing in for editing** — press again to close |
| `F` | Set the draft floor (`h = 0`) to your feet |
| `1`…`9` · `,` `.` | Pick a block — `platform`, `mover-LR`, `lift-UD`, `wall`, `spikes`, **`trapdoor`**, `goal` |
| `;` `'` | Travel distance of the selected mover or lift, ±10px |
| `-` `=` | Cycle time (period), ±10 frames |
| `/` | Step the phase through the cycle in eighths |
| `Delete` | **Blank canvas** — hide the whole level to build from nothing (again to restore) |
| `[` `]` | Narrow or widen the next piece by 10px |
| Left click | **Drag** an existing piece, or place a new one on empty space |
| Right click | Erase the piece under the cursor — **works on the real level too**, opening that segment automatically |
| `Backspace` | Undo last placement · `X` close/clear |
| `E` | **Save** — writes the file, reloads, and drops you into what you just saved |

The palette is a list of *variants*, not bare types: the horizontal mover and the
vertical lift are the same `moving` entity separated only by `axis`, so each gets its own
slot. Any entity type registered in `entities/` that isn't listed as a variant is appended
automatically, so a new obstacle is placeable the moment you register it.

**Trapdoors** (`entities/trapdoor.py`) are a fixed one-tile block, not a stretchable
slab — landable and solid like a `Platform` while closed, but stand on one
continuously for `stand_delay` frames (45 by default, visibly shaking for the last
stretch as a warning) and it swings open, dropping you through exactly like a gap. It
resets shut on its own after `open_duration` frames (90 by default) whether or not
anyone is still there. Stepping off before it triggers resets the timer to zero — only
sustained standing counts.

The mechanism is worth understanding since it's the template for any future timed
obstacle: main.py is the only thing that knows about `Player`, so it's the one place
that checks `player.standing_platform is entity` each frame for everything tagged
`"collapsible"`, calling `on_stand()`/`on_leave()` — the same pattern already used for
hazard damage on the `"damaging"` tag. That check runs whenever real physics is active,
which includes creative mode with noclip **off** — turning off flight to playtest a jump
you just placed is exactly when a trapdoor needs to actually spring, so the check is
gated on `dev.noclip`, not on `dev.active`. `TrapDoor` itself never touches `Player`; when it
opens it simply removes itself from every sprite group it was in (so `apply_gravity`'s
landing check no longer sees it, no special-casing required), then rejoins them when it
resets. `lint_segments.py` treats it as landable for reachability purposes, since it's a
legitimate step in a jump chain right up until it opens.

**Movers are timed with `phase`.** A mover's `phase` is where in its cycle it starts,
`0`–`1` of a full period. Left unset, it's derived from the mover's position within its
segment, so movers never silently share a clock — without that every mover with the same
`period` starts at t=0 and a row of them swings in perfect lockstep, reading as one
machine rather than several. Set it explicitly to time them against each other: two
movers at `0.0` and `0.5` are exactly opposed, four at `0.0`/`0.25`/`0.5`/`0.75` chase
each other round. The derived default keys off *segment-local* position, so every copy of
a repeated segment keeps identical timing and a jump designed against one works on all of
them.

**Repeats are hidden while creative mode is on.** The tower is endless because it repeats
the authored segments, so a level with only one or two of them stacks the same geometry
all the way up — while building, that reads as your own block having been duplicated
infinitely upward. Creative mode shows each segment only where it first appears; normal
repetition resumes the moment you leave it.

Hazards do no damage while creative mode is on, so you can fly through spikes to inspect
geometry. Normal play is untouched — none of this runs unless `F4` is pressed.

### The draft floor matters

A segment file's `h` values are measured from *its own floor*, not from the ground. Stand
where the segment should begin and press <kbd>F</kbd> before placing anything; export
subtracts that height from everything, so the numbers it writes are correct segment-local
coordinates. Get this wrong and the export refuses rather than writing a broken file.

### Saving

<kbd>E</kbd> writes the file, reloads every segment and warps you into the one you just
saved. That last step matters: a brand-new segment is placed *after* every existing one,
so it lands several hundred metres up the tower. Before the warp existed, saving looked
like it had done nothing at all. Every creative-mode message is also printed to the
console, so a refusal ("need at least one platform", "pieces below the draft floor")
can't scroll past unnoticed.

### Editing what's already there

<kbd>O</kbd> opens the segment you're standing in. Its real pieces load into the editor and
the original is hidden, so what you see and drag around *is* that segment. <kbd>E</kbd>
then writes back over that segment's own file, keeping its docstring; <kbd>X</kbd> closes
without saving and restores the original.

Saving a segment this way rewrites it as a flat spec list. If the file used
`_build_leg` to compute its coordinates, that code is replaced by the resulting numbers —
the geometry is identical, but the authoring helper is gone. That is usually what you
want once you start nudging pieces by hand.

### The full authoring loop

1. <kbd>F3</kbd> to the altitude you're designing for
2. <kbd>F4</kbd>, then <kbd>F</kbd> to set the floor
3. Place geometry, or <kbd>O</kbd> to edit what's there — the green/red tint tells you
   immediately whether it connects
4. <kbd>E</kbd> to export, then `python lint_segments.py` to confirm
5. Rename `seg_99_draft.py` into the difficulty order you want
6. <kbd>F5</kbd> to reload and play it for real

## Adding a new segment

Copy the shape of `segments/seg_01_zigzag.py` (simplest) or `seg_03_spike_alley.py`
(explicit coordinates): either use `platforms._build_leg` to lay out a row of platforms
from relative `(gap, width, rise)` hops, or write the `(x, w, h)` tuples out directly. Pin
hazards and walls to a platform's own `h` so they sit flush with its surface, then export
`HEIGHT`/`ENTITIES` plus `ENTRY`/`EXIT`. Name the file to sort after the segments that
should come before it (`seg_06_...`) — `tower.py` picks them up in filename order
automatically.

Then check it before you play it:

```bash
python lint_segments.py
```

That prints the player's actual reach budget — max rise, and max gap at each rise for
walk / sprint / sprint+dash, all derived from the constants in `player_classes.py` — then
verifies every platform is reachable from something below it, that nothing leaves the map
bounds, and that each segment's `EXIT` band overlaps the next one's `ENTRY`, including the
wrap-around seam. Design against those numbers rather than guessing.

If you alternate which side of the map your segments exit on, keep `CYCLE_TAIL` **even**
so the wrap lands on a segment whose `ENTRY` is on the matching side.

In-game, use `F3` to warp near where the new segment starts and `F5` to reload it after
each edit, rather than climbing the whole tower on every test.

## Testing

`main()` accepts optional `max_frames` and `on_frame` hooks so the loop can be driven
headlessly. Normal play leaves both `None`:

```bash
SDL_VIDEODRIVER=dummy python -c "import main; main.main(max_frames=120)"
```

## Not done yet

- `Enemy` is a stub — no AI, movement or attacks, and it isn't instantiated by `main.py`.
- Nothing deals damage except spike hazards (and the `H` debug key).
- Six segments exist so far; the tower repeats the top four once it wraps. More files
  further down the alphabet is how it gets deeper.
- The reachability overlay tests single hops from a standing start. It won't tell you a
  route is possible via a mid-air direction change, and it assumes the dash is off
  cooldown.
- `lint_segments.py` models the player as a point mass on a clean jump arc. It cannot see
  dash cooldown (800ms, so back-to-back forced dash-jumps may be tighter than it reports),
  moving-platform timing, or spike placement, so a segment it passes can still play badly.
  It catches the impossible, not the unpleasant.
- `Goal` still exists as an entity type but nothing uses it — there is no finish line in
  an endless climb. It is kept as a starting point for checkpoints.
