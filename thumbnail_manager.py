"""
thumbnail_manager.py
Lightweight thumbnail + metadata maintenance for the Local Video Server.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from math import floor
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Iterable, List, Set

# Configuration
VIDEO_DIR = Path("videos")
THUMB_DIR = Path("static") / "thumbnails"
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".wmv"}
THUMB_EXT = ".jpg"
THUMB_SIZE = "320:180"  # WxH passed to ffmpeg scale
PLACEHOLDER = None  # e.g. "static/placeholder.jpg" for 404s
THUMB_LOG = Path("thumbnail_errors.log")

# metadata JSON files at project root
META_FILES = ["favorites.json", "ratings.json", "tags.json", "views.json"]

# internal thread pool – thumbnails render in the background
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="thumb-gen")


# Helpers
def _video_stem_exact(filename: str | Path) -> str:
    """Stem exactly as it appears on disk (case preserved)."""
    return Path(filename).stem


def _video_stem_ci(filename: str | Path) -> str:
    """Case-insensitive stem – used only for comparisons."""
    return Path(filename).stem.lower()


def thumb_path_for(video_filename: str | Path) -> Path:
    """Map any video filename to its thumbnail Path, preserving case."""
    return THUMB_DIR / f"{_video_stem_exact(video_filename)}{THUMB_EXT}"


# Thumbnail generation
def generate_async(video_filename: str | Path) -> None:
    """Spawn a background thread to generate a thumbnail if missing."""

    def _log(message: str) -> None:
        try:
            with THUMB_LOG.open("a", encoding="utf-8") as fh:
                fh.write(f"{message}\n")
        except Exception:
            pass

    def _probe_duration_seconds(video_path: Path) -> float | None:
        """Return video duration in seconds using ffprobe, or None on error."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=True,
                text=True,
            )
            duration = float(result.stdout.strip() or 0)
            return duration if duration > 0 else None
        except Exception:
            return None

    def _format_timestamp(seconds: float) -> str:
        """Format seconds to ffmpeg-friendly HH:MM:SS.mmm string."""
        seconds = max(0, seconds)
        h = floor(seconds / 3600)
        m = floor((seconds % 3600) / 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"

    def _compute_timestamps(video_path: Path) -> list[str]:
        """
        Primary: 5:00 or 3:00 if shorter. Fallbacks: ~60s, 30s, 10s, 1s.
        """
        duration = _probe_duration_seconds(video_path)
        target = 300.0  # 5 minutes
        fallback = 180.0  # 3 minutes
        candidates: list[str] = []

        if duration is None:
            _log(f"FFPROBE_MISSING {video_path.name} defaulting to 5m")
            candidates.append(_format_timestamp(target))
        else:
            if duration >= target:
                candidates.append(_format_timestamp(target))
            elif duration >= fallback:
                candidates.append(_format_timestamp(fallback))
            else:
                candidates.append(_format_timestamp(max(1.0, duration - 1.0)))

            alt_point = min(duration - 1.0, 60.0) if duration and duration > 60 else max(5.0, (duration or 0) / 2 or 5)
            candidates.append(_format_timestamp(max(1.0, alt_point)))

        # Additional early fallbacks
        candidates.extend([
            _format_timestamp(30.0),
            _format_timestamp(10.0),
            _format_timestamp(1.0),
        ])

        seen = set()
        deduped: list[str] = []
        for ts in candidates:
            if ts not in seen:
                seen.add(ts)
                deduped.append(ts)
        return deduped

    def _attempt_thumbnail(ts: str, tpath: Path, vpath: Path) -> bool:
        """Run ffmpeg once for the given timestamp; return success flag."""
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            ts,
            "-i",
            str(vpath),
            "-frames:v",
            "1",
            "-vf",
            (
                f"scale={THUMB_SIZE}:force_original_aspect_ratio=decrease,"
                f"pad={THUMB_SIZE}:(320-iw)/2:(180-ih)/2"
            ),
            str(tpath),
        ]
        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=90,
            )
            print(f"[THUMB] ✓ {tpath.name} @ {ts}")
            _log(f"OK {vpath.name} @ {ts}")
            return True
        except subprocess.TimeoutExpired:
            print(f"[THUMB] ✖ timeout generating {vpath.name} @ {ts}")
            _log(f"TIMEOUT {vpath.name} @ {ts}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"[THUMB] ✖ ffmpeg error for {vpath.name} @ {ts}: {e}")
            stderr = e.stderr.decode("utf-8", "ignore") if getattr(e, "stderr", None) else str(e)
            _log(f"FFMPEG_ERROR {vpath.name} @ {ts} :: {stderr}")
            return False

    def _worker() -> None:
        vpath = VIDEO_DIR / video_filename
        tpath = thumb_path_for(video_filename)

        if tpath.exists() or not vpath.exists():
            return  # nothing to do

        THUMB_DIR.mkdir(parents=True, exist_ok=True)

        for ts in _compute_timestamps(vpath):
            if _attempt_thumbnail(ts, tpath, vpath):
                return

    _pool.submit(_worker)


# Maintenance - sync()
def _valid_video_files() -> List[Path]:
    return [
        p for p in VIDEO_DIR.iterdir() if p.suffix.lower() in VIDEO_EXTS and p.is_file()
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
            new = {k: v for k, v in data.items() if _video_stem_ci(k) in valid_stems_ci}
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

    force_regen:
      False (default) – generate only missing thumbnails.
      True            – delete every thumbnail and rebuild.
    """
    THUMB_DIR.mkdir(parents=True, exist_ok=True)

    video_files = _valid_video_files()
    valid_stems_ci = {_video_stem_ci(p.name) for p in video_files}
    thumb_files = list(THUMB_DIR.glob(f"*{THUMB_EXT}"))
    thumb_stems_ci = {_video_stem_ci(p.name) for p in thumb_files}

    # 1) Remove orphan thumbnails (no matching video)
    for thumb in thumb_files:
        if _video_stem_ci(thumb.name) not in valid_stems_ci:
            thumb.unlink(missing_ok=True)
            print(f"[SYNC] 🔥 {thumb.name}")

    # 2) Optionally delete all remaining thumbnails (full rebuild)
    if force_regen:
        for thumb in THUMB_DIR.glob(f"*{THUMB_EXT}"):
            thumb.unlink(missing_ok=True)
        thumb_stems_ci.clear()
        print("[SYNC] 🔁 forced full rebuild - all thumbs removed")

    # 3) Queue generation jobs
    to_generate = [
        v for v in video_files if _video_stem_ci(v.name) not in thumb_stems_ci or force_regen
    ]
    for vf in to_generate:
        generate_async(vf.name)

    # 4) Clean metadata + database
    _clean_metadata(valid_stems_ci)
    _clean_database(valid_stems_ci)

    print(f"[SYNC] ✓ queued {len(to_generate)} thumbnail job(s)")


def retry_failed_thumbnails(log_path: Path = THUMB_LOG) -> int:
    """
    Retry only thumbnails that previously failed (TIMEOUT/FFMPEG_ERROR) and
    currently have no thumbnail file. Returns number of jobs queued.
    """
    if not log_path.exists():
        print("[RETRY] No log file found; nothing to retry.")
        return 0

    failed: set[str] = set()
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(("TIMEOUT", "FFMPEG_ERROR")):
            _, rest = line.split(" ", 1)
            fname, _, _ = rest.partition(" @ ")
            failed.add(fname.strip())

    queued = 0
    for fname in failed:
        tpath = thumb_path_for(fname)
        if tpath.exists():
            continue
        generate_async(fname)
        queued += 1

    print(f"[RETRY] queued {queued} retry job(s)")
    return queued


# CLI entry-point
def _cli() -> None:
    parser = argparse.ArgumentParser(description="Thumbnail + metadata maintenance utility")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete all thumbnails then rebuild from scratch",
    )
    parser.add_argument(
        "--retry-failures",
        action="store_true",
        help="Retry only the thumbnails that previously failed (per log)",
    )
    args = parser.parse_args()

    if args.retry_failures:
        retry_failed_thumbnails()
    else:
        sync(force_regen=args.force)

    # wait for background jobs to finish before exiting
    _pool.shutdown(wait=True)


if __name__ == "__main__":
    _cli()
