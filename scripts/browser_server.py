"""Launch a fully isolated browser-test server. No production startup maintenance."""
import argparse
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.test_library import seed_library


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--count', type=int, default=92)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='lvs-browser-') as temporary:
        root = Path(temporary)
        seed_library(root, args.count)
        os.chdir(root)
        os.environ['LVS_DB_PATH'] = str(root / 'data/metadata.db')
        from main import app
        from backend.app import legacy_runtime as legacy
        from database_migration import VideoDatabase
        legacy.gallery_index.refresh(force=True, wait=True)
        db = VideoDatabase()
        group_id = db.create_gallery_group('Fixture group', 'image-0000.jpg')
        db.add_images_to_group(group_id, ['image-0000.jpg', 'image-0001.jpg'])
        # Warm only the synthetic fixtures, never a real library.
        for name, meta in legacy.gallery_index.snapshot()['image_meta'].items():
            legacy.gallery_index._build(name, meta)
        try:
            app.run(host='127.0.0.1', port=args.port, threaded=True, use_reloader=False)
        finally:
            legacy.gallery_index.close()


if __name__ == '__main__':
    main()
