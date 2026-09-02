# Block sprites

One set of block art per altitude band — the same bands as the backgrounds,
so a "level" is one folder name in both places:

```
backgrounds/02_cliffs/frame_1.png   <- what's behind you
tiles_art/02_cliffs/platform.png    <- what you stand on
```

Drop a sprite in and it is used automatically. **Anything you don't supply keeps
the current hand-drawn look**, so you can theme one band, or one block type,
and leave the rest alone.

## Where the files go

```
tiles_art/
  01_ground/   platform.png  mover.png  lift.png  wall.png  hazard.png  goal.png
  02_cliffs/   ...
  03_clouds/   ...
  04_storm/    ...
  05_void/     ...
```

| File | Block | Missing → |
| --- | --- | --- |
| `platform.png` | Static ledge | hand-drawn earth slab |
| `mover.png` | Horizontal mover | `platform.png`, else steel slab + chevrons |
| `lift.png` | Vertical lift | `mover.png`, then `platform.png`, else steel slab |
| `wall.png` | Blocking pillar | hand-drawn masonry |
| `hazard.png` | Spikes | hand-drawn spike bank |
| `goal.png` | Finish marker | hand-drawn flag |

## How each one is fitted

Blocks are arbitrary sizes, so sprites are **never simply stretched**.

| Block | Fitting |
| --- | --- |
| platform / mover / lift | **3-slice horizontal** — left 8px and right 8px stay fixed, the middle tiles |
| wall | **3-slice vertical** — top and bottom 8px fixed, middle tiles |
| hazard | **tiled horizontally** at constant scale, so one sprite = one tooth |
| goal | scaled to fit |

So a platform sprite only has to be as wide as its two end caps plus a little
tiling middle. **48×20** is plenty; it will render correctly at any width from
40px to 600px. The 8px cap size is `CAP` in `tiles.py` — raise it if your art
has chunkier ends.

Heights: platforms and movers are **20px** tall by default, spikes **16px**,
walls whatever the segment asks for. Author at 1× (the game is 640×360, so
one game pixel is one art pixel) unless you want the scaler to downsample.

Format: PNG with alpha. Transparency is respected everywhere.

## Which band appears when

| Band | From | To | ≈ metres |
| --- | --- | --- | --- |
| `01_ground` | 0 | 2 500 | 0–104 m |
| `02_cliffs` | 2 500 | 7 000 | 104–291 m |
| `03_clouds` | 7 000 | 14 000 | 291–583 m |
| `04_storm` | 14 000 | 24 000 | 583–1000 m |
| `05_void` | 24 000 | ∞ | 1000 m up |

That's `BACKGROUND_BANDS` in `background.py` — one table drives both the
backdrops and these sprites.

A block's band is fixed by the altitude it sits at, so a platform never changes
sprite once built. Unlike the backgrounds there is no cross-fade: blocks swap
cleanly at the boundary.

Press `F5` in game to reload sprites after adding or changing a file.
