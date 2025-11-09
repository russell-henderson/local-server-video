"""Compatibility stub for subtitle configuration.

An archived copy exists at `archive/python_legacy/config_subtitles.py`.
This stub provides a minimal configuration object for imports that
still reference `config_subtitles.SUBTITLES`.
"""

from dataclasses import dataclass
import warnings

warnings.warn(
    "config_subtitles archived to archive/python_legacy/config_subtitles.py",
    DeprecationWarning,
)


@dataclass
class SubtitleConfig:
    enabled: bool = False
    model_size: str = "medium"
    compute_type: str = "auto"
    language: str | None = None
    translate_to_english: bool = False
    out_format: list[str] | None = None
    max_concurrent: int = 1
    quiet_hours: tuple[int, int] = (1, 6)
    videos_root: str = "videos"
    subs_ext: str = ".vtt"

    def __post_init__(self):
        if self.out_format is None:
            self.out_format = ["vtt", "srt"]


SUBTITLES = SubtitleConfig()
