"""Unit tests for Gmail API routes."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User, UserDocument
from dependencies.session_auth import require_auth

FAKE_SESSION = {
    "user": {"user_id": "u1", "email": "test@example.com", "name": "Test User"},
    "tokens": {"access_token": "fake-access-token", "refresh_token": "fake-refresh-token"},
}


@pytest.fixture(autouse=True)
def mock_mongo_startup():
    """Mock MongoDB connection so tests run without a real Mongo."""
    with (
        patch("app.main.connect_to_mongo", new_callable=AsyncMock),
        patch("app.main.ensure_session_indexes", new_callable=AsyncMock),
        patch("app.main.ensure_user_indexes", new_callable=AsyncMock),
        patch("app.main.load_model"),
    ):
        yield


@pytest.fixture(autouse=True)
def override_auth():
    """Bypass require_auth for all Gmail tests."""
    app.dependency_overrides[require_auth] = lambda: FAKE_SESSION
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture
def gmail_client_mock():
    """Return a mock GmailClient with async-capable methods."""
    mock = MagicMock()
    mock.list_messages_since = AsyncMock()
    mock.get_message_body = AsyncMock()
    mock.list_labels = AsyncMock()
    mock.create_label = AsyncMock()
    mock.apply_labels = AsyncMock()
    return mock


@pytest.fixture
def http_client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. get_messages — returns messages since last_checked, updates last_checked
# ---------------------------------------------------------------------------

def test_get_messages_returns_messages_since_last_checked(http_client, gmail_client_mock):
    """get_messages passes last_checked to the Gmail client and updates it on success."""
    last_checked = datetime(2024, 6, 1, tzinfo=UTC)
    user_doc = UserDocument(
        user=User(user_id="u1", email="test@example.com", name="Test"),
        last_checked=last_checked,
    )
    fake_messages = [
        {"id": "msg1", "subject": "Hello", "snippet": "Hi there"},
        {"id": "msg2", "subject": "Meeting", "snippet": "Tomorrow at 10"},
    ]
    gmail_client_mock.list_messages_since.return_value = fake_messages

    with (
        patch("app.api.gmail.get_user_by_id", new_callable=AsyncMock, return_value=user_doc),
        patch("app.api.gmail.update_user_document", new_callable=AsyncMock) as mock_update,
        patch("app.api.gmail._gmail_client", return_value=gmail_client_mock),
    ):
        resp = http_client.get("/api/gmail/messages")

    assert resp.status_code == 200
    data = resp.json()
    # Each message is enriched with a "pipeline" key by the route
    expected = [{**m, "pipeline": None} for m in fake_messages]
    assert data["messages"] == expected
    assert data["count"] == 2

    # Correct after= timestamp was forwarded to the Gmail client
    gmail_client_mock.list_messages_since.assert_awaited_once_with(after=last_checked)

    # last_checked was updated with a fresh UTC datetime
    mock_update.assert_awaited_once()
    update_call = mock_update.call_args
    assert update_call[0][0] == "u1"
    assert "last_checked" in update_call[0][1]
    assert isinstance(update_call[0][1]["last_checked"], datetime)


# ---------------------------------------------------------------------------
# 2. get_message_body — returns subject and plain-text body
# ---------------------------------------------------------------------------

def test_get_message_body_returns_subject_and_body(http_client, gmail_client_mock):
    """get_message_body returns the subject and plain-text body of a message."""
    gmail_client_mock.get_message_body.return_value = {
        "id": "abc123",
        "subject": "Weekly digest",
        "body": "Here are your updates for the week.",
    }

    with patch("app.api.gmail._gmail_client", return_value=gmail_client_mock):
        resp = http_client.get("/api/gmail/messages/abc123/body")

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "abc123"
    assert data["subject"] == "Weekly digest"
    assert data["body"] == "Here are your updates for the week."
    gmail_client_mock.get_message_body.assert_awaited_once_with("abc123")


# ---------------------------------------------------------------------------
# 3. get_labels — returns all Gmail labels for the user
# ---------------------------------------------------------------------------

def test_get_labels_returns_all_labels(http_client, gmail_client_mock):
    """get_labels returns the full list of Gmail labels for the authenticated user."""
    fake_labels = [
        {"id": "INBOX", "name": "INBOX", "type": "system"},
        {"id": "SENT", "name": "SENT", "type": "system"},
        {"id": "Label_1", "name": "Work", "type": "user"},
    ]
    gmail_client_mock.list_labels.return_value = fake_labels

    with patch("app.api.gmail._gmail_client", return_value=gmail_client_mock):
        resp = http_client.get("/api/gmail/labels")

    assert resp.status_code == 200
    data = resp.json()
    assert data["labels"] == fake_labels
    gmail_client_mock.list_labels.assert_awaited_once()


# ---------------------------------------------------------------------------
# 4. create_label — creates Gmail label and persists it in MongoDB
# ---------------------------------------------------------------------------

def test_create_label_creates_gmail_label_and_stores_in_mongodb(http_client, gmail_client_mock):
    """create_label creates a Gmail label and writes it to the user's label store."""
    user_doc = UserDocument(
        user=User(user_id="u1", email="test@example.com", name="Test"),
        labels={},
    )
    gmail_client_mock.create_label.return_value = {
        "id": "Label_42",
        "name": "Work",
        "type": "user",
    }

    with (
        patch("app.api.gmail.get_user_by_id", new_callable=AsyncMock, return_value=user_doc),
        patch("app.api.gmail.update_user_document", new_callable=AsyncMock) as mock_update,
        patch("app.api.gmail._gmail_client", return_value=gmail_client_mock),
    ):
        resp = http_client.post("/api/gmail/labels", json={"name": "Work"})

    assert resp.status_code == 200
    data = resp.json()

    # Gmail label returned in response
    assert data["label"]["id"] == "Label_42"
    assert data["label"]["name"] == "Work"

    # Stored label has correct fields
    assert data["stored"]["name"] == "Work"
    assert data["stored"]["gmail_label_id"] == "Label_42"
    assert data["stored"]["type"] == "custom"

    # Gmail API and MongoDB were each called once
    gmail_client_mock.create_label.assert_awaited_once_with("Work")
    mock_update.assert_awaited_once()
    update_call = mock_update.call_args
    assert update_call[0][0] == "u1"
    assert "labels.Work" in update_call[0][1]


# ---------------------------------------------------------------------------
# 5. apply_label — applies and removes labels on a Gmail message
# ---------------------------------------------------------------------------

def test_apply_label_applies_and_removes_labels(http_client, gmail_client_mock):
    """apply_label forwards add/remove label IDs to the Gmail client."""
    gmail_client_mock.apply_labels.return_value = None

    with patch("app.api.gmail._gmail_client", return_value=gmail_client_mock):
        resp = http_client.post(
            "/api/gmail/messages/abc123/label",
            json={"label_ids": ["Label_42"], "remove_label_ids": ["INBOX"]},
        )

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    gmail_client_mock.apply_labels.assert_awaited_once_with(
        "abc123",
        add_label_ids=["Label_42"],
        remove_label_ids=["INBOX"],
    )
