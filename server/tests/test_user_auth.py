"""Unit tests for auth endpoints (status, logout) with mocked session layer."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

# TestClient is sync; FastAPI handles async routes
client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_mongo_startup():
    """Mock MongoDB connection so tests run without a real Mongo."""
    with (
        patch("app.main.connect_to_mongo", new_callable=AsyncMock),
        patch("app.main.ensure_session_indexes", new_callable=AsyncMock),
        patch("app.main.ensure_user_indexes", new_callable=AsyncMock),
    ):
        yield


def test_status_unauthenticated():
    """GET /api/user/auth/status returns authenticated=False when no session."""
    with patch("app.api.auth.get_session", new_callable=AsyncMock, return_value=None):
        resp = client.get("/api/user/auth/status")
    assert resp.status_code == 200
    assert resp.json() == {"authenticated": False}


def test_status_authenticated():
    """GET /api/user/auth/status returns user when session exists."""
    session_data = {
        "user": {"name": "Jane", "email": "jane@example.com", "user_id": "456"},
        "tokens": {},
    }
    with patch("config.session.get_session", new_callable=AsyncMock, return_value=session_data):
        resp = client.get("/api/user/auth/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["authenticated"] is True
    assert data["user"] == session_data["user"]


def test_logout_clears_session():
    """POST /api/user/auth/logout calls delete_session and clears cookie."""
    with patch("app.api.auth.delete_session", new_callable=AsyncMock) as mock_delete:
        resp = client.post(
            "/api/user/auth/logout",
            headers={"Cookie": "labl_session=some-session-id"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    mock_delete.assert_awaited_once_with("some-session-id")
    set_cookies = [h for h in resp.headers.get_list("set-cookie") if "labl_session" in h.lower()]
    assert len(set_cookies) >= 1


def test_logout_without_cookie_succeeds():
    """POST /api/user/auth/logout without cookie still returns 200."""
    client.cookies.delete("labl_session")
    with patch("app.api.auth.delete_session", new_callable=AsyncMock) as mock_delete:
        resp = client.post("/api/user/auth/logout")
    assert resp.status_code == 200
    mock_delete.assert_not_awaited()
