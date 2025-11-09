"""Compatibility stub: subtitles module archived.

This file is a compact compatibility stub. The fuller archived copy is
available at `archive/python_legacy/subtitles.py`.
"""
import warnings
from typing import Iterator, List

warnings.warn(
    "subtitles module functionality has been archived to archive/python_legacy/subtitles.py",
    DeprecationWarning,
)


def has_any_subs(video_path: str) -> bool:
    """Compatibility: always indicate no subtitles are present."""
    return False


def iter_video_files(root: str) -> Iterator[str]:
    if False:
        yield ""


def generate_for_file(video_path: str) -> dict:
    return {"file": video_path, "language": None, "duration": 0, "segments": 0, "outputs": []}


def generate_missing(root: str = "videos") -> List[dict]:
    return []


def within_quiet_hours(*_args, **_kwargs) -> bool:
    return False
