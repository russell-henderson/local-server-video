from __future__ import annotations

import os
import re
from pathlib import Path


# Matches: "anything (2).ext" where (2) is right before the extension
TRAILING_COPY_RE = re.compile(r"^(?P<stem>.*)\s\((?P<num>2)\)$")


def main() -> int:
    folder = Path(r"Z:\local-video-server\videos")

    if not folder.exists() or not folder.is_dir():
        print(f"[ERROR] Folder not found or not a directory: {folder}")
        return 1

    renamed = 0
    skipped = 0
    conflicts = 0

    for entry in folder.iterdir():
        if not entry.is_file():
            continue

        stem = entry.stem  # filename without extension
        m = TRAILING_COPY_RE.match(stem)
        if not m:
            continue

        new_name = f"{m.group('stem')}{entry.suffix}"
        target = entry.with_name(new_name)

        # Skip if target already exists (avoid overwriting)
        if target.exists():
            print(f"[CONFLICT] {entry.name} -> {target.name} (target already exists)")
            conflicts += 1
            continue

        try:
            entry.rename(target)
            print(f"[RENAMED] {entry.name} -> {target.name}")
            renamed += 1
        except OSError as e:
            print(f"[SKIP] Failed to rename {entry.name}: {e}")
            skipped += 1

    print("\n--- Summary ---")
    print(f"Renamed:   {renamed}")
    print(f"Conflicts: {conflicts}")
    print(f"Skipped:   {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
