from fastapi import Depends, HTTPException, Request
from config.session import get_session

def require_auth(request: Request):
    session = get_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session
