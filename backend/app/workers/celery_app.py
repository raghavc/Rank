from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings


_settings = get_settings()

celery_app = Celery(
    "rank",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
    include=[
        "app.workers.refresh_balances",
        "app.workers.recompute_leaderboard",
    ],
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
        "refresh-all-balances-daily": {
            "task": "app.workers.refresh_balances.refresh_all_balances",
            "schedule": crontab(hour=4, minute=0),
        },
    },
)
