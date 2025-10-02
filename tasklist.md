Absolutely. You can add **fully automatic subtitle generation** that runs locally, stays privacy-safe, and “just works” across your whole library. Here is a clean, offline-first setup that fits the refactor you just finished.

---

# What you’ll get

* Auto-generated **.vtt** (and **.srt**) sidecars for every video.
* Runs **locally** using **faster-whisper**. GPU if available, CPU otherwise.
* Batch “generate all missing” job + on-demand lazy generation when a video is first watched.
* Tracks are picked up automatically by the unified player with a `<track>` tag.
* Styling stays in your current dark theme.

---

# Option overview

* **Recommended**: Local **faster-whisper** (highest quality, private).
* **Lighter**: **whisper.cpp** binaries if you want a tiny footprint and no Python wheels.
* **Fallback**: OpenAI Whisper API only if you already use it and want cloud speed. Kept behind a feature flag.

I will wire the **faster-whisper** path below end to end.

---

# 1) Install dependencies

```bash
# in your venv
pip install faster-whisper==1.0.3 numpy==2.1.1

# Optional: PyTorch for GPU acceleration (skip if CPU-only)
# Windows CUDA example (adjust to your CUDA version):
# pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Models live in `~/.cache/faster_whisper`. First run downloads automatically.

---

# 2) Add a config toggle

Create `config_subtitles.py`:

```python
# config_subtitles.py
from dataclasses import dataclass

@dataclass
class SubtitleConfig:
    enabled: bool = True
    model_size: str = "medium"     # tiny, base, small, medium, large-v3
    compute_type: str = "auto"     # auto, int8, float16, float32
    language: str | None = None    # None = auto-detect
    translate_to_english: bool = False
    out_format: list[str] = ("vtt", "srt")  # which sidecars to write
    max_concurrent: int = 1        # keep it low to avoid CPU spikes
    quiet_hours: tuple[int, int] = (1, 6)   # 1am–6am preferred window
    videos_root: str = "videos"    # adjust if different
    subs_ext: str = ".vtt"         # default track we attach in the player

SUBTITLES = SubtitleConfig()
```

---

# 3) Subtitle engine

Create `subtitles.py`:

```python
# subtitles.py
import os
import threading
from datetime import datetime, timedelta
from typing import Iterable

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
                device="cuda" if SUBTITLES.compute_type == "auto" else "auto",
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
            f.write(f"{idx}\n{_fmt_ts_srt(seg.start)} --> {_fmt_ts_srt(seg.end)}\n{text}\n\n")
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

    if "vtt" in SUBTITLES.out_format:
        out_vtt = f"{base}.vtt"
        _write_vtt(segs, out_vtt)
        wrote.append(out_vtt)

    if "srt" in SUBTITLES.out_format:
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

def iter_video_files(root: str) -> Iterable[str]:
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
```

---

# 4) CLI for batch jobs

Add `manage_subs.py`:

```python
# manage_subs.py
import argparse
from subtitles import generate_for_file, generate_missing
from config_subtitles import SUBTITLES

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", help="Generate subtitles for a single file")
    p.add_argument("--all-missing", action="store_true", help="Generate for all videos lacking tracks")
    args = p.parse_args()

    if args.file:
        stats = generate_for_file(args.file)
        print(stats)
        return

    if args.all_missing:
        stats = generate_missing(SUBTITLES.videos_root)
        print(f"Generated {len(stats)} files")
        return

    p.print_help()

if __name__ == "__main__":
    main()
```

Now you can run:

```bash
python manage_subs.py --all-missing
# or a single file
python manage_subs.py --file "videos/sample.mp4"
```

Schedule this nightly in Task Scheduler inside your quiet hours.

---

# 5) Hook into the Watch page (lazy generation)

If a user opens a video that has no subs yet, kick off a background generation and show the track as soon as it appears.

In your Flask app (where you serve `/watch/<filename>`), add:

```python
# app_subs_integration.py (fold into your existing app code)
import os
import threading
from flask import Blueprint, send_file, abort, current_app, url_for
from subtitles import has_any_subs, generate_for_file
from config_subtitles import SUBTITLES

bp_subs = Blueprint("subs", __name__)

@bp_subs.route("/subs/<path:relpath>")
def serve_sub(relpath: str):
    # relpath like "folder/video.vtt" or "video.srt"
    abs_path = os.path.join(SUBTITLES.videos_root, relpath)
    if not os.path.exists(abs_path):
        abort(404)
    return send_file(abs_path, mimetype="text/vtt" if abs_path.endswith(".vtt") else "application/x-subrip")

def ensure_subs_async(abs_video_path: str):
    def _job():
        try:
            generate_for_file(abs_video_path)
        except Exception as ex:
            current_app.logger.exception("Subtitle generation failed: %s", ex)
    threading.Thread(target=_job, daemon=True).start()

def subs_track_url(rel_video_path: str) -> str | None:
    # return the best available track for the player
    base_no_ext, _ = os.path.splitext(rel_video_path)
    vtt_rel = f"{base_no_ext}.vtt"
    srt_rel = f"{base_no_ext}.srt"
    for rel in (vtt_rel, srt_rel):
        if os.path.exists(os.path.join(SUBTITLES.videos_root, rel)):
            return url_for("subs.serve_sub", relpath=rel)
    return None
```

Register the blueprint once:

```python
# in your app factory or main
app.register_blueprint(bp_subs)
```

In the watch route handler, before rendering:

```python
# Given: filename is the relative path from videos root
from app_subs_integration import has_any_subs, ensure_subs_async, subs_track_url
from config_subtitles import SUBTITLES

abs_path = os.path.join(SUBTITLES.videos_root, filename)
if SUBTITLES.enabled and not has_any_subs(abs_path):
    # Fire and forget. The first playback will be without subs, but it will appear quickly.
    ensure_subs_async(abs_path)

track_href = subs_track_url(filename)  # None if not ready yet
return render_template("watch.html", filename=filename, subs_href=track_href)
```

---

# 6) Template change to load tracks

In `templates/_player.html` add the track element only when available:

```html
<video
  id="video"
  src="{{ url_for('video', filename=filename) }}"
  playsinline
  controls
>
  {% if subs_href %}
  <track kind="subtitles" src="{{ subs_href }}" srclang="en" label="Subtitles" default>
  {% endif %}
</video>
```

No changes needed in `player.js` if you are using native `<video controls>`. If you built custom controls, keep the `<track>` tag as above and the browser will handle it. You can add a captions toggle button later by reading `video.textTracks`.

---

# 7) Optional finishing touches

* **Language auto detect** is already on. You can set `translate_to_english=True` to always produce English.
* Generate a **second track**:

  * Keep `.vtt` as the default for the player.
  * Also write `.srt` for compatibility.
* Add an **Admin** button “Generate subtitles for all missing” that calls a small endpoint which triggers `generate_missing()` in a thread and streams progress to the page.
* Add a **subtitle style** snippet in your CSS if you want a consistent look:

  ```css
  /* app.css */
  ::cue {
    font-family: ui-sans-serif, system-ui, Inter, Roboto, "Segoe UI", Arial;
    font-size: 18px;
    line-height: 1.35;
    color: var(--text);
    background: rgba(0,0,0,.35);
    text-shadow: 0 1px 2px rgba(0,0,0,.6);
  }
  ```

---

## Cursor prompt to wire it now

Copy and paste:

Implement automatic subtitles:
* [ ] 1) Add Files:

* config_subtitles.py (as provided)
* subtitles.py (as provided)
* manage_subs.py (as provided)
* app_subs_integration.py (as provided)

1) Register the blueprint in app init and update the /watch route to:

* call ensure_subs_async for missing tracks
* pass subs_href into templates

* [ ] date templates/_player.html:

* [ ] ude <track> only when subs_href is present

* [ ]  a CSS ::cue style in app.css for better readability

* [ ] 5) Verify:

* [ ] Run `python manage_subs.py --all-missing` to generate batch subtitles
* [ ] Open a video without subs to test lazy generation
* [ ] Confirm the <track> loads and captions show under the native controls

* [ ] If you want me to add the Admin page actions, a progress stream, or a “Captions” toggle in your custom controls, tell me which and I will drop the full code.
