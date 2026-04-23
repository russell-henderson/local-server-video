"""
Smoke suite: fast contract checks for core runtime routes and basic behaviors.
"""

from __future__ import annotations

import pytest


def _get_any_video(client):
    response = client.get("/admin/cache/status")
    if response.status_code != 200:
        return None
    payload = response.get_json() or {}
    recent = payload.get("recent_videos") or []
    return recent[0] if recent else None


def test_app_boot_and_home(client):
    assert client.get("/ping").status_code == 200
    assert client.get("/").status_code == 200


def test_public_watch_and_video_routes(client):
    filename = _get_any_video(client)
    if not filename:
        pytest.skip("No videos available for watch/stream smoke test")

    assert client.get(f"/watch/{filename}").status_code == 200
    assert client.get(f"/video/{filename}").status_code in (200, 206)


def test_admin_cache_routes(client):
    assert client.get("/admin/cache/status").status_code == 200
    assert client.post("/admin/cache/refresh").status_code == 200


def test_ratings_legacy_and_api_contract(client):
    filename = _get_any_video(client)
    if not filename:
        pytest.skip("No videos available for ratings smoke test")

    legacy = client.post("/rate", json={"filename": filename, "rating": 4})
    assert legacy.status_code == 200
    assert (legacy.get_json() or {}).get("success") is True


def test_favorites_toggle_and_page(client):
    filename = _get_any_video(client)
    if not filename:
        pytest.skip("No videos available for favorites smoke test")

    toggle = client.post("/favorite", json={"filename": filename})
    assert toggle.status_code == 200
    assert (toggle.get_json() or {}).get("success") is True
    assert client.get("/favorites").status_code == 200


def test_rating_widget_presence_on_core_pages(client):
    home = client.get("/")
    assert home.status_code == 200
    assert b'class="rating"' in home.data
    assert b"favorite-btn" in home.data
    assert b"/static/js/ratings.js" in home.data
    assert b"/static/js/rating.js" not in home.data

    filename = _get_any_video(client)
    if not filename:
        pytest.skip("No videos available for watch rating-widget test")

    watch = client.get(f"/watch/{filename}")
    assert watch.status_code == 200
    assert b'class="rating"' in watch.data
    assert b"favorite-btn" in watch.data
    assert b"/static/js/ratings.js" in watch.data
    assert b"/static/js/rating.js" not in watch.data


def test_random_and_gallery_baseline(client):
    random_response = client.get("/random", follow_redirects=False)
    assert random_response.status_code in (200, 302, 303, 307, 308)

    gallery_api = client.get("/api/gallery")
    assert gallery_api.status_code == 200
    payload = gallery_api.get_json() or {}
    assert "images" in payload


def test_search_route_and_header_form_exist(client):
    response = client.get("/search?q=")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'action="/search"' in body
    assert 'name="q"' in body
