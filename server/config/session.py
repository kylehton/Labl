import json
from uuid import uuid4
from fastapi import Request
from config.redis import redis_client
import os
from dotenv import load_dotenv

load_dotenv()

COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "gsort_session")
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS", 60*60*24*30))

def create_session(data: dict) -> str:
    session_id = uuid4().hex
    redis_client.setex(
        f"session:{session_id}",
        SESSION_TTL,
        json.dumps(data),
    )
    return session_id

def get_session(request: Request) -> dict | None:
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        return None

    data = redis_client.get(f"session:{session_id}")
    if not data:
        return None

    return json.loads(data)

def delete_session(session_id: str):
    redis_client.delete(f"session:{session_id}")
