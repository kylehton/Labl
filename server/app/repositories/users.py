# app/repositories/users.py

from datetime import datetime, UTC
from typing import Optional
from pymongo import ReturnDocument

from config.db import get_db
from app.models.user import User, UserDocument

USERS_COLLECTION = "users"

_repo: Optional["UserRepository"] = None


def _repo_instance() -> "UserRepository":
    global _repo
    if _repo is None:
        _repo = UserRepository()
    return _repo


async def get_user_by_id(user_id: str) -> Optional[UserDocument]:
    return await _repo_instance().get_by_id(user_id)


async def get_or_create_user(user_id: str, email: str, name: str) -> UserDocument:
    existing = await get_user_by_id(user_id)
    if existing:
        return existing

    from app.repositories.presets import get_preset_labels
    from app.models.label import Label

    preset_labels = await get_preset_labels()

    # Subscription List has no medoid — it is matched purely by _check_rules.
    preset_labels["Subscription List"] = Label(name="Subscription List", type="system")

    doc = UserDocument(
        user=User(user_id=user_id, email=email, name=name),
        auto_apply=False,
        auto_sync=False,
        labels=preset_labels,
    )
    await _repo_instance().upsert(doc)
    return doc


async def update_user_document(user_id: str, update: dict) -> Optional[UserDocument]:
    return await _repo_instance().update_fields(user_id, update)


async def get_users_due_for_auto_sync(now: datetime) -> list["UserDocument"]:
    return await _repo_instance().get_due_for_auto_sync(now)


async def ensure_user_indexes() -> None:
    await _repo_instance().ensure_indexes()


class UserRepository:
    @property
    def collection(self):
        return get_db()[USERS_COLLECTION]

    async def get_by_id(self, user_id: str) -> Optional[UserDocument]:
        doc = await self.collection.find_one({"user.user_id": user_id}) or await self.collection.find_one({"user_id": user_id})
        if not doc:
            return None

        doc.pop("_id", None)
        return UserDocument.model_validate(doc)

    async def upsert(self, user_doc: UserDocument) -> None:
        payload = user_doc.model_dump()
        payload["updated_at"] = datetime.now(UTC)

        await self.collection.update_one(
            {"user.user_id": user_doc.user.user_id},
            {"$set": payload},
            upsert=True,
        )

    async def update_fields(
        self, user_id: str, update: dict
    ) -> Optional[UserDocument]:
        update["updated_at"] = datetime.now(UTC)

        result = await self.collection.find_one_and_update(
            {"user.user_id": user_id},
            {"$set": update},
            return_document=ReturnDocument.AFTER,
        )

        if not result:
            return None

        result.pop("_id", None)
        return UserDocument.model_validate(result)

    async def get_due_for_auto_sync(self, now: datetime) -> list:
        cursor = self.collection.find({
            "auto_sync": True,
            "$or": [
                {"next_sync_at": {"$lte": now}},
                {"next_sync_at": None},
                {"next_sync_at": {"$exists": False}},
            ],
        })
        docs = await cursor.to_list(length=None)
        result = []
        for doc in docs:
            doc.pop("_id", None)
            try:
                result.append(UserDocument.model_validate(doc))
            except Exception:
                pass
        return result

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            "user.user_id", unique=True
        )
