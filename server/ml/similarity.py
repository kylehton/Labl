"""Cosine similarity search against a user's label centroids."""
import numpy as np

from app.models.label import Label

# Minimum similarity score to auto-label. Below this → suggest only.
LABEL_THRESHOLD = 0.85
# Minimum similarity score to suggest at all. Below this → no action.
SUGGEST_THRESHOLD = 0.65


def find_best_label(
    email_vector: list[float],
    labels: dict[str, Label],
    threshold: float = LABEL_THRESHOLD,
    suggest_threshold: float = SUGGEST_THRESHOLD,
) -> dict | None:
    """Find the highest-scoring label for an email vector.

    Only considers labels that have a centroid (i.e. have been seeded).

    Returns:
        {
            "label_name": str,
            "score": float,       # cosine similarity (0–1, higher = more similar)
            "action": "label" | "suggest"
        }
        or None if no labels have centroids yet.
    """
    candidates = {
        name: label
        for name, label in labels.items()
        if label.centroid is not None
    }
    if not candidates:
        return None

    ev = np.array(email_vector, dtype=np.float32)
    best_name: str | None = None
    best_score = -1.0

    for name, label in candidates.items():
        cv = np.array(label.centroid, dtype=np.float32)
        # Both vectors are L2-normalised → dot product == cosine similarity
        score = float(np.dot(ev, cv))
        if score > best_score:
            best_score = score
            best_name = name

    if best_name is None or best_score < suggest_threshold:
        return None

    return {
        "label_name": best_name,
        "score": best_score,
        "action": "label" if best_score >= threshold else "suggest",
    }
