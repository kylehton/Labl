from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from config.session import create_session, get_session, delete_session
from dependencies.session_auth import require_auth
from urllib.parse import urlencode
import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

router = APIRouter(prefix="/api/user/auth")

@router.get("/login")
def login():
    try:
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(GMAIL_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }
        google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        logger.info(f"Redirecting to Google OAuth URL: {google_auth_url}")
        return RedirectResponse(google_auth_url)
    except Exception as e:
        logger.error(f"Failed to generate login URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate login URL: {e}")

def exchange_code_for_tokens(code: str) -> dict:
    """Exchange the authorization code for access & refresh tokens."""
    try:
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        resp = requests.post("https://oauth2.googleapis.com/token", data=data)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

def fetch_google_user(access_token: str) -> dict:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers=headers)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Fetching user info failed: {e}")

@router.get("/login/callback")
def callback(request: Request, code: str = None, error: str = None):
    if error:
        logger.error(f"Google login error: {error}")
        raise HTTPException(status_code=400, detail=f"Google login failed: {error}")
    if not code:
        logger.error("No code returned from Google")
        raise HTTPException(status_code=400, detail="No code returned from Google")

    tokens = exchange_code_for_tokens(code)
    user = fetch_google_user(tokens.get("access_token"))

    session_id = create_session({
        "user": {
            "name": user['given_name'],
            "email": user['email'],
            "user_id": user['id']
        },
        "tokens": {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token")
        }
    })

    response = RedirectResponse("http://localhost:3000")
    response.set_cookie(
        key="gsort_session",
        value=session_id,
        httponly=True,
        secure=False,       # SET TO TRUE for prod.
        samesite="lax",    # 'none' REQUIRED for cross-origin
    )
    return response

@router.get("/status")
def status(request: Request):
    session = get_session(request)
    if not session:
        return {"authenticated": False}
    return {"authenticated": True, "user": session.get("user")}


@router.post("/logout")
def logout(request: Request):
    session_id = request.cookies.get("gsort_session")
    if session_id:
        delete_session(session_id)

    response = JSONResponse({"ok": True})
    response.delete_cookie("gsort_session")
    return response

