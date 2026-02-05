Found it. Your `/tags` page is **not reading sidecars at all**. It’s calling:

```py
sorted_tags = cache.get_all_unique_tags()
```

So your script wrote correct `*.mp4.json` tags, but the UI is still showing whatever the **cache/DB** thinks the tags are.

### Fix strategy

Make `/tags` (and `/tag/<tag>`) **sidecar-first**, with a small TTL cache so it stays fast.

You only need to change **`/app/main.py`**.

---

## Step 1: Patch `main.py` to read tags from sidecars

### 1) Add these imports (near the top of `main.py`)

If you already have some of these, don’t duplicate them.

```py
import json
import time
from pathlib import Path
```

### 2) Add these helper functions (put them anywhere above the routes, for example near other helpers)

```py
# --- Sidecar tag aggregation (sidecar-first) ---

_SIDECAR_TAG_CACHE = {"ts": 0.0, "tags": [], "by_tag": {}}
_SIDECAR_TAG_TTL_SECONDS = 10.0

_VIDEO_EXTS = (".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v")

def _videos_dir() -> Path:
    # In docker-compose, ./videos is mounted to /app/videos
    # app.root_path is /app
    return Path(app.root_path) / "videos"

def _iter_sidecars(vdir: Path):
    # sidecars are <video>.<ext>.json, e.g. movie.mp4.json
    for ext in _VIDEO_EXTS:
        yield from vdir.glob(f"*{ext}.json")

def _read_tags_from_sidecar(p: Path) -> list[str]:
    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        tags = data.get("tags", [])
        if isinstance(tags, list):
            return [t.strip() for t in tags if isinstance(t, str) and t.strip()]
    except Exception:
        pass
    return []

def _normalize_tag(t: str) -> str:
    return t.strip().lstrip("#").strip()

def get_sidecar_tags_snapshot(force: bool = False):
    """
    Returns:
      tags_sorted: list[str]
      by_tag: dict[str, list[str]]  # tag -> filenames (video filename, without .json)
    """
    now = time.time()
    if not force and (now - _SIDECAR_TAG_CACHE["ts"] < _SIDECAR_TAG_TTL_SECONDS):
        return _SIDECAR_TAG_CACHE["tags"], _SIDECAR_TAG_CACHE["by_tag"]

    vdir = _videos_dir()
    tags_set = set()
    by_tag: dict[str, list[str]] = {}

    if vdir.exists():
        for sc in _iter_sidecars(vdir):
            # convert "<name>.mp4.json" -> "<name>.mp4"
            video_filename = sc.name[:-5]  # strip trailing ".json"
            tags = _read_tags_from_sidecar(sc)
            for raw in tags:
                tag = _normalize_tag(raw)
                if not tag:
                    continue
                tags_set.add(tag)
                by_tag.setdefault(tag, []).append(video_filename)

    tags_sorted = sorted(tags_set, key=lambda x: x.lower())
    # stable ordering for filenames too
    for k in list(by_tag.keys()):
        by_tag[k] = sorted(set(by_tag[k]), key=lambda x: x.lower())

    _SIDECAR_TAG_CACHE["ts"] = now
    _SIDECAR_TAG_CACHE["tags"] = tags_sorted
    _SIDECAR_TAG_CACHE["by_tag"] = by_tag
    return tags_sorted, by_tag
```

---

## Step 2: Replace the `/tags` route (lines 691–696)

Replace your current function:

```py
@app.route('/tags')
@performance_monitor("route_tags")
def tags_page():
    """Optimized tags page with cached data"""
    sorted_tags = cache.get_all_unique_tags()
    return render_template('tags.html', tags=sorted_tags, tag_count=len(sorted_tags))
```

With this:

```py
@app.route('/tags')
@performance_monitor("route_tags")
def tags_page():
    """Tags page (sidecar-first)"""
    sorted_tags, _ = get_sidecar_tags_snapshot()
    return render_template('tags.html', tags=sorted_tags, tag_count=len(sorted_tags))
```

---

## Step 3: Add a safe fallback in `/tag/<tag>` so clicking a new tag works

Right now you have:

```py
filtered_videos = cache.get_videos_by_tag_optimized(normalized_tag)
```

If the cache doesn’t know sidecar tags, that will return empty.

Change that block to:

```py
sorted_tags, by_tag = get_sidecar_tags_snapshot()
filenames = by_tag.get(normalized_tag, [])

if filenames:
    # Build minimal video dicts that your templates expect.
    # If your cache can enrich, do it; otherwise fallback to filename-only.
    filtered_videos = []
    for fn in filenames:
        try:
            v = cache.get_video_data(fn)  # if you have this method
            if v:
                filtered_videos.append(v)
            else:
                filtered_videos.append({"filename": fn})
        except Exception:
            filtered_videos.append({"filename": fn})
else:
    # fallback to existing cache method (covers DB-only tags)
    filtered_videos = cache.get_videos_by_tag_optimized(normalized_tag)
```

If your `cache_manager` doesn’t have `get_video_data()`, keep the `{"filename": fn}` fallback only. Your templates already use filename in most places.

---

## Step 4: Restart and verify

```powershell
docker compose restart video-server
```

Then refresh:

* `http://192.168.4.96:5000/tags`
* `http://192.168.4.96:8080/tags`

You should now see tags like `kelly`, `momma`, `payne` immediately.

---

## Why this is the right fix

* You already proved sidecars are correct and mounted at `/app/videos`.
* Your UI was reading `cache.get_all_unique_tags()` (DB/cached view), not sidecars.
* This makes tags reflect what your script writes, without needing DB migrations or reindex plumbing.


