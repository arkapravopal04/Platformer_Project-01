"""Segment package - each seg_NN_*.py module here is one authored chunk of
the endless tower (see tower.py).

Discovery is normally automatic: discover_names() lists this directory.
SEGMENT_NAMES below is an explicit fallback for runtimes that can't list
directories reliably - e.g. pygbag's in-browser filesystem, where the game
would otherwise launch with no segments at all (tower.py's _EmptySegment)
and no error to explain why. Keep it in sync with the files in this
package when you add, remove, or rename a segment.
"""

import pkgutil

SEGMENT_NAMES = [
    'seg_00_first_steps',
    'seg_01_stepping_up',
    'seg_02_gearing_up',
    'seg_03_lift_lines',
    'seg_04_dash_line',
    'seg_05_collapse_gauntlet',
]


def discover_names():
    """Every segment module's name under this package, sorted by filename.

    Prefers a real directory listing so a segment file dropped in during
    authoring/hot-reload is picked up with no edits needed here. Falls
    back to SEGMENT_NAMES only when that listing comes back empty.
    """
    found = sorted(name for _, name, _ in pkgutil.iter_modules(__path__))
    return found if found else list(SEGMENT_NAMES)
