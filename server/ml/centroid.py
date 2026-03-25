"""Medoid computation and k-means clustering for label embedding vectors."""
import numpy as np
from sklearn.cluster import KMeans

# Emails needed before graduating from single medoid to k-means clusters.
CLUSTER_THRESHOLD = 20
# Hard cap on number of clusters regardless of email count.
K_MAX = 5


def k_for_count(n: int) -> int:
    """Return the number of k-means clusters appropriate for n confirmed emails."""
    return min(K_MAX, max(2, n // 10))


def compute_medoid(embeddings: list[list[float]]) -> list[float]:
    """Return the embedding that is most central to all others.

    Because all vectors are L2-normalised, dot product == cosine similarity,
    so the most central point is argmax of row sums of the gram matrix.
    This is an actual data point (a real email embedding), not a synthetic average.
    """
    arr = np.array(embeddings, dtype=np.float32)
    # gram[i, j] = cosine_similarity(e_i, e_j) since vectors are L2-normalised
    gram = arr @ arr.T
    centrality = gram.sum(axis=1)
    medoid_idx = int(np.argmax(centrality))
    return arr[medoid_idx].tolist()


def fit_kmeans(embeddings: list[list[float]], k: int) -> list[list[float]]:
    """Fit k-means and return L2-normalised cluster centers.

    Called when label.count >= CLUSTER_THRESHOLD. Each center is renormalised
    so cosine similarity (dot product) stays well-defined against them.
    """
    arr = np.array(embeddings, dtype=np.float32)
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    km.fit(arr)
    centers = km.cluster_centers_.astype(np.float32)
    norms = np.linalg.norm(centers, axis=1, keepdims=True)
    norms = np.where(norms > 0, norms, 1.0)
    centers = centers / norms
    return centers.tolist()
