"""
Shared pytest fixtures for the test suite.
"""
import pytest
from main import app as flask_app


@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()
