"""Build responsive gallery thumbnail derivatives.

Original gallery files remain in ``images/gallery``.  This command writes
cacheable WebP derivatives under ``static/gallery-thumbnails`` and is safe to
run repeatedly; unchanged files are skipped.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageOps


SOURCE_DIR = Path("images/gallery")
OUTPUT_DIR = Path("static/gallery-thumbnails")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
DEFAULT_SIZES = (160, 320, 640, 1280)


def output_path(source: Path, size: int) -> Path:
    return OUTPUT_DIR / str(size) / f"{source.name}.webp"


def build_one(source: Path, sizes: tuple[int, ...], quality: int) -> tuple[str, int]:
    created = 0
    try:
        with Image.open(source) as original:
            # Preserve animated formats as a representative first frame for
            # discovery cards; the original remains available in the lightbox.
            original.seek(0)
            image = ImageOps.exif_transpose(original).convert("RGB")
            for size in sizes:
                target = output_path(source, size)
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and target.stat().st_mtime_ns >= source.stat().st_mtime_ns:
                    continue
                derivative = image.copy()
                derivative.thumbnail((size, size), Image.Resampling.LANCZOS)
                derivative.save(target, "WEBP", quality=quality, method=4)
                created += 1
    except Exception as exc:  # keep one corrupt asset from stopping the batch
        print(f"[GALLERY THUMB] failed {source}: {exc}")
    return source.name, created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--quality", type=int, default=82)
    parser.add_argument("--sizes", nargs="+", type=int, default=list(DEFAULT_SIZES))
    args = parser.parse_args()

    sources = sorted(
        path for path in SOURCE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ) if SOURCE_DIR.exists() else []
    if not sources:
        print("[GALLERY THUMB] no gallery images found")
        return 0

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        results = list(pool.map(lambda path: build_one(path, tuple(args.sizes), args.quality), sources))

    generated = sum(count for _, count in results)
    print(f"[GALLERY THUMB] scanned={len(sources)} generated={generated} sizes={args.sizes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
