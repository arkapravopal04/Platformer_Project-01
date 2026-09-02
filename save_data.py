import json
import os
import sys

_SAVE_PATH = os.path.join(os.path.dirname(__file__), 'save_data.json')

# The web build has no real filesystem to persist to - the wasm FS pygbag
# mounts is wiped on every page reload. localStorage is the browser
# equivalent: per-origin storage that lives in the visitor's own browser
# and survives reloads. Desktop keeps using the plain JSON file below.
WEB = sys.platform == 'emscripten'
_STORAGE_KEY = 'rustbound_best_score'

# Falls back to this if localStorage genuinely can't be reached (e.g. a
# pygbag runtime whose JS-interop shape doesn't match _local_storage()
# below) - keeps a run playable even though the score won't survive a
# reload, in keeping with this module's existing rule of never raising
# over a save/load failure.
_memory_best = 0


def _local_storage():
    """The browser's window.localStorage, or None if unreachable."""
    try:
        import platform
        return platform.window.localStorage
    except Exception:
        return None


def load_best():
    """All-time best altitude score, or 0 if there's no save yet / it's
    unreadable. Never raises - a corrupt or missing save file just means
    starting from 0, not a crash."""
    if WEB:
        storage = _local_storage()
        if storage is None:
            return _memory_best
        try:
            raw = storage.getItem(_STORAGE_KEY)
            return int(raw) if raw is not None else 0
        except (ValueError, TypeError):
            return 0
    try:
        with open(_SAVE_PATH) as f:
            return int(json.load(f).get('best_score', 0))
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError, TypeError):
        return 0


def save_best(score):
    """Write the best score to disk (or localStorage on the web build).
    Deliberately NOT called every time the score ticks up - climbing gains
    a metre every 24px, which worked out to hundreds of writes per minute
    of play. main.py keeps the running best in memory and flushes it here
    only on death and on exit."""
    if WEB:
        global _memory_best
        _memory_best = score
        storage = _local_storage()
        if storage is None:
            return
        try:
            storage.setItem(_STORAGE_KEY, str(score))
        except Exception:
            pass
        return
    try:
        with open(_SAVE_PATH, 'w') as f:
            json.dump({'best_score': score}, f)
    except OSError:
        pass
