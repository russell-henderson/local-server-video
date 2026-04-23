"""
Regression suite: broader compatibility checks for ratings/favorites/tags/admin/gallery.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from flask import render_template

from backend.app.api.ratings import is_lan_origin
from backend.app.factory import create_app
from backend.app import legacy_runtime
from backend.app.core.rate_limiter import RateLimiter
from backend.services.ratings_service import RatingsService


def _get_any_video(client):
    response = client.get("/admin/cache/status")
    if response.status_code != 200:
        return None
    payload = response.get_json() or {}
    recent = payload.get("recent_videos") or []
    return recent[0] if recent else None


def test_ratings_api_roundtrip(client):
    filename = _get_any_video(client)
    if not filename:
        pytest.skip("No videos available for ratings API regression test")

    media_hash = RatingsService.get_media_hash(filename)
    write = client.post(f"/api/ratings/{media_hash}", json={"value": 5})
    assert write.status_code in (201, 429)

    if write.status_code == 201:
        read = client.get(f"/api/ratings/{media_hash}")
        assert read.status_code == 200
        payload = read.get_json() or {}
        assert "average" in payload
        assert "count" in payload


def test_tags_db_authoritative_read_write_path(client):
    filename = _get_any_video(client)
    if not filename:
        pytest.skip("No videos available for tags regression test")

    add = client.post("/tag", json={"filename": filename, "tag": "regression-tag"})
    assert add.status_code == 200
    assert (add.get_json() or {}).get("success") is True

    list_for_video = client.get("/api/tags/video", query_string={"filename": filename})
    assert list_for_video.status_code == 200
    tags_payload = list_for_video.get_json() or {}
    assert "tags" in tags_payload

    popular = client.get("/api/tags/popular")
    assert popular.status_code == 200

    tag_page = client.get("/tag/regression-tag")
    assert tag_page.status_code == 200
    assert b'class="rating"' in tag_page.data
    assert b"favorite-btn" in tag_page.data
    assert b"/static/js/ratings.js" in tag_page.data
    assert b"/static/js/rating.js" not in tag_page.data


def test_favorites_page_rating_widget_present(client):
    page = client.get("/favorites")
    assert page.status_code == 200
    assert b'class="rating"' in page.data
    assert b"favorite-btn" in page.data
    assert b"/static/js/ratings.js" in page.data
    assert b"/static/js/rating.js" not in page.data


def test_watch_page_main_and_related_have_metadata_controls(client):
    filename = _get_any_video(client)
    if not filename:
        pytest.skip("No videos available for watch metadata-controls regression test")

    page = client.get(f"/watch/{filename}")
    assert page.status_code == 200
    html = page.data
    rating_count = html.count(b'class="rating"')
    favorite_count = html.count(b"favorite-btn")
    assert rating_count >= 1
    assert favorite_count >= 1
    if b"No related videos found." not in html:
        assert rating_count >= 2
        assert favorite_count >= 2
    assert b"/static/js/ratings.js" in html
    assert b"/static/js/rating.js" not in html


def test_gallery_baseline_routes(client):
    assert client.get("/gallery").status_code == 200
    assert client.get("/api/gallery").status_code == 200


def test_admin_cache_contract_remains_stable(client):
    status_response = client.get("/admin/cache/status")
    assert status_response.status_code == 200
    payload = status_response.get_json() or {}
    assert "video_count" in payload

    refresh_response = client.post("/admin/cache/refresh")
    assert refresh_response.status_code == 200


def test_ratings_unknown_hash_returns_404(client):
    response = client.get("/api/ratings/unknown_hash_for_regression")
    assert response.status_code == 404


def test_ratings_cors_preflight_lan_origin(client):
    response = client.options(
        "/api/ratings/testhash123",
        headers={"Origin": "http://192.168.1.10:5000"},
    )
    assert response.status_code == 204
    assert response.headers.get("Access-Control-Allow-Origin") == "http://192.168.1.10:5000"


def test_lan_origin_detection_invariants():
    assert is_lan_origin("http://localhost:5000")
    assert is_lan_origin("http://127.0.0.1:5000")
    assert is_lan_origin("http://192.168.1.10:8080")
    assert not is_lan_origin("http://example.com")


def test_rate_limiter_unit_window_behavior():
    limiter = RateLimiter(max_requests=2, window_seconds=5)
    allowed_1, info_1 = limiter.is_allowed("10.0.0.1")
    allowed_2, info_2 = limiter.is_allowed("10.0.0.1")
    allowed_3, info_3 = limiter.is_allowed("10.0.0.1")

    assert allowed_1 is True
    assert allowed_2 is True
    assert info_2["remaining"] == 0
    assert allowed_3 is False
    assert info_3["remaining"] == 0
    assert info_3["reset_in"] >= 1


def test_admin_metadata_prune_contract(client):
    response = client.post("/admin/metadata/prune")
    assert response.status_code == 200
    payload = response.get_json() or {}
    assert payload.get("success") is True
    for key in (
        "ratings_removed",
        "views_removed",
        "favorites_removed",
        "tag_entries_removed",
        "tag_values_removed",
    ):
        assert key in payload


def test_required_templates_use_shared_tag_chips_partial():
    template_paths = [
        "templates/index.html",
        "templates/watch.html",
        "templates/favorites.html",
        "templates/tag_videos.html",
        "templates/popular.html",
        "templates/best_of.html",
    ]
    repo_root = Path(__file__).resolve().parents[1]
    for rel_path in template_paths:
        content = (repo_root / rel_path).read_text(encoding="utf-8")
        assert "partials/video_tag_chips.html" in content


def test_tag_chip_overflow_on_related_cards(client):
    filename = _get_any_video(client)
    if not filename:
        pytest.skip("No videos available for tag chip regression test")

    base = f"chipreg{uuid4().hex[:8]}"
    tag_names = [f"{base}a", f"{base}b", f"{base}c", f"{base}d"]

    for tag_name in tag_names:
        add = client.post("/tag", json={"filename": filename, "tag": tag_name})
        assert add.status_code == 200
        assert (add.get_json() or {}).get("success") is True

    tag_page = client.get(f"/tag/{tag_names[0]}")
    assert tag_page.status_code == 200

    watch = client.get(f"/watch/{filename}")
    assert watch.status_code == 200
    watch_html = watch.data.decode("utf-8", errors="ignore")
    assert 'data-tag-scope="card"' in watch_html


def test_watch_main_uses_single_editable_tag_surface(client):
    filename = _get_any_video(client)
    if not filename:
        pytest.skip("No videos available for watch tag-surface regression test")

    watch = client.get(f"/watch/{filename}")
    assert watch.status_code == 200
    html = watch.data.decode("utf-8", errors="ignore")
    assert 'id="existing-tags"' in html
    assert 'id="new-tag"' in html
    assert 'data-tag-scope="main"' in html
    assert html.find('data-tag-scope="main"') < html.find("video-container")


def test_watch_main_no_chip_row_when_video_has_no_tags(client):
    response = client.get("/admin/cache/status")
    if response.status_code != 200:
        pytest.skip("No cache status available for no-tags watch test")

    recent = (response.get_json() or {}).get("recent_videos") or []
    if not recent:
        pytest.skip("No recent videos available for no-tags watch test")

    no_tag_filename = None
    for name in recent[:25]:
        tags_resp = client.get("/api/tags/video", query_string={"filename": name})
        if tags_resp.status_code != 200:
            continue
        if not ((tags_resp.get_json() or {}).get("tags") or []):
            no_tag_filename = name
            break

    if not no_tag_filename:
        pytest.skip("No recent video without tags found")

    watch = client.get(f"/watch/{no_tag_filename}")
    assert watch.status_code == 200
    html = watch.data.decode("utf-8", errors="ignore")
    assert 'data-tag-scope="main"' not in html


def test_video_tag_chips_partial_limits_to_three_with_overflow(app):
    tags = ["#alpha", "#beta", "#gamma", "#delta"]
    with app.test_request_context("/"):
        html = render_template(
            "partials/video_tag_chips.html",
            tags=tags,
            max_tags=3,
            show_overflow_count=True,
            tag_scope="card",
        )
    assert 'href="/tag/alpha"' in html
    assert 'href="/tag/beta"' in html
    assert 'href="/tag/gamma"' in html
    assert 'href="/tag/delta"' not in html
    assert "+1" in html


def test_video_tag_chips_partial_renders_all_when_unlimited(app):
    tags = ["#alpha", "#beta", "#gamma", "#delta"]
    with app.test_request_context("/"):
        html = render_template(
            "partials/video_tag_chips.html",
            tags=tags,
            max_tags=None,
            show_overflow_count=False,
            tag_scope="main",
        )
    assert 'href="/tag/alpha"' in html
    assert 'href="/tag/beta"' in html
    assert 'href="/tag/gamma"' in html
    assert 'href="/tag/delta"' in html
    assert "+1" not in html


def _search_video(filename: str, tags: list[str] | None = None, title: str | None = None) -> dict:
    return {
        "filename": filename,
        "title": title,
        "tags": tags or [],
        "rating": 4,
        "views": 42,
        "media_hash": filename,
    }


def _search_client_with_videos(monkeypatch, videos: list[dict]):
    app = create_app()
    app.config.update(TESTING=True)
    monkeypatch.setattr(legacy_runtime.cache, "use_database", True)
    monkeypatch.setattr(legacy_runtime.cache, "db", object())
    monkeypatch.setattr(legacy_runtime.cache, "get_favorites", lambda: [])
    monkeypatch.setattr(
        legacy_runtime.cache,
        "get_all_video_data",
        lambda sort_by="date", reverse=True, limit=None, offset=0: videos,
    )
    monkeypatch.setattr(legacy_runtime, "ensure_thumbnails_exist", lambda _: None)
    return app.test_client()


def test_search_empty_query_helper_state(monkeypatch):
    client = _search_client_with_videos(monkeypatch, [_search_video("one.mp4", tags=["#tag"])])
    response = client.get("/search?q=")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "0 matches" in body
    assert "Start searching from the header." in body


def test_search_display_title_fallback_and_filename_match(monkeypatch):
    videos = [
        _search_video("blonde-outdoor.mp4", tags=["#outside"]),
        _search_video("summer_trip.mp4", tags=["#vacation"]),
        _search_video("other.mp4"),
    ]
    client = _search_client_with_videos(monkeypatch, videos)

    response_one = client.get("/search?q=blonde")
    assert response_one.status_code == 200
    assert "blonde-outdoor.mp4" in response_one.get_data(as_text=True)

    response_two = client.get("/search?q=summer")
    assert response_two.status_code == 200
    body_two = response_two.get_data(as_text=True)
    assert "summer_trip.mp4" in body_two
    assert "other.mp4" not in body_two


def test_search_tag_case_and_multi_token_and(monkeypatch):
    videos = [
        _search_video("scene_a.mp4", tags=["#blonde", "#outdoor"]),
        _search_video("scene_b.mp4", tags=["#blonde", "#studio"]),
        _search_video("scene_c.mp4", tags=["#outdoor"]),
        _search_video("CaseMixed.mp4", tags=["#OutDoor"]),
    ]
    client = _search_client_with_videos(monkeypatch, videos)

    tag_only = client.get("/search?q=outdoor")
    assert tag_only.status_code == 200
    assert "scene_a.mp4" in tag_only.get_data(as_text=True)

    case_insensitive = client.get("/search?q=casemixed outdoor")
    assert case_insensitive.status_code == 200
    assert "CaseMixed.mp4" in case_insensitive.get_data(as_text=True)

    and_query = client.get("/search?q=blonde outdoor")
    assert and_query.status_code == 200
    body = and_query.get_data(as_text=True)
    assert "scene_a.mp4" in body
    assert "scene_b.mp4" not in body
    assert "scene_c.mp4" not in body


def test_search_result_cards_keep_shared_contract(monkeypatch):
    client = _search_client_with_videos(monkeypatch, [_search_video("contract.mp4", tags=["#chip"])])
    response = client.get("/search?q=contract")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'class="video-tag-chips' in body
    assert 'class="video-metadata-row' in body
