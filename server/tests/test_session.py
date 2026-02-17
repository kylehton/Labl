"""Unit tests for session logic (create, get, delete) with mocked DB."""
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config.session import (
    COOKIE_NAME,
    SESSION_COLLECTION,
    create_session,
    delete_session,
    get_session,
)


# In-memory store: session_id -> session doc, "user:{user_id}" -> user doc
_fake_store: dict = {}


async def _mock_insert_one(collection: str, document: dict):
    _fake_store[document["session_id"]] = document
    return document["session_id"]


async def _mock_find_one(collection: str, query: dict):
    if "session_id" in query:
        return _fake_store.get(query["session_id"])
    if "user_id" in query:
        return _fake_store.get("user:" + query["user_id"])
    return None


async def _mock_delete_one(collection: str, query: dict):
    if "session_id" in query:
        sid = query["session_id"]
        if sid in _fake_store:
            del _fake_store[sid]
    return 1


async def _mock_get_or_create_user(user_id: str, email: str, name: str):
    from app.models.user import User, UserDocument
    doc = UserDocument(
        user=User(user_id=user_id, email=email, name=name),
        auto_label=False,
        labels={},
    )
    payload = doc.model_dump()
    payload["user_id"] = user_id
    _fake_store["user:" + user_id] = payload
    return doc


async def _mock_get_user_by_id(user_id: str):
    from app.models.user import UserDocument
    raw = _fake_store.get("user:" + user_id)
    if not raw:
        return None
    return UserDocument.model_validate({k: v for k, v in raw.items() if k != "_id"})


@pytest.fixture(autouse=True)
def reset_fake_store():
    """Clear fake store before each test."""
    _fake_store.clear()
    yield
    _fake_store.clear()


@pytest.fixture
def mock_db():
    """Patch session DB calls and users repo (UserRepository uses get_db, so mock get_or_create_user/get_user_by_id)."""
    with (
        patch("config.session.insert_one", side_effect=_mock_insert_one),
        patch("config.session.find_one", side_effect=_mock_find_one),
        patch("config.session.delete_one", side_effect=_mock_delete_one),
        patch("config.session.get_or_create_user", side_effect=_mock_get_or_create_user),
    ):
        yield


@pytest.mark.asyncio
async def test_create_session_returns_session_id(mock_db):
    """create_session returns a non-empty session_id."""
    data = {
        "user": {"name": "Test", "email": "test@example.com", "user_id": "123"},
        "tokens": {"access_token": "at", "refresh_token": "rt"},
    }
    session_id = await create_session(data)
    assert session_id
    assert len(session_id) == 32  # uuid4.hex
    assert session_id in _fake_store


@pytest.mark.asyncio
async def test_create_session_stores_user_and_tokens(mock_db):
    """create_session stores user_id and encrypted refresh token."""
    data = {
        "user": {"name": "Alice", "email": "alice@example.com", "user_id": "u1"},
        "tokens": {"access_token": "access_abc", "refresh_token": "refresh_xyz"},
    }
    session_id = await create_session(data)
    doc = _fake_store[session_id]
    assert doc["user_id"] == "u1"
    assert doc["access_token"] == "access_abc"
    assert doc["refresh_token_encrypted"]  # encrypted, not plaintext
    assert doc["refresh_token_encrypted"] != "refresh_xyz"
    assert "expires_at" in doc
    assert "user:u1" in _fake_store


@pytest.mark.asyncio
async def test_create_session_without_refresh_token(mock_db):
    """create_session handles missing refresh_token (e.g. first-time OAuth)."""
    data = {
        "user": {"name": "Bob", "email": "bob@example.com", "user_id": "u2"},
        "tokens": {"access_token": "at_only", "refresh_token": None},
    }
    session_id = await create_session(data)
    doc = _fake_store[session_id]
    assert doc["refresh_token_encrypted"] is None
    assert doc["user_id"] == "u2"


@pytest.mark.asyncio
async def test_get_session_returns_none_when_no_cookie(mock_db):
    """get_session returns None when cookie is missing."""
    request = MagicMock()
    request.cookies.get.return_value = None
    result = await get_session(request)
    assert result is None


@pytest.mark.asyncio
async def test_get_session_returns_none_when_unknown_session(mock_db):
    """get_session returns None when session_id is not in DB."""
    request = MagicMock()
    request.cookies.get.return_value = "unknown-session-id"
    result = await get_session(request)
    assert result is None


@pytest.mark.asyncio
async def test_get_session_returns_user_and_tokens(mock_db):
    """get_session returns user and decrypted tokens for valid session."""
    data = {
        "user": {"name": "Carol", "email": "carol@example.com", "user_id": "u3"},
        "tokens": {"access_token": "at", "refresh_token": "rt"},
    }
    session_id = await create_session(data)
    request = MagicMock()
    request.cookies.get.return_value = session_id

    result = await get_session(request)
    assert result is not None
    assert result["user"] == data["user"]
    assert result["tokens"]["access_token"] == "at"
    assert result["tokens"]["refresh_token"] == "rt"


@pytest.mark.asyncio
async def test_get_session_returns_none_when_expired(mock_db):
    """get_session returns None and deletes session when expired."""
    data = {
        "user": {"name": "Expired", "email": "e@ex.com", "user_id": "u4"},
        "tokens": {"access_token": "at", "refresh_token": "rt"},
    }
    session_id = await create_session(data)
    doc = _fake_store[session_id]
    doc["expires_at"] = datetime.now(UTC) - timedelta(seconds=1)
    _fake_store[session_id] = doc

    request = MagicMock()
    request.cookies.get.return_value = session_id
    result = await get_session(request)
    assert result is None
    assert session_id not in _fake_store


@pytest.mark.asyncio
async def test_delete_session_removes_from_db(mock_db):
    """delete_session removes the session document."""
    data = {
        "user": {"user_id": "u0", "email": "u@ex.com", "name": "U"},
        "tokens": {"access_token": "at", "refresh_token": "rt"},
    }
    session_id = await create_session(data)
    assert session_id in _fake_store

    await delete_session(session_id)
    assert session_id not in _fake_store


@pytest.mark.asyncio
async def test_delete_session_unknown_id_does_not_raise(mock_db):
    """delete_session on unknown id does not raise."""
    await delete_session("nonexistent-id")
    # Should not raise
