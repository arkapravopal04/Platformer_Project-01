# Background art

One animated background per altitude band. Drop the files in and they are
picked up automatically — no code change needed.

## Where the files go

```
backgrounds/
  01_ground/   frame_1.png  frame_2.png  frame_3.png
  02_cliffs/   frame_1.png  frame_2.png  frame_3.png
  03_clouds/   frame_1.png  frame_2.png  frame_3.png
  04_storm/    frame_1.png  frame_2.png  frame_3.png
  05_void/     frame_1.png  frame_2.png  frame_3.png
```

Names must be exactly `frame_1.png`, `frame_2.png`, `frame_3.png`.
Any folder still missing its files renders a labelled placeholder, so the
game runs and the bands are visible before the art is done.

## What the art should be

| | |
| --- | --- |
| Format | PNG |
| Size | **640×360** (or any multiple — 1280×720, 1920×1080) |
| Aspect | Scaled to screen height, tiled horizontally, so wider art = less repetition |
| Seamless | Tile horizontally **and** vertically if you can — the backdrop wraps in both directions |
| Frames | 3, played on a loop at 200 ms each (600 ms per cycle) |

The three frames are a **loop**, not a sequence with a start and end — frame 3
runs straight back into frame 1. Subtle motion works best: drifting cloud,
a flicker, a slow shimmer. The player is reading platforms in front of this,
so keep contrast low and detail sparse.

## Which band appears when

Altitudes are in world pixels above the starting ground (1 m ≈ 24 px).

| Band | From | To | Roughly |
| --- | --- | --- | --- |
| `01_ground` | 0 | 2 500 | 0–104 m |
| `02_cliffs` | 2 500 | 7 000 | 104–291 m |
| `03_clouds` | 7 000 | 14 000 | 291–583 m |
| `04_storm` | 14 000 | 24 000 | 583–1000 m |
| `05_void` | 24 000 | ∞ | 1000 m up |

Each band cross-fades into the next over the last 700 px, so neighbouring
backgrounds should share a rough value range or the transition will pop.

## Changing the bands

Edit `BACKGROUND_BANDS` in `background.py`:

```python
BACKGROUND_BANDS = [
    (0,      'ground',  '01_ground'),
    (2500,   'cliffs',  '02_cliffs'),
    ...
]
```

`(start_altitude, display name, folder)`. Add, remove or reorder freely —
the only rule is that the first entry starts at `0`. Other knobs in the same
file: `FRAME_COUNT`, `FRAME_MS` (speed), `FADE_HEIGHT` (cross-fade distance),
`PARALLAX` (0 = pinned to the screen, 1 = moves with the world).

Press `F5` in game to reload art after adding or changing a file.
