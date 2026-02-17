from datetime import datetime, UTC
from pydantic import BaseModel, EmailStr, Field
from app.models.label import Label

class User(BaseModel):
    user_id: str
    email: EmailStr
    name: str


class UserDocument(BaseModel):
    user: User
    auto_label: bool = False # assume suggestion only unless specified
    labels: dict[str, Label] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

