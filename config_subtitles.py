# config_subtitles.py
from dataclasses import dataclass


@dataclass
class SubtitleConfig:
    enabled: bool = True
    model_size: str = "medium"     # tiny, base, small, medium, large-v3
    compute_type: str = "auto"     # auto, int8, float16, float32
    language: str | None = None    # None = auto-detect
    translate_to_english: bool = False
    out_format: list[str] | None = None   # which sidecars to write
    max_concurrent: int = 1        # keep it low to avoid CPU spikes
    quiet_hours: tuple[int, int] = (1, 6)   # 1am–6am preferred window
    videos_root: str = "videos"    # adjust if different
    subs_ext: str = ".vtt"         # default track we attach in the player

    def __post_init__(self):
        if self.out_format is None:
            self.out_format = ["vtt", "srt"]


SUBTITLES = SubtitleConfig()
