"""Celery application instance and configuration."""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_RESULT_URL = os.getenv("REDIS_RESULT_URL", "redis://localhost:6379/1")

celery_app = Celery(
    "labl",
    broker=REDIS_URL,
    backend=REDIS_RESULT_URL,
    include=["tasks.labeling", "tasks.auto_sync"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=86400,  # 24h — results also persisted to Mongo
    task_track_started=True,
    beat_schedule={
        "scan-auto-syncs": {
            "task": "tasks.auto_sync.scan_and_enqueue_auto_syncs",
            "schedule": 300.0,  # every 5 minutes
        },
    },
)
