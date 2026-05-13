"""DB-backed sessions with encrypted token storage. Opaque session_id in cookie."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, Request

from app.models.session import SessionDocument
from app.repositories.users import get_or_create_user
from config.crypto import decrypt, encrypt
from config.db import delete_one, find_one, get_collection, insert_one

import os
import logging

from dotenv import load_dotenv
load_dotenv()

COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "labl_session")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", 60 * 60 * 24 * 30))  # 30 days
SESSION_COLLECTION = "sessions"

# Secure cookie in production (HTTPS). Set to False for local dev.
SECURE_COOKIE = os.getenv("SECURE_COOKIE", "false").lower() == "true"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_session(data: dict) -> str:
    """Upsert user in users collection, create session with SessionDocument. Returns session_id."""
    session_id = uuid4().hex
    user_data = data.get("user", {})
    tokens = data.get("tokens", {})
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    user_id = user_data.get("user_id", "")
    email = user_data.get("email", "")
    name = user_data.get("name", "")

    await get_or_create_user(user_id=user_id, email=email, name=name)

    refresh_encrypted = encrypt(refresh_token) if refresh_token else None

    if refresh_encrypted:
        from app.repositories.users import update_user_document
        await update_user_document(user_id, {"refresh_token_encrypted": refresh_encrypted})
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=SESSION_TTL_SECONDS)

    session_doc = SessionDocument(
        session_id=session_id,
        user_id=user_id,
        access_token=access_token,
        refresh_token_encrypted=refresh_encrypted,
        created_at=now,
        expires_at=expires_at,
    )
    doc = session_doc.model_dump()

    try:
        await insert_one(SESSION_COLLECTION, doc)
    except Exception as e:
        logger.exception("Failed to create session")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {e}") from e

    return session_id


async def get_session(request: Request) -> dict | None:
    """Load session by session_id, then user from users collection. Returns session dict or None."""
    from app.repositories.users import get_user_by_id

    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        return None

    doc = await find_one(SESSION_COLLECTION, {"session_id": session_id})
    if not doc:
        return None

    expires_at = doc.get("expires_at")
    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            await delete_one(SESSION_COLLECTION, {"session_id": session_id})
            return None

    user_id = doc.get("user_id")
    user_doc = await get_user_by_id(user_id) if user_id else None
    if not user_doc:
        await delete_one(SESSION_COLLECTION, {"session_id": session_id})
        return None

    refresh_enc = doc.get("refresh_token_encrypted")
    refresh_token = decrypt(refresh_enc) if refresh_enc else None

    return {
        "user": user_doc.user.model_dump(),
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
