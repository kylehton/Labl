import os
from typing import Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(
            MONGO_URI,
            tz_aware=True,
            maxPoolSize=50,
            minPoolSize=5,
        )
        _db = _client[MONGO_DB_NAME]


async def close_mongo_connection() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Mongo not initialized")
    return _db


def get_collection(name: str):
    return get_db()[name]


async def insert_one(collection: str, document: dict):
    result = await get_collection(collection).insert_one(document)
    return result.inserted_id


async def find_one(collection: str, query: dict):
    return await get_collection(collection).find_one(query)


async def find_many(collection: str, query: dict, limit: int = 100) -> list:
    cursor = get_collection(collection).find(query).limit(limit)
    return await cursor.to_list(length=limit)


async def update_one(collection: str, query: dict, update: dict) -> int:
    result = await get_collection(collection).update_one(query, update)
    return result.modified_count


async def upsert_one(collection: str, query: dict, document: dict) -> None:
    await get_collection(collection).update_one(query, {"$set": document}, upsert=True)


async def delete_one(collection: str, query: dict) -> int:
    result = await get_collection(collection).delete_one(query)
    return result.deleted_count
