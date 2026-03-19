from pydantic import BaseModel
from typing import Literal, Optional

class Label(BaseModel):
    name: str
    type: Literal["system", "custom"]
    gmail_label_id: Optional[str] = None  # Gmail's label ID, needed to apply labels via API
    centroid: Optional[list[float]] = None  # populated after seed emails are embedded
    count: int = 0
    confidence: float = 0.0
