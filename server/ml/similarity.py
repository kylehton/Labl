"""Hybrid similarity search: dense cosine (embedding) + sparse keyword (BM25)."""
import re
from typing import Any
import numpy as np

from app.models.label import Label

try:
    from rank_bm25 import BM25Okapi
    _BM25Okapi = BM25Okapi
except ImportError:
    _BM25Okapi = None  # type: ignore

# Minimum hybrid score to auto-label. Below this → suggest only.
LABEL_THRESHOLD = 0.7
# Minimum hybrid score to suggest at all. Below this → no action.
SUGGEST_THRESHOLD = 0.6
# Weight given to semantic (embedding) score vs BM25 keyword score.
# 0.0 = keyword only, 1.0 = semantic only.
HYBRID_ALPHA = 0.7
# Minimum gap between the best and second-best label score to auto-label.
# Prevents ambiguous emails (multiple labels score similarly) from being auto-labeled.
LABEL_MARGIN = 0.12

# BM25 model cache: (label_name, corpus_len) → BM25Okapi instance.
# Corpus length is used as a cheap invalidation key — when new emails are
# confirmed the corpus grows, the key changes, and the stale entry is evicted.
_bm25_cache: dict[tuple[str, int], Any] = {}


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


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase word tokens, stripping punctuation."""
    return re.findall(r"\b\w+\b", text.lower())


def _get_bm25(label_name: str, texts: list[str]) -> Any:
    """Return a cached BM25Okapi model for this label corpus.

    Cache key is (label_name, corpus_len). When new emails are confirmed the
    corpus grows, the key changes, and the stale model is naturally evicted.
    """
    assert _BM25Okapi is not None
    key = (label_name, len(texts))
    if key not in _bm25_cache:
        _bm25_cache[key] = _BM25Okapi([_tokenize(t) for t in texts])
    return _bm25_cache[key]


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

    query_tokens = _tokenize(query_text)
    raw: dict[str, float] = {}

    for label_name, texts in label_corpora:
        if not texts:
            raw[label_name] = 0.0
            continue
        bm25 = _get_bm25(label_name, texts)
        scores = bm25.get_scores(query_tokens)
        raw[label_name] = float(scores.max())

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
    debug: bool = False,
) -> dict | None:
    """Find the highest-scoring label for an email using hybrid scoring.

    Hybrid score = HYBRID_ALPHA * cosine_similarity + (1 - HYBRID_ALPHA) * bm25_score

    Only considers labels that have been seeded (have medoid, centroid, or clusters).

    Returns:
        {
            "label_name": str,
            "score": float,
            "action": "label" | "suggest",
            "all_scores": dict (only when debug=True),
        }
        or None if no seeded labels exist or no label clears suggest_threshold.
        When debug=True, always returns the best match even if below suggest_threshold,
        with action="none".
    """
    candidates = {
        name: label
        for name, label in labels.items()
        if label.medoid is not None or label.clusters is not None
    }
    if not candidates:
        return None

    any_has_corpus = any(label.texts for label in candidates.values())
    bm25 = _bm25_scores(
        email_text,
        [(name, label.texts) for name, label in candidates.items()],
    ) if any_has_corpus else {}

    best_name: str | None = None
    best_score = -1.0
    all_scores: dict[str, float] = {}

    for name, label in candidates.items():
        sem = _semantic_score(email_vector, label)
        kw = bm25.get(name, 0.0)
        # If no label has a corpus (BM25 unavailable), use semantic score at full weight
        # rather than penalising it with a 0.3 dead-weight term.
        score = (
            sem if not any_has_corpus
            else HYBRID_ALPHA * sem + (1.0 - HYBRID_ALPHA) * kw
        )
        all_scores[name] = round(score, 4)
        if score > best_score:
            best_score = score
            best_name = name

    if best_name is None:
        return None

    if best_score < suggest_threshold:
        if debug:
            return {
                "label_name": best_name,
                "score": best_score,
                "action": "none",
                "all_scores": all_scores,
            }
        return None

    second_score = max(
        (s for n, s in all_scores.items() if n != best_name),
        default=0.0,
    )
    confident = best_score >= threshold and (best_score - second_score) >= LABEL_MARGIN
    result = {
        "label_name": best_name,
        "score": best_score,
        "action": "label" if confident else "suggest",
    }
    if debug:
        result["all_scores"] = all_scores
    return result
