"""
Shared pytest fixtures for the test suite.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

# Isolate metadata SQLite from repo `data/video_metadata.db` (developer runtime DB can be
# corrupt or unsuitable for CI). VideoDatabase() resolves path via LVS_DB_PATH; set it
# before importing `main`, which constructs the global cache and ratings DB handles.
_PYTEST_METADATA_DIR = Path(tempfile.mkdtemp(prefix="lvs-pytest-metadata-"))
_ORIGINAL_CWD = Path.cwd()
from scripts.test_library import seed_library
seed_library(_PYTEST_METADATA_DIR, count=4)
os.chdir(_PYTEST_METADATA_DIR)
_TEST_DB_PATH = _PYTEST_METADATA_DIR / "video_metadata.db"
os.environ["LVS_DB_PATH"] = str(_TEST_DB_PATH)
assert Path(os.environ["LVS_DB_PATH"]).resolve() == _TEST_DB_PATH.resolve()

from main import app as flask_app
os.chdir(_ORIGINAL_CWD)


@pytest.fixture(autouse=True)
def isolated_working_directory(monkeypatch):
    monkeypatch.chdir(_PYTEST_METADATA_DIR)


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    from backend.app import legacy_runtime
    legacy_runtime.gallery_index.close()
    os.chdir(_ORIGINAL_CWD)
    shutil.rmtree(_PYTEST_METADATA_DIR, ignore_errors=True)


@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()
