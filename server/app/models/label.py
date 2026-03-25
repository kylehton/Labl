from pydantic import BaseModel
from typing import Literal, Optional


class Label(BaseModel):
    name: str
    type: Literal["system", "custom"]
    gmail_label_id: Optional[str] = None
    count: int = 0
    confidence: float = 0.0

    # Phase tracking — "bootstrap" uses a single medoid, "mature" uses k-means clusters
    phase: Literal["bootstrap", "mature"] = "bootstrap"

    # All confirmed email embeddings and texts for this label (needed for medoid/k-means/BM25)
    embeddings: list[list[float]] = []
    texts: list[str] = []

    # Phase 1: single medoid (most representative real embedding in the set)
    medoid: Optional[list[float]] = None

    # Phase 2: k-means cluster centers (replaces medoid once enough emails accumulate)
    clusters: Optional[list[list[float]]] = None
