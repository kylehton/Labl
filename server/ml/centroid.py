"""Centroid computation and online EMA update for label vectors."""
import numpy as np

# Learning rate for exponential moving average updates.
# Lower = centroid adapts slowly (stable); higher = adapts quickly (responsive).
EMA_ALPHA = 0.1


def compute_centroid(embeddings: list[list[float]]) -> list[float]:
    """Compute mean centroid from seed embeddings, then L2-normalise.

    Called once when a user seeds a label with their initial k emails.
    The result is stored as label.centroid in MongoDB.
    """
    arr = np.array(embeddings, dtype=np.float32)
    centroid = arr.mean(axis=0)
    norm = np.linalg.norm(centroid)
    if norm > 0:
        centroid = centroid / norm
    return centroid.tolist()


def update_centroid_ema(
    current_centroid: list[float],
    new_embedding: list[float],
    alpha: float = EMA_ALPHA,
) -> list[float]:
    """Shift centroid toward a confirmed new example using EMA, then re-normalise.

    Called when a user confirms a suggested label (or when auto_label fires).
    Re-normalisation keeps the vector on the unit sphere so cosine similarity
    stays well-defined.
    """
    c = np.array(current_centroid, dtype=np.float32)
    e = np.array(new_embedding, dtype=np.float32)
    updated = (1.0 - alpha) * c + alpha * e
    norm = np.linalg.norm(updated)
    if norm > 0:
        updated = updated / norm
    return updated.tolist()
