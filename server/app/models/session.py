from datetime import datetime
from pydantic import BaseModel


class SessionDocument(BaseModel):
    session_id: str
    user_id: str
    access_token: str | None
    refresh_token_encrypted: str | None
    created_at: datetime
    expires_at: datetime
