from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.label import Label

class User(BaseModel):
    user_id: str
    email: EmailStr
    name: str


class UserDocument(BaseModel):
    user: User
    auto_apply: bool = False  # auto-apply high-confidence labels (vs always suggest)
    auto_sync: bool = False   # run labeling pipeline on a schedule automatically
    labels: dict[str, Label] = Field(default_factory=dict)
    last_checked: Optional[datetime] = None  # last time inbox was polled
    last_dashboard_visit: Optional[datetime] = None
    next_sync_at: Optional[datetime] = None  # earliest time the auto-sync scanner will re-enqueue
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

