"""Celery task: scan users due for auto-sync and enqueue labeling pipeline tasks."""
import asyncio
import logging
from datetime import UTC, datetime, timedelta

from pymongo import DESCENDING

from config.celery_app import celery_app
from config.db import reconnect_for_worker

logger = logging.getLogger(__name__)

SYNC_INTERVAL_MINUTES = 60  # 1h


@celery_app.task(name="tasks.auto_sync.scan_and_enqueue_auto_syncs")
def scan_and_enqueue_auto_syncs() -> dict:
    return asyncio.run(_scan_async())


async def _scan_async() -> dict:
    await reconnect_for_worker()

    from app.repositories.users import get_users_due_for_auto_sync, update_user_document
    from config.crypto import decrypt
    from config.db import get_db

    now = datetime.now(UTC)
    users = await get_users_due_for_auto_sync(now)
    enqueued = 0
    skipped = 0

    for user_doc in users:
        user_id = user_doc.user.user_id

        session = await get_db()["sessions"].find_one(
            {"user_id": user_id, "expires_at": {"$gt": now}},
            sort=[("created_at", DESCENDING)],
        )
        if not session:
            logger.info("No active session for user %s — skipping auto-sync", user_id)
            skipped += 1
            continue

        # Advance next_sync_at before enqueuing to block the scanner from re-enqueuing
        # this user until the interval has elapsed, even if the task is still running.
        next_sync = now + timedelta(minutes=SYNC_INTERVAL_MINUTES)
        await update_user_document(user_id, {"next_sync_at": next_sync})

        refresh_enc = session.get("refresh_token_encrypted")
        refresh_token = decrypt(refresh_enc) if refresh_enc else None

        celery_app.send_task(
            "tasks.labeling.run_labeling_pipeline",
            kwargs={
                "user_id": user_id,
                "access_token": "",
                "refresh_token": refresh_token,
                "session_id": session.get("session_id"),
                "triggered_by": "auto",
            },
        )
        logger.info("Enqueued auto-sync for user %s (next at %s)", user_id, next_sync)
        enqueued += 1

    return {"enqueued": enqueued, "skipped": skipped}
