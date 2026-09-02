"""Wipe the level: move every segment out of segments/ so the tower is empty.

    python clear_level.py            # back up, then clear
    python clear_level.py --restore  # put the most recent backup back
    python clear_level.py --list     # show what's there and what's backed up

Segment files are not tracked by git, so deleting them outright would be
unrecoverable. This never deletes: it moves them into a timestamped folder
under segments_backup/ first, so a clear is always undoable.

With segments/ empty the game still runs - tower._EmptySegment contributes
blank space, leaving the ground floor and sky. Press F4 and start building.
"""

import argparse
import os
import shutil
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
SEGMENT_DIR = os.path.join(ROOT, 'segments')
BACKUP_ROOT = os.path.join(ROOT, 'segments_backup')


def segment_files(directory):
    """Segment modules in a directory - everything but __init__ and caches."""
    if not os.path.isdir(directory):
        return []
    return sorted(
        f for f in os.listdir(directory)
        if f.endswith('.py') and f != '__init__.py'
    )


def clear():
    files = segment_files(SEGMENT_DIR)
    if not files:
        print('segments/ is already empty - nothing to clear.')
        return 0

    stamp = time.strftime('%Y%m%d-%H%M%S')
    destination = os.path.join(BACKUP_ROOT, stamp)
    os.makedirs(destination, exist_ok=True)
    for name in files:
        shutil.move(os.path.join(SEGMENT_DIR, name),
                    os.path.join(destination, name))

    cache = os.path.join(SEGMENT_DIR, '__pycache__')
    if os.path.isdir(cache):
        shutil.rmtree(cache)      # stale .pyc would otherwise still import

    print(f'moved {len(files)} segment(s) to segments_backup/{stamp}/')
    for name in files:
        print(f'  {name}')
    print()
    print('The level is now empty. Run the game, press F4, and build.')
    print(f'To undo:  python clear_level.py --restore')
    return 0


def restore():
    if not os.path.isdir(BACKUP_ROOT):
        print('no backups found.')
        return 1
    stamps = sorted(d for d in os.listdir(BACKUP_ROOT)
                    if os.path.isdir(os.path.join(BACKUP_ROOT, d)))
    if not stamps:
        print('no backups found.')
        return 1

    newest = os.path.join(BACKUP_ROOT, stamps[-1])
    files = segment_files(newest)
    existing = set(segment_files(SEGMENT_DIR))
    clashes = [f for f in files if f in existing]
    if clashes:
        print('these would be overwritten in segments/ - move them aside first:')
        for name in clashes:
            print(f'  {name}')
        return 1

    for name in files:
        shutil.copy2(os.path.join(newest, name),
                     os.path.join(SEGMENT_DIR, name))
    print(f'restored {len(files)} segment(s) from segments_backup/{stamps[-1]}/')
    return 0


def show():
    current = segment_files(SEGMENT_DIR)
    print(f'segments/  ({len(current)})')
    for name in current:
        print(f'  {name}')
    if not current:
        print('  (empty - the tower is blank space)')
    print()
    if os.path.isdir(BACKUP_ROOT):
        for stamp in sorted(os.listdir(BACKUP_ROOT)):
            path = os.path.join(BACKUP_ROOT, stamp)
            if os.path.isdir(path):
                print(f'segments_backup/{stamp}/  ({len(segment_files(path))})')
    else:
        print('no backups yet.')
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--restore', action='store_true',
                       help='restore the most recent backup')
    group.add_argument('--list', action='store_true',
                       help='show current segments and backups')
    args = parser.parse_args()
    if args.restore:
        return restore()
    if args.list:
        return show()
    return clear()


if __name__ == '__main__':
    raise SystemExit(main())
