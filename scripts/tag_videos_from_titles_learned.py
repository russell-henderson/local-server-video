import argparse
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from difflib import SequenceMatcher

VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v"}

# ...existing code...
VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v"}

# Tokens you typically do NOT want as tags.
STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "to", "of", "in", "on", "for", "with",
    "part", "pt", "vol", "volume", "ep", "episode", "full", "hd", "fhd",
    "uhd", "1080p", "720p", "2160p", "4k", "8k", "x264", "x265", "h264",
    "h265", "hevc", "web", "rip", "webrip", "bluray", "brrip", "your",
    "name", "best", "version", "final", "cut", "extended", "unrated",
    "director", "s", "edition", "stop", "complete", "collection",
    "remastered", "repack", "proper", "limited", "internal", "subbed",
    "dubbed", "subs", "dub", "multi", "audio", "video", "codec", "release",
    "group", "sample", "trailer", "teaser", "preview", "behind", "scenes",
    "bts", "bonus", "featurette", "deleted", "scene", "special", "effects",
    "vfx", "visual", "fx", "about", "this", "that", "it", "is", "are",
    "was", "were", "be", "by", "as", "at", "from", "up", "down", "out",
    "over", "under", "again", "further", "then", "once", "incestflix",
    "horrible", "mean", "screw", "fucks", "shit", "damn", "hell", "cock",
    "curious", "date", "time", "week", "month", "year", "day", "stick",
    "plays", "play", "watch", "seen", "viewed", "my", "his", "her", "our",
    "their", "me", "him", "us", "them", "you", "he", "she", "they",
    "fantasy", "finally", "actually", "really", "just", "only", "ever",
    "never", "always", "sometimes", "maybe", "probably", "definitely",
    "absolutely", "seriously", "literally", "figuratively", "basically",
    "essentially", "overall", "simply", "quite", "pretty", "rather",
    "somewhat", "extremely", "incredibly", "totally", "completely",
    "utterly", "highly", "deeply", "truly", "genuinely", "particularly",
    "especially", "sorta", "kinda", "lot", "lots", "bit", "bits", "bunch",
    "couple", "few", "several", "many", "much", "most", "least", "enough",
    "plenty", "ton", "tons", "whole", "entire", "particular", "certain",
    "various", "different", "needs", "want", "wants", "need", "like",
    "likes", "dislike", "feels", "feel", "feeling", "felt", "thought",
    "think", "thinking", "thoughts", "guess", "guesses", "hope", "hopes",
    "expect", "expects", "expected", "wish", "wishes", "believe",
    "believes", "believed", "know", "knows", "knew", "understand",
    "understands", "understood", "see", "sees", "saw", "watching",
}

# Optional: you can hardcode some rule tags if you want higher precision.
# If empty, the script still works using keyword extraction + existing-tag mapping.
TAG_RULES: Dict[str, List[str]] = {
    # Example:
    # "behind_the_scenes": ["behind the scenes", "bts"],
}


@dataclass
class SidecarPolicy:
    merge_with_existing: bool = True
    overwrite_existing: bool = False
    write_to_ai_labels: bool = False


def normalize_text(s: str) -> str:
    s = s.lower()
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def tokenize(s: str) -> List[str]:
    tokens = [t for t in normalize_text(s).split(
        " ") if t and t not in STOPWORDS]
    tokens = [t for t in tokens if not re.fullmatch(r"\d+", t)]
    return tokens


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def sidecar_path_for_video(video_path: Path, mode: str) -> Path:
    # mode:
    #   - "adjacent-dotjson": <video>.json (movie.mp4.json)
    #   - "stem-dotjson": <stem>.json (movie.json)
    if mode == "stem-dotjson":
        return video_path.with_suffix(".json")
    return Path(str(video_path) + ".json")


def load_sidecar(p: Path) -> Dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_sidecar(p: Path, data: Dict) -> None:
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                 encoding="utf-8")


def merge_tags(existing: List[str], new_tags: List[str]) -> List[str]:
    s = {t.strip() for t in (existing or []) if t and t.strip()}
    for t in new_tags:
        if t and t.strip():
            s.add(t.strip())
    return sorted(s, key=lambda x: x.lower())


def learn_tags_from_sidecars(videos_dir: Path, sidecar_mode: str, field: str) -> Set[str]:
    learned: Set[str] = set()
    for vp in videos_dir.rglob("*"):
        if not (vp.is_file() and vp.suffix.lower() in VIDEO_EXTS):
            continue
        sc = sidecar_path_for_video(vp, sidecar_mode)
        data = load_sidecar(sc)
        tags = data.get(field, [])
        if isinstance(tags, list):
            for t in tags:
                if isinstance(t, str) and t.strip():
                    learned.add(t.strip())
    return learned


def learn_tags_from_tags_page(tags_url: str) -> Set[str]:
    """
    Very lightweight HTML scrape:
    - Pulls page HTML
    - Extracts candidate tokens that look like tags from link/text nodes
    You can tighten this later if your /tags HTML structure is known.
    """
    learned: Set[str] = set()
    try:
        with urllib.request.urlopen(tags_url, timeout=5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return learned

    # Common patterns: tag chips, anchor text, data-tag attr, etc.
    # We'll extract:
    # - data-tag="something"
    # - >something</a> for simple tag lists
    learned.update(re.findall(
        r'data-tag\s*=\s*"([^"]+)"', html, flags=re.IGNORECASE))
    # Anchor text (coarse): keep short-ish strings
    for m in re.findall(r">([^<]{1,40})</a>", html, flags=re.IGNORECASE):
        s = m.strip()
        if s and not re.search(r"\s{2,}", s):
            # avoid obvious UI words
            if s.lower() in {"tags", "home", "back", "next", "prev", "previous"}:
                continue
            learned.add(s)
    return {t.strip() for t in learned if t and t.strip()}


def build_tag_vocabulary(videos_dir: Path, sidecar_mode: str, field: str, tags_url: Optional[str]) -> Tuple[Set[str], Dict[str, str]]:
    """
    Returns:
      - raw tags set
      - normalized->canonical map (for exact matching)
    """
    learned = learn_tags_from_sidecars(videos_dir, sidecar_mode, field)
    if tags_url:
        learned |= learn_tags_from_tags_page(tags_url)

    norm_map: Dict[str, str] = {}
    for t in learned:
        nt = normalize_text(t)
        # keep first-seen canonical; prefer shorter canonical if collision
        if nt not in norm_map or len(t) < len(norm_map[nt]):
            norm_map[nt] = t

    return learned, norm_map


def map_to_existing_tag(candidate: str, vocab: Set[str], norm_map: Dict[str, str], min_ratio: float) -> str:
    """
    Map candidate to existing tag:
      1) exact normalized match
      2) fuzzy match to closest existing normalized string
      3) fallback to candidate (new tag)
    """
    nc = normalize_text(candidate)
    if not nc:
        return candidate

    if nc in norm_map:
        return norm_map[nc]

    # Fuzzy match against normalized vocabulary
    best_tag = None
    best_score = 0.0
    for existing in vocab:
        ne = normalize_text(existing)
        if not ne:
            continue
        score = similarity(nc, ne)
        if score > best_score:
            best_score = score
            best_tag = existing

    if best_tag and best_score >= min_ratio:
        return best_tag

    return candidate


def find_rule_tags(title: str) -> Set[str]:
    norm = normalize_text(title)
    tags = set()
    for tag, phrases in TAG_RULES.items():
        for p in phrases:
            if normalize_text(p) in norm:
                tags.add(tag)
                break
    return tags


def derive_keyword_tags(title: str, max_extra: int = 4) -> List[str]:
    tokens = tokenize(title)
    # Prefer longer words first, stable ordering
    tokens = sorted(set(tokens), key=lambda t: (-len(t), t))
    extras: List[str] = []
    for t in tokens:
        if len(t) < 4:
            continue
        extras.append(t)
        if len(extras) >= max_extra:
            break
    return extras


def process_video(
    video_path: Path,
    sidecar_mode: str,
    policy: SidecarPolicy,
    dry_run: bool,
    vocab: Set[str],
    norm_map: Dict[str, str],
    min_ratio: float,
    field: str,
) -> Tuple[bool, List[str], Path]:
    title = video_path.stem

    # Candidate tags: rules + keywords
    rule_tags = find_rule_tags(title)
    extras = derive_keyword_tags(title, max_extra=4)
    candidates = list(sorted(rule_tags)) + \
        [t for t in extras if t not in rule_tags]

    # Map to existing vocabulary (prevents fragmentation)
    mapped = []
    for c in candidates:
        mapped.append(map_to_existing_tag(
            c, vocab, norm_map, min_ratio=min_ratio))

    # Dedupe while preserving order
    seen = set()
    derived: List[str] = []
    for t in mapped:
        key = normalize_text(t)
        if key and key not in seen:
            seen.add(key)
            derived.append(t)

    sidecar_path = sidecar_path_for_video(video_path, sidecar_mode)
    data = load_sidecar(sidecar_path)
    existing = data.get(field, [])

    if policy.overwrite_existing:
        final_tags = derived
    elif policy.merge_with_existing:
        final_tags = merge_tags(existing, derived)
    else:
        final_tags = existing if existing else derived

    changed = (existing != final_tags)
    if changed:
        data[field] = final_tags
        data.setdefault("title", title)
        if not dry_run:
            save_sidecar(sidecar_path, data)

    return changed, final_tags, sidecar_path


def main():
    ap = argparse.ArgumentParser(
        description="Derive tags from video filenames using existing tags as vocabulary.")
    ap.add_argument("--videos-dir", default=r"Z:\local-video-server\videos")
    ap.add_argument(
        "--sidecar-mode", choices=["adjacent-dotjson", "stem-dotjson"], default="adjacent-dotjson")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--no-merge", action="store_true")
    ap.add_argument("--ai-labels", action="store_true")
    ap.add_argument("--tags-url", default="",
                    help="Optional. e.g. http://192.168.4.96:8080/tags")
    ap.add_argument("--min-similarity", type=float, default=0.86,
                    help="Fuzzy match threshold (0-1).")
    args = ap.parse_args()

    policy = SidecarPolicy(
        merge_with_existing=not args.no_merge and not args.overwrite,
        overwrite_existing=args.overwrite,
        write_to_ai_labels=args.ai_labels,
    )

    videos_dir = Path(args.videos_dir)
    if not videos_dir.exists():
        raise SystemExit(f"Videos folder not found: {videos_dir}")

    field = "ai_labels" if policy.write_to_ai_labels else "tags"
    tags_url = args.tags_url.strip() or None

    vocab, norm_map = build_tag_vocabulary(
        videos_dir, args.sidecar_mode, field, tags_url)

    vids = [p for p in videos_dir.rglob(
        "*") if p.is_file() and p.suffix.lower() in VIDEO_EXTS]

    print(f"Learned tags: {len(vocab)} (field='{field}')")
    if tags_url:
        print(f"Also attempted tag learning from: {tags_url}")

    changed_count = 0
    for vp in vids:
        changed, tags, sidecar = process_video(
            vp, args.sidecar_mode, policy, args.dry_run,
            vocab=vocab, norm_map=norm_map,
            min_ratio=args.min_similarity,
            field=field,
        )
        if changed:
            changed_count += 1
            print(f"[CHANGED] {vp.name}")
            print(f"  -> {sidecar.name}")
            print(f"  {field}: {tags}")

    print(
        f"\nDone. Videos scanned: {len(vids)} | Sidecars updated: {changed_count} | dry-run={args.dry_run}")


if __name__ == "__main__":
    main()
