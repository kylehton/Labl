from datetime import datetime, UTC
from typing import Literal, Optional
from pydantic import BaseModel, Field


class LabelRecord(BaseModel):
    record_id: str                              # str(ObjectId) — assigned on insert
    user_id: str
    task_id: str                                # Celery task that produced this record
    gmail_message_id: str
    subject: str                                # stored at creation so UI doesn't need a Gmail fetch
    label_name: str
    gmail_label_id: Optional[str]
    action: Literal["label", "suggest"]         # what the pipeline decided
    source: Literal["rule", "ml", "manual"]      # how the match was found
    score: Optional[float]                      # confidence score (None for rule matches)
    # embedding vector stored so confirm can update the model without re-fetching the email
    vector: Optional[list[float]] = None
    status: Literal["applied", "suggested", "confirmed", "rejected", "undone"]
    applied_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: Optional[datetime] = None
