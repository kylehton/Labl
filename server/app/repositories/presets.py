"""Preset label repository.

Manages the `preset` collection in MongoDB, which stores pre-computed Label
objects (embeddings + medoid) for each system label. This collection is
seeded once at startup and read when a new user document is created so that
their label store starts populated.
"""

import logging

from config.db import get_db
from app.models.label import Label

logger = logging.getLogger(__name__)

PRESET_COLLECTION = "preset"


async def seed_preset_collection() -> None:
    """Populate the preset collection if it is empty.

    Called once during app startup. If the collection already has documents
    (i.e. a previous startup already seeded it), this is a no-op.
    Building preset labels runs the embedding model, so this only happens
    once across the lifetime of the deployment.
    """
    col = get_db()[PRESET_COLLECTION]
    if await col.count_documents({}) > 0:
        logger.info("Preset collection already seeded — skipping.")
        return

    # Import here to avoid loading the embedding model at module import time.
    from ml.preset_labels import build_preset_labels

    logger.info("Seeding preset label collection...")
    labels = build_preset_labels()
    docs = [{"name": name, **label.model_dump()} for name, label in labels.items()]
    await col.insert_many(docs)
    logger.info("Preset collection seeded with %d labels.", len(docs))


async def get_preset_labels() -> dict[str, Label]:
    """Return all preset labels from the collection as a name → Label dict."""
    col = get_db()[PRESET_COLLECTION]
    docs = await col.find({}).to_list(length=100)
    result: dict[str, Label] = {}
    for doc in docs:
        doc.pop("_id", None)
        name = doc["name"]
        result[name] = Label.model_validate(doc)
    return result
