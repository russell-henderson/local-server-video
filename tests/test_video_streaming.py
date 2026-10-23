"""
Tests for byte-range video streaming endpoint:
- Bounded Range requests (bytes=0-1023)
- Open-ended Range requests (bytes=100-)
- Suffix Range requests (bytes=-50 and bytes=-999999)
- Unsatisfiable Range requests (bytes=99999999- and bytes=500-200 -> HTTP 416)
- Malformed Range headers (bytes=invalid, malformed, multi-range -> HTTP 416)
- Early client disconnection / generator cleanup (file handle closed)
- Bounded memory / chunked delivery
- Full file requests without Range header
"""

from __future__ import annotations

import io
from pathlib import Path
import pytest
from backend.app import legacy_runtime


def _get_test_video_path(client) -> tuple[str, Path]:
    """Retrieve an existing video file path from the isolated test environment."""
    response = client.get("/admin/cache/status")
    assert response.status_code == 200
    payload = response.get_json() or {}
    recent = payload.get("recent_videos") or []
    if not recent:
        pytest.skip("No videos available in test environment")
    filename = recent[0]
    path = legacy_runtime.get_video_path(filename)
    return filename, path


def test_stream_video_no_range(client):
    """Requests without Range header return full file (HTTP 200)."""
    filename, path = _get_test_video_path(client)
    resp = client.get(f"/video/{filename}")
    assert resp.status_code == 200
    assert resp.content_type == "video/mp4"
    assert resp.headers.get("Accept-Ranges") == "bytes"
    assert len(resp.data) == path.stat().st_size


def test_stream_video_bounded_range(client):
    """Bounded range requests return 206 with exact slice."""
    filename, path = _get_test_video_path(client)
    size = path.stat().st_size
    assert size > 20, "Test file too small"

    resp = client.get(f"/video/{filename}", headers={"Range": "bytes=0-19"})
    assert resp.status_code == 206
    assert resp.headers["Content-Range"] == f"bytes 0-19/{size}"
    assert resp.headers["Content-Length"] == "20"
    assert resp.headers["Accept-Ranges"] == "bytes"
    assert resp.content_type == "video/mp4"
    assert len(resp.data) == 20

    with path.open("rb") as f:
        expected = f.read(20)
    assert resp.data == expected


def test_stream_video_open_ended_range(client):
    """Open-ended range (bytes=N-) streams from offset to EOF without full buffering."""
    filename, path = _get_test_video_path(client)
    size = path.stat().st_size
    offset = min(100, size // 2)

    resp = client.get(f"/video/{filename}", headers={"Range": f"bytes={offset}-"})
    assert resp.status_code == 206
    expected_length = size - offset
    assert resp.headers["Content-Range"] == f"bytes {offset}-{size - 1}/{size}"
    assert resp.headers["Content-Length"] == str(expected_length)
    assert len(resp.data) == expected_length

    with path.open("rb") as f:
        f.seek(offset)
        expected = f.read()
    assert resp.data == expected


def test_stream_video_suffix_range(client):
    """Suffix range (bytes=-N) requests the last N bytes."""
    filename, path = _get_test_video_path(client)
    size = path.stat().st_size
    suffix_len = min(50, size)

    resp = client.get(f"/video/{filename}", headers={"Range": f"bytes=-{suffix_len}"})
    assert resp.status_code == 206
    start = size - suffix_len
    assert resp.headers["Content-Range"] == f"bytes {start}-{size - 1}/{size}"
    assert resp.headers["Content-Length"] == str(suffix_len)
    assert len(resp.data) == suffix_len

    with path.open("rb") as f:
        f.seek(start)
        expected = f.read()
    assert resp.data == expected


def test_stream_video_suffix_larger_than_file(client):
    """Suffix range larger than file size clamps to entire file."""
    filename, path = _get_test_video_path(client)
    size = path.stat().st_size

    resp = client.get(f"/video/{filename}", headers={"Range": "bytes=-99999999"})
    assert resp.status_code == 206
    assert resp.headers["Content-Range"] == f"bytes 0-{size - 1}/{size}"
    assert resp.headers["Content-Length"] == str(size)
    assert len(resp.data) == size


def test_stream_video_unsatisfiable_range(client):
    """Out-of-range requests return HTTP 416 with Content-Range bytes */size."""
    filename, path = _get_test_video_path(client)
    size = path.stat().st_size

    # Range start beyond file size
    resp = client.get(f"/video/{filename}", headers={"Range": f"bytes={size + 5000}-"})
    assert resp.status_code == 416
    assert resp.headers["Content-Range"] == f"bytes */{size}"
    assert resp.headers["Accept-Ranges"] == "bytes"

    # Inverted range (start > end)
    resp_inverted = client.get(f"/video/{filename}", headers={"Range": "bytes=500-200"})
    assert resp_inverted.status_code == 416
    assert resp_inverted.headers["Content-Range"] == f"bytes */{size}"


def test_stream_video_malformed_range(client):
    """Malformed or unsupported multi-range headers return HTTP 416."""
    filename, path = _get_test_video_path(client)
    size = path.stat().st_size

    for bad_range in ["bytes=invalid", "malformed", "bytes=0-10, 20-30", "bytes=-0", "bytes="]:
        resp = client.get(f"/video/{filename}", headers={"Range": bad_range})
        assert resp.status_code == 416, f"Expected 416 for Range: {bad_range}"
        assert resp.headers["Content-Range"] == f"bytes */{size}"
        assert resp.headers["Accept-Ranges"] == "bytes"


def test_stream_video_not_found(client):
    """Missing video returns 404."""
    resp = client.get("/video/non_existent_video_12345.mp4")
    assert resp.status_code == 404


def test_stream_video_early_client_disconnect(client, monkeypatch):
    """When a client disconnects early, the underlying file handle is closed cleanly."""
    filename, path = _get_test_video_path(client)
    
    opened_handles = []
    original_open = Path.open

    def tracking_open(self, *args, **kwargs):
        fh = original_open(self, *args, **kwargs)
        if self == path:
            opened_handles.append(fh)
        return fh

    monkeypatch.setattr(Path, "open", tracking_open)

    resp = client.get(f"/video/{filename}", headers={"Range": "bytes=0-"})
    assert resp.status_code == 206
    assert len(opened_handles) == 1
    fh = opened_handles[0]
    assert not fh.closed, "File handle should be open during streaming"

    # Simulate client reading only one chunk and aborting/disconnecting
    iterator = resp.iter_encoded()
    _ = next(iterator)
    resp.close()

    assert fh.closed, "File handle must close when response is closed / client disconnects"


def test_stream_video_bounded_memory(client):
    """Verify that chunks yielded by the generator never exceed STREAMING_CHUNK_SIZE."""
    filename, path = _get_test_video_path(client)
    size = path.stat().st_size

    resp = client.get(f"/video/{filename}", headers={"Range": "bytes=0-"})
    assert resp.status_code == 206

    total_received = 0
    max_chunk_seen = 0
    for chunk in resp.iter_encoded():
        total_received += len(chunk)
        if len(chunk) > max_chunk_seen:
            max_chunk_seen = len(chunk)

    assert total_received == size
    assert max_chunk_seen <= legacy_runtime.STREAMING_CHUNK_SIZE
