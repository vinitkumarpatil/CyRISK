"""Pytest fixtures: an isolated, seeded API client over a throwaway SQLite DB.

The DATABASE_URL is redirected to a temp file BEFORE the app is imported, so
tests never touch the developer's cyberrisk.db. The TestClient is used as a
context manager so FastAPI's lifespan (init_db + first-run demo seed) runs.
"""
import os
import sys
import tempfile

# Make `import app...` work regardless of the directory pytest is invoked from.
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Redirect the database to an isolated temp file before importing the app.
_TMP = tempfile.mkdtemp(prefix="cyberrisk_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ.setdefault("SECRET_KEY", "test-only-secret-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.main as main_module  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """Session-wide TestClient; the `with` block triggers startup seeding."""
    with TestClient(main_module.app) as c:
        yield c


def _login(client, username: str, password: str) -> dict:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="session")
def analyst_headers(client):
    return _login(client, "analyst", "analyst123")


@pytest.fixture(scope="session")
def ciso_headers(client):
    return _login(client, "ciso", "ciso123")


@pytest.fixture(scope="session")
def exec_headers(client):
    return _login(client, "exec", "exec123")
