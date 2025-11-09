"""
Original subtitle module (archived copy)

This is an archived copy of the lightweight compatibility shim that
replaced the original subtitle backend. Kept for historical traceability
and reference.
"""
from typing import Iterator, List


def has_any_subs(video_path: str) -> bool:
    """Always return False: no subtitles are available."""
    return False


def iter_video_files(root: str) -> Iterator[str]:
    """Yield nothing — subtitle generation removed."""
    if False:
        yield ""


def generate_for_file(video_path: str) -> dict:
    """Stub: subtitle generation removed.

    Returns a minimal dict for compatibility, with no outputs.
    """
    return {
        "file": video_path,
        "language": None,
        "duration": 0,
        "segments": 0,
        "outputs": [],
    }


def generate_missing(root: str = "videos") -> List[dict]:
    return []


def within_quiet_hours(*_args, **_kwargs) -> bool:
    return False
