# app/worker/celery_app.py
import os
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

# Get Redis URL from environment variable, default to localhost if not set
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Example configuration
celery_app = Celery(
    "agentos_tasks",
    broker=redis_url, # Use environment variable
    backend=redis_url, # Use environment variable
    include=[
        "app.worker.tasks_delivery",
        "app.worker.tasks_scheduling",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "trigger-fallback-checks-scheduler": {
            "task": "schedule.trigger_fallback_checks",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "periodic"}
        },
    }
)