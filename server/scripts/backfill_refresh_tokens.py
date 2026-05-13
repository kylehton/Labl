"""One-off script: copy refresh_token_encrypted from sessions → user documents.

Run from the server/ directory:
    python scripts/backfill_refresh_tokens.py

For a specific user only:
    python scripts/backfill_refresh_tokens.py --user-id <user_id>
"""
import argparse
import asyncio
import os
import sys

from datetime import UTC, datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING


MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")


async def backfill(user_id: str | None = None) -> None:
    client = AsyncIOMotorClient(
        MONGO_URI,
        tz_aware=True,
        tls=True,
        tlsALlowInvalidCertificates=True,
    )
    db = client[MONGO_DB_NAME]

    user_filter = {}
    if user_id:
        user_filter = {"user.user_id": user_id}

    users_cursor = db["users"].find(user_filter)
    users = await users_cursor.to_list(length=None)

    updated = 0
    skipped = 0
    not_found = 0

    for user_doc in users:
        uid = (user_doc.get("user") or {}).get("user_id") or user_doc.get("user_id")
        if not uid:
            print(f"  [SKIP] user doc missing user_id: {user_doc.get('_id')}")
            skipped += 1
            continue

        # Already has a refresh token on the user doc — nothing to do.
        if user_doc.get("refresh_token_encrypted"):
            print(f"  [SKIP] {uid} — already has refresh_token_encrypted")
            skipped += 1
            continue

        # Find the most recent non-expired session with a refresh token.
        session = await db["sessions"].find_one(
            {
                "user_id": uid,
                "refresh_token_encrypted": {"$exists": True, "$ne": None},
                "expires_at": {"$gt": datetime.now(UTC)},
            },
            sort=[("created_at", DESCENDING)],
        )

        if not session:
            # Fall back to any session with a refresh token, even expired ones.
            session = await db["sessions"].find_one(
                {
                    "user_id": uid,
                    "refresh_token_encrypted": {"$exists": True, "$ne": None},
                },
                sort=[("created_at", DESCENDING)],
            )

        if not session or not session.get("refresh_token_encrypted"):
            print(f"  [MISS] {uid} — no session with refresh token found")
            not_found += 1
            continue

        await db["users"].update_one(
            {"user.user_id": uid},
            {
                "$set": {
                    "refresh_token_encrypted": session["refresh_token_encrypted"],
                    "updated_at": datetime.now(UTC),
                }
            },
        )
        print(f"  [OK]   {uid} — refresh token written from session {session['session_id']}")
        updated += 1

    client.close()
    print(f"\nDone — updated: {updated}, skipped: {skipped}, no session found: {not_found}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill refresh tokens onto user documents.")
    parser.add_argument("--user-id", help="Limit to a single user_id")
    args = parser.parse_args()

    asyncio.run(backfill(user_id=args.user_id))
