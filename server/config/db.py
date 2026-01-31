from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    global client, db

    if client is None:
        client = AsyncIOMotorClient(
            MONGO_URI,
            maxPoolSize=50,
            minPoolSize=5
        )
        db = client[MONGO_DB_NAME]


async def close_mongo_connection() -> None:
    global client
    if client is not None:
        client.close()
        client = None


def get_db() -> AsyncIOMotorDatabase:
    if db is None:
        raise RuntimeError("MongoDB not initialized. Connect to Mongo Client first.")
    return db


def get_collection(name: str):
    return get_db()[name]


async def insert_one(collection: str, document: dict):
    result = await get_collection(collection).insert_one(document)
    return result.inserted_id


async def find_one(collection: str, query: dict):
    return await get_collection(collection).find_one(query)


async def find_many(collection: str, query: dict, limit: int = 100):
    cursor = get_collection(collection).find(query).limit(limit)
    return await cursor.to_list(length=limit)


async def update_one(collection: str, query: dict, update: dict):
    result = await get_collection(collection).update_one(query, update)
    return result.modified_count


async def delete_one(collection: str, query: dict):
    result = await get_collection(collection).delete_one(query)
    return result.deleted_count
