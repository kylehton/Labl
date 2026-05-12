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


async def delete_resolved_records_before(user_id: str, threshold: datetime) -> int:
    """Delete terminal-status records older than threshold. Leaves 'suggested' records intact."""
    result = await _get_col().delete_many({
        "user_id": user_id,
        "status": {"$in": ["applied", "confirmed", "rejected", "undone"]},
        "applied_at": {"$lt": threshold},
    })
    return result.deleted_count


async def get_recent_grouped_emails(
    user_id: str,
    limit: Optional[int] = 20,
) -> list[dict]:
    """Return recent emails grouped by message, with confirmed and suggested label arrays.

    Runs a MongoDB aggregation so grouping, filtering, and sorting all happen in the DB.
    Only active statuses (applied, confirmed, suggested) are included — rejected and undone
    are excluded so stale labels don't appear on the dashboard.
    """
    pipeline = [
        {"$match": {
            "user_id": user_id,
            "status": {"$nin": ["rejected", "undone"]},
        }},
        {"$group": {
            "_id": "$gmail_message_id",
            "subject": {"$first": "$subject"},
            "applied_at": {"$max": "$applied_at"},
            "records": {"$push": {
                "record_id": {"$toString": "$_id"},
                "label_name": "$label_name",
                "status": "$status",
            }},
        }},
        {"$sort": {"applied_at": DESCENDING}},
        *([{"$limit": limit}] if limit is not None else []),
        {"$project": {
            "_id": 0,
            "gmail_message_id": "$_id",
            "subject": 1,
            "applied_at": 1,
            "confirmed_labels": {
                "$map": {
                    "input": {
                        "$filter": {
                            "input": "$records",
                            "as": "r",
                            "cond": {"$in": ["$$r.status", ["applied", "confirmed"]]},
                        }
                    },
                    "as": "r",
                    "in": {"record_id": "$$r.record_id", "label_name": "$$r.label_name"},
                }
            },
            "suggested_labels": {
                "$map": {
                    "input": {
                        "$filter": {
                            "input": "$records",
                            "as": "r",
                            "cond": {"$eq": ["$$r.status", "suggested"]},
                        }
                    },
                    "as": "r",
                    "in": {"record_id": "$$r.record_id", "label_name": "$$r.label_name"},
                }
            },
        }},
    ]
    cursor = _get_col().aggregate(pipeline)
    return await cursor.to_list(length=None)


async def ensure_indexes() -> None:
    col = _get_col()
    await col.create_index([("user_id", DESCENDING), ("applied_at", DESCENDING)])
    await col.create_index([("user_id", DESCENDING), ("status", DESCENDING)])
    await col.create_index([("user_id", DESCENDING), ("gmail_message_id", DESCENDING)])
