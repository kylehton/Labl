"""Repository for label_records collection."""
from datetime import datetime, UTC
from typing import Optional

from bson import ObjectId
from pymongo import DESCENDING

from app.models.label_record import LabelRecord
from config.db import get_db

COLLECTION = "label_records"


def _get_col():
    return get_db()[COLLECTION]


def _to_record(doc: dict) -> LabelRecord:
    doc["record_id"] = str(doc.pop("_id"))
    return LabelRecord.model_validate(doc)


async def insert_record(record: LabelRecord) -> str:
    """Insert a label record. Returns the string record_id."""
    payload = record.model_dump(exclude={"record_id"})
    result = await _get_col().insert_one(payload)
    return str(result.inserted_id)


async def get_record(record_id: str) -> Optional[LabelRecord]:
    doc = await _get_col().find_one({"_id": ObjectId(record_id)})
    if not doc:
        return None
    return _to_record(doc)


async def get_records_for_user(
    user_id: str,
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
) -> list[LabelRecord]:
    query: dict = {"user_id": user_id}
    if status:
        query["status"] = status
    cursor = (
        _get_col()
        .find(query)
        .sort("applied_at", DESCENDING)
        .skip(offset)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_to_record(d) for d in docs]


async def update_record_status(
    record_id: str,
    status: str,
    resolved_at: Optional[datetime] = None,
) -> Optional[LabelRecord]:
    update: dict = {"status": status}
    if resolved_at is not None:
        update["resolved_at"] = resolved_at
    doc = await _get_col().find_one_and_update(
        {"_id": ObjectId(record_id)},
        {"$set": update},
        return_document=True,
    )
    if not doc:
        return None
    return _to_record(doc)


async def ensure_indexes() -> None:
    col = _get_col()
    await col.create_index([("user_id", DESCENDING), ("applied_at", DESCENDING)])
    await col.create_index([("user_id", DESCENDING), ("status", DESCENDING)])
    await col.create_index([("user_id", DESCENDING), ("gmail_message_id", DESCENDING)])
