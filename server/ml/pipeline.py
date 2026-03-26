"""End-to-end labeling pipeline: embed → match → label or suggest."""
import logging

from app.models.label import Label
from ml.centroid import (
    CLUSTER_THRESHOLD,
    compute_medoid,
    fit_kmeans,
    k_for_count,
)
from ml.embeddings import embed
from ml.similarity import find_best_label, LABEL_THRESHOLD

logger = logging.getLogger(__name__)

# Must match the name of the pre-created subscription label exactly.
SUBSCRIPTION_LABEL = "Subscription List"


def build_email_text(subject: str, body: str) -> str:
    """Combine subject and body into a single embedding input."""
    return f"{subject}\n\n{body}".strip()


def _check_rules(
    labels: dict[str, Label],
    list_unsubscribe: bool,
    body: str,
) -> str | None:
    """Return a label name if a deterministic rule matches, otherwise None.

    Rules are checked in priority order and short-circuit the ML pipeline entirely.
    The matched label must exist in the user's label store to be returned.
    """
    if SUBSCRIPTION_LABEL in labels:
        if list_unsubscribe or "unsubscribe" in body.lower():
            return SUBSCRIPTION_LABEL
    return None


def batch_process_emails(
    messages: list[dict],
    labels: dict[str, Label],
    auto_label: bool = False,
    threshold: float = LABEL_THRESHOLD,
    debug: bool = False,
) -> list[dict | None]:
    """Embed and classify a list of emails in one batched encode call.

    Each entry in `messages` must have keys: subject, body, list_unsubscribe.
    Returns a result dict (same shape as process_email) or None per message.

    All messages are embedded in a single model.encode() call. Rule-matched
    messages are also run through the ML pipeline (excluding the rule-matched
    label) to identify their secondary category (e.g. a subscription email that
    is also a Receipt). The secondary result is returned under the "ml_label" key.
    """
    if not messages:
        return []

    texts: list[str] = []
    text_indices: list[int] = []
    results: list[dict | None] = [None] * len(messages)
    rule_matches: dict[int, str] = {}  # msg_idx → rule-matched label name

    for i, msg in enumerate(messages):
        text = build_email_text(msg["subject"], msg["body"])
        rule_match = _check_rules(labels, msg.get("list_unsubscribe", False), msg["body"])
        if rule_match:
            rule_matches[i] = rule_match
        texts.append(text)
        text_indices.append(i)

    vectors = embed(texts)
    for batch_idx, msg_idx in enumerate(text_indices):
        text = texts[batch_idx]
        vector = vectors[batch_idx]
        rule_match = rule_matches.get(msg_idx)

        if rule_match:
            label = labels[rule_match]
            primary_action = "label" if auto_label else "suggest"
            # Run ML against all other labels to find a secondary category.
            other_labels = {n: l for n, l in labels.items() if n != rule_match}
            ml_match = (
                find_best_label(vector, other_labels, threshold=threshold, email_text=text, debug=debug)
                if other_labels else None
            )
            if ml_match and ml_match["action"] == "label" and not auto_label:
                ml_match = {**ml_match, "action": "suggest"}
            results[msg_idx] = {
                "label_name": rule_match,
                "gmail_label_id": label.gmail_label_id,
                "score": 1.0,
                "action": primary_action,
                "vector": vector,
                "text": text,
                "ml_label": ml_match,
                "all_scores": ml_match.get("all_scores") if ml_match else None,
            }
        else:
            match = find_best_label(vector, labels, threshold=threshold, email_text=text, debug=debug)
            if match is None:
                continue
            action = match["action"]
            if action == "label" and not auto_label:
                action = "suggest"
            label = labels[match["label_name"]]
            results[msg_idx] = {
                "label_name": match["label_name"],
                "gmail_label_id": label.gmail_label_id,
                "score": match["score"],
                "action": action,
                "vector": vector,
                "text": text,
                "all_scores": match.get("all_scores"),
            }

    return results


def process_email(
    subject: str,
    body: str,
    labels: dict[str, Label],
    auto_label: bool = False,
    threshold: float = LABEL_THRESHOLD,
    list_unsubscribe: bool = False,
) -> dict | None:
    """Embed an email and determine whether to label or suggest.

    Returns:
        {
            "label_name": str,
            "gmail_label_id": str | None,
            "score": float,
            "action": "label" | "suggest",
            "vector": list[float],   # embedding (needed for confirm_label)
            "text": str,             # full text (needed for BM25 confirm_label)
        }
        or None if no seeded labels exist yet.
    """
    text = build_email_text(subject, body)

    rule_match = _check_rules(labels, list_unsubscribe, body)
    if rule_match:
        label = labels[rule_match]
        return {
            "label_name": rule_match,
            "gmail_label_id": label.gmail_label_id,
            "score": 1.0,
            "action": "label" if auto_label else "suggest",
            "vector": None,
            "text": text,
        }

    vector = embed([text])[0]

    result = find_best_label(vector, labels, threshold=threshold, email_text=text)
    if result is None:
        return None

    action = result["action"]
    if action == "label" and not auto_label:
        action = "suggest"

    label = labels[result["label_name"]]
    return {
        "label_name": result["label_name"],
        "gmail_label_id": label.gmail_label_id,
        "score": result["score"],
        "action": action,
        "vector": vector,
        "text": text,
    }


def seed_label(seed_texts: list[tuple[str, str]]) -> dict:
    """Embed seed emails and return initial label fields for MongoDB.

    Called when a user selects emails to define a new label.
    Always starts in bootstrap phase (single medoid), regardless of seed count.

    Returns a dict of field name → value to be written under labels.<name> in MongoDB.
    """
    texts = [build_email_text(subject, body) for subject, body in seed_texts]
    embeddings = embed(texts)
    medoid = compute_medoid(embeddings)
    return {
        "embeddings": embeddings,
        "texts": texts,
        "medoid": medoid,
        "phase": "bootstrap",
        "count": len(embeddings),
    }


def confirm_label_batch(label: Label, new_items: list[tuple[list[float], str]]) -> dict:
    """Same as confirm_label but accepts multiple (vector, text) pairs at once.

    Appends all new embeddings/texts in one pass, then computes medoid or k-means
    a single time. Avoids N recomputations when multiple emails are confirmed for
    the same label in one request.
    """
    new_embeddings = label.embeddings + [v for v, _ in new_items]
    new_texts = label.texts + [t for _, t in new_items]
    new_count = label.count + len(new_items)

    if new_count < CLUSTER_THRESHOLD:
        return {
            "embeddings": new_embeddings,
            "texts": new_texts,
            "medoid": compute_medoid(new_embeddings),
            "phase": "bootstrap",
            "count": new_count,
        }

    k = k_for_count(new_count)
    return {
        "embeddings": new_embeddings,
        "texts": new_texts,
        "clusters": fit_kmeans(new_embeddings, k),
        "phase": "mature",
        "count": new_count,
    }


def confirm_label(label: Label, new_vector: list[float], new_text: str) -> dict:
    """Return MongoDB field updates after a user confirms a label assignment.

    Appends the new embedding and text to the label's corpus, then either:
    - Bootstrap (count < CLUSTER_THRESHOLD): recomputes medoid from all embeddings.
    - Mature (count >= CLUSTER_THRESHOLD): refits k-means cluster centers.

    Returns a dict of field name → value to be written under labels.<name> in MongoDB.
    """
    new_embeddings = label.embeddings + [new_vector]
    new_texts = label.texts + [new_text]
    new_count = label.count + 1

    if new_count < CLUSTER_THRESHOLD:
        return {
            "embeddings": new_embeddings,
            "texts": new_texts,
            "medoid": compute_medoid(new_embeddings),
            "phase": "bootstrap",
            "count": new_count,
        }

    k = k_for_count(new_count)
    return {
        "embeddings": new_embeddings,
        "texts": new_texts,
        "clusters": fit_kmeans(new_embeddings, k),
        "phase": "mature",
        "count": new_count,
    }
