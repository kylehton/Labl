"""Celery task: scan users due for auto-sync and enqueue labeling pipeline tasks."""
import asyncio
import logging
from datetime import UTC, datetime, timedelta

from config.celery_app import celery_app
from config.db import reconnect_for_worker

logger = logging.getLogger(__name__)

SYNC_INTERVAL_MINUTES = 60  # 1h


@celery_app.task(name="tasks.auto_sync.scan_and_enqueue_auto_syncs")
def scan_and_enqueue_auto_syncs() -> dict:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_scan_async())
    finally:
        loop.close()
        asyncio.set_event_loop(None)


async def _scan_async() -> dict:
    await reconnect_for_worker()
    from config.db import close_mongo_connection

    from app.repositories.users import get_users_due_for_auto_sync, update_user_document
    from config.crypto import decrypt

    now = datetime.now(UTC)
    users = await get_users_due_for_auto_sync(now)
    enqueued = 0
    skipped = 0

    for user_doc in users:
        user_id = user_doc.user.user_id

        if not user_doc.refresh_token_encrypted:
            logger.info("No refresh token for user %s — skipping auto-sync", user_id)
            skipped += 1
            continue

        # Advance next_sync_at before enqueuing to block the scanner from re-enqueuing
        # this user until the interval has elapsed, even if the task is still running.
        next_sync = now + timedelta(minutes=SYNC_INTERVAL_MINUTES)
        await update_user_document(user_id, {"next_sync_at": next_sync})

        refresh_token = decrypt(user_doc.refresh_token_encrypted)

        celery_app.send_task(
            "tasks.labeling.run_labeling_pipeline",
            kwargs={
                "user_id": user_id,
                "access_token": "",
                "refresh_token": refresh_token,
                "session_id": None,
                "triggered_by": "auto",
            },
        )
        logger.info("Enqueued auto-sync for user %s (next at %s)", user_id, next_sync)
        enqueued += 1

    await close_mongo_connection()
    return {"enqueued": enqueued, "skipped": skipped}
