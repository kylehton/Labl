import json
from uuid import uuid4
from fastapi import Request, HTTPException
from config.redis import redis_client
import os
import logging

COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "gsort_session")
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS", 60 * 60 * 24 * 30))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_session(data: dict) -> str:
    session_id = uuid4().hex
    key = f"session:{session_id}"

    try:
        redis_client.setex(
            key,
            SESSION_TTL,
            json.dumps(data),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {e}",
        )

    return session_id


def get_session(request: Request) -> dict | None:
    logger.info(f"Identifier: {COOKIE_NAME}")
    session_id = request.cookies.get(COOKIE_NAME)
    logger.info(f"Session ID: {session_id}")

    if not session_id:
        logger.info("no session found")
        return None

    key = f"session:{session_id}"
    data = redis_client.get(key)

    if not data:
        logger.info(f"no data found")
        return None

    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def delete_session(session_id: str):
    try:
        redis_client.delete(f"session:{session_id}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to log out user: {e}",
        )
    return
 
