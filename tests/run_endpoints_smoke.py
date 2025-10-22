"""Smoke test for Flask endpoints (/view and /favorite)
Run with: python tests/run_endpoints_smoke.py
"""
import tempfile
from pathlib import Path
import sys
import json

# Ensure project root importable
sys.path.insert(0, str(Path(__file__).parents[1]))

from cache_manager import VideoCache
import main


def run():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        videos_dir = td_path / "videos"
        videos_dir.mkdir()
        sample = videos_dir / "sample.mp4"
        sample.write_text("fake")

        # Create a fresh JSON-backed cache and point main to use it
        test_cache = VideoCache(cache_ttl=1, use_database=False)
        test_cache.video_dir = str(videos_dir)
        test_cache.ratings_file = str(td_path / "ratings.json")
        test_cache.views_file = str(td_path / "views.json")
        test_cache.tags_file = str(td_path / "tags.json")
        test_cache.favorites_file = str(td_path / "favorites.json")

        # Force refresh
        test_cache._last_refresh = {k: 0 for k in test_cache._last_refresh}

        # Patch main's cache and VIDEO_DIR
        main.cache = test_cache
        main.VIDEO_DIR = Path(test_cache.video_dir)

        client = main.app.test_client()

        # Check initial favorites list
        resp = client.get('/favorites')
        assert resp.status_code == 200

        # POST a view
        r = client.post('/view', json={'filename': 'sample.mp4'})
        assert r.status_code == 200
        data = r.get_json()
        print('/view response:', data)
        assert data.get('success') is True
        assert isinstance(data.get('views'), int)

        # POST favorite toggle
        r2 = client.post('/favorite', json={'filename': 'sample.mp4'})
        assert r2.status_code == 200
        data2 = r2.get_json()
        print('/favorite response:', data2)
        assert data2.get('success') is True
        assert 'sample.mp4' in data2.get('favorites', [])

        # Toggle favorite again (remove)
        r3 = client.post('/favorite', json={'filename': 'sample.mp4'})
        data3 = r3.get_json()
        print('/favorite toggle off response:', data3)
        assert 'sample.mp4' not in data3.get('favorites', [])

        print('Endpoint smoke checks passed')


if __name__ == '__main__':
    try:
        run()
        print('ENDPOINT SMOKE TEST: PASS')
    except AssertionError as e:
        print('ENDPOINT SMOKE TEST: FAIL:', e)
        raise
    except Exception as ex:
        print('ENDPOINT SMOKE TEST: ERROR:', ex)
        raise
