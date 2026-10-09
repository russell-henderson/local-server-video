"""Warm the same versioned gallery derivatives used by the web application."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.gallery_index import GalleryIndex
from config import get_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args()
    config = get_config()
    index = GalleryIndex(Path(config.gallery_directory), Path(config.gallery_thumbnail_directory), Path(config.gallery_index_db))
    try:
        index.refresh(force=True, wait=True)
        if index.status()['error']:
            print(index.status()['error'])
            return 1
        records = index.snapshot()['image_meta']
        with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as pool:
            list(pool.map(lambda item: index._build(*item), records.items()))
        failures = index.status()['thumbnail_errors']
        print(f'Gallery: scanned={len(records)}, failed={len(failures)}')
        for name, error in failures.items():
            print(f'{name}: {error}')
        return int(bool(failures))
    finally:
        index.close()


if __name__ == '__main__':
    raise SystemExit(main())
