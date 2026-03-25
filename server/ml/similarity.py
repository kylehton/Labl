"""Hybrid similarity search: dense cosine (embedding) + sparse keyword (BM25)."""
import numpy as np

from app.models.label import Label

try:
    from rank_bm25 import BM25Okapi
    _BM25Okapi = BM25Okapi
except ImportError:
    _BM25Okapi = None  # type: ignore

# Minimum hybrid score to auto-label. Below this → suggest only.
LABEL_THRESHOLD = 0.85
# Minimum hybrid score to suggest at all. Below this → no action.
SUGGEST_THRESHOLD = 0.65
# Weight given to semantic (embedding) score vs BM25 keyword score.
# 0.0 = keyword only, 1.0 = semantic only.
HYBRID_ALPHA = 0.7


def _semantic_score(email_vector: list[float], label: Label) -> float:
    """Cosine similarity between email and label's representative vector(s).

    Mature phase: max cosine similarity across all k-means cluster centers.
    Bootstrap phase: cosine similarity against medoid (falls back to legacy centroid).
    """
    ev = np.array(email_vector, dtype=np.float32)

    if label.phase == "mature" and label.clusters:
        return max(
            float(np.dot(ev, np.array(c, dtype=np.float32)))
            for c in label.clusters
        )

    if label.medoid is None:
        return -1.0
    vec = label.medoid
    return float(np.dot(ev, np.array(vec, dtype=np.float32)))


def _bm25_scores(
    query_text: str,
    label_corpora: list[tuple[str, list[str]]],
) -> dict[str, float]:
    """Return cross-label normalised BM25 scores in [0, 1].

    For each label, BM25 scores the query against every email in its corpus and
    takes the maximum. Scores are then normalised by the max across all labels
    so they are on the same scale as cosine similarity.

    Returns an empty dict if rank-bm25 is not installed or no corpus texts exist.
    """
    if _BM25Okapi is None or not query_text:
        return {}

    query_tokens = query_text.lower().split()
    raw: dict[str, float] = {}

    for label_name, texts in label_corpora:
        if not texts:
            raw[label_name] = 0.0
            continue
        tokenized = [t.lower().split() for t in texts]
        bm25 = _BM25Okapi(tokenized)
        scores = bm25.get_scores(query_tokens)
        raw[label_name] = float(scores.max()) if len(scores) > 0 else 0.0

    max_raw = max(raw.values(), default=0.0)
    if max_raw <= 0:
        return {name: 0.0 for name in raw}
    return {name: score / max_raw for name, score in raw.items()}


def find_best_label(
    email_vector: list[float],
    labels: dict[str, Label],
    threshold: float = LABEL_THRESHOLD,
    suggest_threshold: float = SUGGEST_THRESHOLD,
    email_text: str = "",
) -> dict | None:
    """Find the highest-scoring label for an email using hybrid scoring.

    Hybrid score = HYBRID_ALPHA * cosine_similarity + (1 - HYBRID_ALPHA) * bm25_score

    Only considers labels that have been seeded (have medoid, centroid, or clusters).

    Returns:
        {
            "label_name": str,
            "score": float,
            "action": "label" | "suggest"
        }
        or None if no seeded labels exist or no label clears suggest_threshold.
    """
    candidates = {
        name: label
        for name, label in labels.items()
        if label.medoid is not None or label.clusters is not None
    }
    if not candidates:
        return None

    bm25 = _bm25_scores(
        email_text,
        [(name, label.texts) for name, label in candidates.items()],
    )

    best_name: str | None = None
    best_score = -1.0

    for name, label in candidates.items():
        sem = _semantic_score(email_vector, label)
        kw = bm25.get(name, 0.0)
        score = HYBRID_ALPHA * sem + (1.0 - HYBRID_ALPHA) * kw
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
