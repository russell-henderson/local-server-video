# subtitles.py
import os
import threading
from datetime import datetime
from typing import Iterator

from faster_whisper import WhisperModel
from config_subtitles import SUBTITLES

VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi"}

_model_lock = threading.Lock()
_model_singleton: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model_singleton
    with _model_lock:
        if _model_singleton is None:
            _model_singleton = WhisperModel(
                SUBTITLES.model_size,
                device="auto",
                compute_type=SUBTITLES.compute_type,
            )
        return _model_singleton


def _fmt_ts_vtt(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _fmt_ts_srt(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write_vtt(segments, out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            start = _fmt_ts_vtt(seg.start)
            end = _fmt_ts_vtt(seg.end)
            text = (seg.text or "").strip()
            if text:
                f.write(f"{start} --> {end}\n{text}\n\n")


def _write_srt(segments, out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        idx = 1
        for seg in segments:
            text = (seg.text or "").strip()
            if not text:
                continue
            start_ts = _fmt_ts_srt(seg.start)
            end_ts = _fmt_ts_srt(seg.end)
            f.write(f"{idx}\n{start_ts} --> {end_ts}\n{text}\n\n")
            idx += 1


def has_any_subs(video_path: str) -> bool:
    base, _ = os.path.splitext(video_path)
    for ext in (".vtt", ".srt"):
        if os.path.exists(f"{base}{ext}"):
            return True
    return False


def generate_for_file(video_path: str) -> dict:
    """
    Transcribe a single file and write .vtt and/or .srt next to it.
    Returns stats dict.
    """
    model = _get_model()
    task = "translate" if SUBTITLES.translate_to_english else "transcribe"

    segments, info = model.transcribe(
        video_path,
        language=SUBTITLES.language,
        task=task,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=250),
    )

    segs = list(segments)

    base, _ = os.path.splitext(video_path)
    wrote = []

    if SUBTITLES.out_format and "vtt" in SUBTITLES.out_format:
        out_vtt = f"{base}.vtt"
        _write_vtt(segs, out_vtt)
        wrote.append(out_vtt)

    if SUBTITLES.out_format and "srt" in SUBTITLES.out_format:
        out_srt = f"{base}.srt"
        _write_srt(segs, out_srt)
        wrote.append(out_srt)

    return {
        "file": video_path,
        "language": info.language,
        "duration": info.duration,
        "segments": len(segs),
        "outputs": wrote,
    }


def iter_video_files(root: str) -> Iterator[str]:
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if os.path.splitext(name)[1].lower() in VIDEO_EXTS:
                yield os.path.join(dirpath, name)


def generate_missing(root: str = SUBTITLES.videos_root) -> list[dict]:
    results = []
    for path in iter_video_files(root):
        if not has_any_subs(path):
            results.append(generate_for_file(path))
    return results


def within_quiet_hours(now: datetime | None = None) -> bool:
    now = now or datetime.now()
    start, end = SUBTITLES.quiet_hours
    if start <= end:
        return start <= now.hour < end
    # crosses midnight
    return now.hour >= start or now.hour < end
