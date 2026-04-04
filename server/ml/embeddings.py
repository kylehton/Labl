"""Local text embeddings via BAAI/bge-small-en-v1.5 (sentence-transformers).

The model is loaded once at server startup via load_model() and held in memory.
All embeddings are L2-normalised so that dot product == cosine similarity.
"""
import logging

logger = logging.getLogger(__name__)

MODEL_NAME = "BAAI/bge-base-en-v1.5"

try:
    from sentence_transformers import SentenceTransformer
    _SentenceTransformer = SentenceTransformer
except ImportError:
    _SentenceTransformer = None  # type: ignore

_model = None


def load_model() -> None:
    """Load the embedding model into memory. Call once at server startup."""
    global _model
    if _SentenceTransformer is None:
        raise RuntimeError(
            "sentence-transformers is not installed. "
            "Run: pip install sentence-transformers"
        )
    if _model is None:
        logger.info("Loading embedding model: %s", MODEL_NAME)
        _model = _SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model ready.")


def embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts. Returns L2-normalised float vectors.

    normalize_embeddings=True ensures dot product == cosine similarity,
    which simplifies the similarity search in ml/similarity.py.
    """
    if _model is None:
        raise RuntimeError("Embedding model not loaded. Call load_model() at startup.")
    vectors = _model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()
