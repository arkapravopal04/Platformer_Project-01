# rustbound

A 2D platformer built with pygame — my first big project, recovered and cleaned up.
Climb an obstacle course of jump-through platforms, moving platforms, blocking walls
and spike hazards, using walking, sprinting, variable-height jumps and a dash.
Reach the flag at the summit to finish the run.

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

## Layout

| File | Contents |
| --- | --- |
| `main.py` | Game loop, input events, pause / death / restart, HUD, draw order |
| `player_classes.py` | `Player` — physics, collision, animation, health, i-frames, dash |
| `platforms.py` | `Platform`, `MovingPlatform`, `Wall`, `Hazard` and `create_obstacle_course()` |
| `camera.py` | Trailing follow-camera, clamped to the map edges |
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

**The course** is generated in `create_obstacle_course()` from relative hop specs
(gap, width, rise) rather than absolute coordinates, then uniformly scaled down if the
background image is too narrow to hold it at full size. A `Goal` flag is planted on the
summit platform; touching it ends the run.

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

## Testing

`main()` accepts optional `max_frames` and `on_frame` hooks so the loop can be driven
headlessly. Normal play leaves both `None`:

```bash
SDL_VIDEODRIVER=dummy python -c "import main; main.main(max_frames=120)"
```

## Not done yet

- `Enemy` is a stub — no AI, movement or attacks, and it isn't instantiated by `main.py`.
- Nothing deals damage except spike hazards (and the `H` debug key).
- `MovingPlatform(axis='y')` is implemented and carries the player correctly, but the
  current course only uses a horizontal one.
- No timer, score, or checkpoints — reaching the summit just shows a banner.
