from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.env("GOOGLE_CLIENT_ID")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]

router = APIRouter(prefix='/api/google/auth')
@router.post("/login")
def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",   # REQUIRED for refresh token
        "prompt": "consent",        # REQUIRED to force refresh token
        "include_granted_scopes": "true",
    }

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode(params)
    )

    return RedirectResponse(url=google_auth_url, status_code=302)

