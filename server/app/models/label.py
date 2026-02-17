from pydantic import BaseModel
from typing import Literal, Optional

class Label(BaseModel):
    name: str
    type: Literal["system", "custom"]
    centroid: Optional[list[float]] = None
    count: int
    confidence: float
