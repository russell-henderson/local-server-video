"""
thumbnail_manager.py
───────────────────────────────────────────────────────────────────────────────
Centralised thumbnail + metadata maintenance for the Local-Video-Server.

Key features
────────────
• Single source of truth for mapping a *video* → *thumbnail* (.jpg).
• Case-preserving filenames so URLs rendered by Jinja match the file on disk.
• Supports multiple video extensions (.mp4 .mkv .webm .mov .avi …).
• Background thumbnail generation using ThreadPoolExecutor.
• One-shot `sync()` routine that:
     1. removes orphan thumbnails
     2. cleans JSON metadata files (favorites / ratings / tags / views)
     3. optionally deletes DB rows (if cache_manager is using SQLite)
     4. queues generation for missing thumbnails (or *all* via --force)
• CLI mode:  `python thumbnail_manager.py            `  → quick sweep  
             `python thumbnail_manager.py --force   `  → nuke & rebuild

External requirements
─────────────────────
• FFmpeg must be in your PATH.
• If you rely on cache_manager’s SQLite backend, import succeeds (else it
  silently skips the DB clean-up).

Usage from main.py
──────────────────
>>> from thumbnail_manager import (
>>>     thumb_path_for,
>>>     generate_async as generate_thumbnail_async,
>>>     sync as sync_thumbnails,
>>> )
>>> # queue thumbs when you render lists:
>>> generate_thumbnail_async("Some Video.mkv")
>>>
>>> # run once at startup
>>> with app.app_context():
>>>     sync_thumbnails(force_regen=False)

MIT License – © 2025 Your Name
"""

from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, List, Set

# ────────────────────────────────────────────────────────────────────────────
# Configuration (edit to taste)
# ────────────────────────────────────────────────────────────────────────────

VIDEO_DIR   = Path("videos")
THUMB_DIR   = Path("static") / "thumbnails"
VIDEO_EXTS  = {".mp4", ".mkv", ".webm", ".mov", ".avi"}
THUMB_EXT   = ".jpg"
THUMB_SIZE  = "320:180"            # WxH passed to ffmpeg scale
PLACEHOLDER = None                 # e.g. "static/placeholder.jpg" for 404s

# metadata JSON files at project root
META_FILES  = ["favorites.json", "ratings.json", "tags.json", "views.json"]

# internal thread pool – thumbnails render in the background
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="thumb-gen")


# ────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────────────────────

def _video_stem_exact(filename: str | Path) -> str:
    """Stem exactly as it appears on disk (case preserved)."""
    return Path(filename).stem


def _video_stem_ci(filename: str | Path) -> str:
    """Case-insensitive stem – used only for comparisons."""
    return Path(filename).stem.lower()


def thumb_path_for(video_filename: str | Path) -> Path:
    """
    Map any video filename to its thumbnail *Path*, preserving case.

    >>> thumb_path_for("My Video.mp4")
    PosixPath('static/thumbnails/My Video.jpg')
    """
    return THUMB_DIR / f"{_video_stem_exact(video_filename)}{THUMB_EXT}"


# ────────────────────────────────────────────────────────────────────────────
# Thumbnail generation
# ────────────────────────────────────────────────────────────────────────────

def generate_async(video_filename: str | Path) -> None:
    """
    Spawn a background thread to generate a thumbnail if missing.

    Safe to call many times – early exit if thumbnail already exists.
    """
    def _worker():
        vpath = VIDEO_DIR / video_filename
        tpath = thumb_path_for(video_filename)

        if tpath.exists() or not vpath.exists():
            return  # nothing to do

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(vpath),
            "-ss", "00:00:30.000",
            "-frames:v", "1",
            "-vf",
            (
                f"scale={THUMB_SIZE}:force_original_aspect_ratio=decrease,"
                f"pad={THUMB_SIZE}:(320-iw)/2:(180-ih)/2"
            ),
            str(tpath),
        ]

        try:
            subprocess.run(cmd, check=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           timeout=30)
            print(f"[THUMB] ✔ {tpath.name}")
        except subprocess.TimeoutExpired:
            print(f"[THUMB] ✖ timeout generating {video_filename}")
        except subprocess.CalledProcessError as e:
            print(f"[THUMB] ✖ ffmpeg error for {video_filename}: {e}")

    _pool.submit(_worker)


# ────────────────────────────────────────────────────────────────────────────
# Maintenance – sync()
# ────────────────────────────────────────────────────────────────────────────

def _valid_video_files() -> List[Path]:
    return [
        p for p in VIDEO_DIR.iterdir()
        if p.suffix.lower() in VIDEO_EXTS and p.is_file()
    ]


def _clean_metadata(valid_stems_ci: Set[str]) -> None:
    """Remove references to missing videos in all META_FILES."""
    for meta in META_FILES:
        path = Path(meta)
        if not path.exists():
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[META] skip {meta}: {e}")
            continue

        changed = False
        if isinstance(data, list):
            new = [v for v in data if _video_stem_ci(v) in valid_stems_ci]
            changed = new != data
            data = new
        elif isinstance(data, dict):
            new = {k: v for k, v in data.items()
                   if _video_stem_ci(k) in valid_stems_ci}
            changed = new != data
            data = new

        if changed:
            try:
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                print(f"[META] cleaned {meta}")
            except Exception as e:
                print(f"[META] cannot write {meta}: {e}")


def _clean_database(valid_stems_ci: Set[str]) -> None:
    """
    If cache_manager is present and using SQLite, delete rows that reference
    non-existent videos.
    """
    try:
        from cache_manager import cache  # local import to avoid hard dependency
        if not (cache.use_database and cache.db):
            return

        for vid in cache.db.get_all_filenames():
            if _video_stem_ci(vid) not in valid_stems_ci:
                cache.db.delete_video_by_filename(vid)
                print(f"[DB] removed row {vid}")

        cache.refresh_all()  # ensure in-memory cache is valid
        print("[DB] cache refreshed")
    except Exception as e:
        print(f"[DB] cache_manager unavailable or error: {e}")


def sync(force_regen: bool = False) -> None:
    """
    One-shot maintenance sweep.

    Parameters
    ----------
    force_regen : bool
        • False (default) → generate only *missing* thumbnails.  
        • True            → delete every thumbnail and rebuild.

    Always call this *once* at application start-up, then let
    `generate_async()` handle on-demand thumbnails for new uploads.
    """
    THUMB_DIR.mkdir(parents=True, exist_ok=True)

    video_files          = _valid_video_files()
    valid_stems_ci       = {_video_stem_ci(p.name) for p in video_files}
    thumb_files          = list(THUMB_DIR.glob(f"*{THUMB_EXT}"))
    thumb_stems_ci       = {_video_stem_ci(p.name) for p in thumb_files}

    # 1 ─ Remove orphan thumbnails (no matching video)
    for thumb in thumb_files:
        if _video_stem_ci(thumb.name) not in valid_stems_ci:
            thumb.unlink(missing_ok=True)
            print(f"[SYNC] 🗑️  {thumb.name}")

    # 2 ─ Optionally delete all remaining thumbnails (full rebuild)
    if force_regen:
        for thumb in THUMB_DIR.glob(f"*{THUMB_EXT}"):
            thumb.unlink(missing_ok=True)
        thumb_stems_ci.clear()
        print("[SYNC] 🔄 forced full rebuild – all thumbs removed")

    # 3 ─ Queue generation jobs
    to_generate = [
        v for v in video_files
        if _video_stem_ci(v.name) not in thumb_stems_ci or force_regen
    ]
    for vf in to_generate:
        generate_async(vf.name)

    # 4 ─ Clean metadata + database
    _clean_metadata(valid_stems_ci)
    _clean_database(valid_stems_ci)

    print(f"[SYNC] ✔ queued {len(to_generate)} thumbnail job(s)")


# ────────────────────────────────────────────────────────────────────────────
# CLI entry-point
# ────────────────────────────────────────────────────────────────────────────

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Thumbnail + metadata maintenance utility")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete *all* thumbnails then rebuild from scratch")
    args = parser.parse_args()

    sync(force_regen=args.force)

    # wait for background jobs to finish before exiting
    _pool.shutdown(wait=True)


if __name__ == "__main__":
    _cli()
