from datetime import datetime
from pydantic import BaseModel, Field

class Session(BaseModel):
    session_id: str
    user: dict
    access_token: str
    refresh_token_encrypted: str | None = None
    expires_at: datetime

    class Config:
        populate_by_name = True
