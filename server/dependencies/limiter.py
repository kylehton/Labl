from slowapi import Limiter
from config.session import COOKIE_NAME


def _user_key(request) -> str:
    """Rate limit key per user session. Falls back to client IP if no cookie."""
    return request.cookies.get(COOKIE_NAME) or request.client.host


limiter = Limiter(key_func=_user_key)
