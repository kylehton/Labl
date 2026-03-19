"""End-to-end labeling pipeline: embed → match → label or suggest."""
import logging

from app.models.label import Label
from ml.centroid import compute_centroid, update_centroid_ema
from ml.embeddings import embed
from ml.similarity import find_best_label, LABEL_THRESHOLD

logger = logging.getLogger(__name__)


def build_email_text(subject: str, body: str) -> str:
    """Combine subject and body into a single embedding input."""
    return f"{subject}\n\n{body}".strip()


def process_email(
    subject: str,
    body: str,
    labels: dict[str, Label],
    auto_label: bool = False,
    threshold: float = LABEL_THRESHOLD,
) -> dict | None:
    """Embed an email and determine whether to label or suggest.

    Args:
        subject:    Email subject line.
        body:       Plain-text email body.
        labels:     User's current label store (from UserDocument.labels).
        auto_label: If True, action can be "label"; if False, capped at "suggest".
        threshold:  Cosine similarity cutoff for auto-labeling.

    Returns:
        {
            "label_name": str,
            "gmail_label_id": str | None,
            "score": float,
            "action": "label" | "suggest",
            "vector": list[float],   # embedding of this email (for centroid update)
        }
        or None if no seeded labels exist yet.
    """
    text = build_email_text(subject, body)
    vector = embed([text])[0]

    result = find_best_label(vector, labels, threshold=threshold)
    if result is None:
        return None

    action = result["action"]
    # Respect the user's auto_label setting — downgrade to suggest if disabled
    if action == "label" and not auto_label:
        action = "suggest"

    label = labels[result["label_name"]]
    return {
        "label_name": result["label_name"],
        "gmail_label_id": label.gmail_label_id,
        "score": result["score"],
        "action": action,
        "vector": vector,
    }


def seed_label_centroid(seed_texts: list[tuple[str, str]]) -> list[float]:
    """Compute initial centroid from seed (subject, body) pairs.

    Called when a user selects k emails to define a label.
    The resulting centroid is stored in label.centroid in MongoDB.
    """
    texts = [build_email_text(subject, body) for subject, body in seed_texts]
    embeddings = embed(texts)
    return compute_centroid(embeddings)


def update_label_after_confirmation(
    current_centroid: list[float],
    confirmed_vector: list[float],
) -> list[float]:
    """Shift the label centroid toward a confirmed email via EMA.

    Called when the user accepts a suggested label (or auto_label fires).
    """
    return update_centroid_ema(current_centroid, confirmed_vector)
