"""DB-backed sessions with encrypted token storage. Opaque session_id in cookie."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, Request

from config.crypto import decrypt, encrypt
from config.db import delete_one, find_one, get_collection, insert_one

import os
import logging

COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "labl_session")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", 60 * 60 * 24 * 30))  # 30 days
SESSION_COLLECTION = "sessions"

# Secure cookie in production (HTTPS). Set to False for local dev.
SECURE_COOKIE = os.getenv("SECURE_COOKIE", "false").lower() == "true"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_session(data: dict) -> str:
    """Create a session in MongoDB. Encrypts refresh token. Returns session_id."""
    session_id = uuid4().hex
    user = data.get("user", {})
    tokens = data.get("tokens", {})
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    refresh_encrypted = encrypt(refresh_token) if refresh_token else None

    doc = {
        "session_id": session_id,
        "user": user,
        "access_token": access_token,
        "refresh_token_encrypted": refresh_encrypted,
        "created_at": datetime.now(UTC),
        "expires_at": datetime.now(UTC) + timedelta(seconds=SESSION_TTL_SECONDS),
    }

    try:
        await insert_one(SESSION_COLLECTION, doc)
    except Exception as e:
        logger.exception("Failed to create session")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {e}") from e

    return session_id


async def get_session(request: Request) -> dict | None:
    """Load session from DB by session_id in cookie. Returns session dict or None."""
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        return None

    doc = await find_one(SESSION_COLLECTION, {"session_id": session_id})
    if not doc:
        return None

    expires_at = doc.get("expires_at")
    if expires_at and expires_at < datetime.now(UTC):
        # Expired – delete and return None
        await delete_one(SESSION_COLLECTION, {"session_id": session_id})
        return None

    refresh_enc = doc.get("refresh_token_encrypted")
    refresh_token = decrypt(refresh_enc) if refresh_enc else None

    return {
        "user": doc.get("user", {}),
        "tokens": {
            "access_token": doc.get("access_token"),
            "refresh_token": refresh_token,
        },
    }


async def delete_session(session_id: str) -> None:
    """Remove session from DB."""
    try:
        await delete_one(SESSION_COLLECTION, {"session_id": session_id})
    except Exception as e:
        logger.exception("Failed to delete session")
        raise HTTPException(status_code=500, detail=f"Failed to log out: {e}") from e


async def ensure_session_indexes() -> None:
    """Create indexes for sessions collection: session_id (unique) and TTL on expires_at."""
    coll = get_collection(SESSION_COLLECTION)
    await coll.create_index("session_id", unique=True)
    await coll.create_index([("expires_at", 1)], expireAfterSeconds=0)
