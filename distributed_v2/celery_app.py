from __future__ import annotations

import os
from celery import Celery

celery_app = Celery(
    "intelligence_os",
    broker=os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_RESULT_BACKEND", "redis://redis:6379/1"),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "continuous-recon-loop": {
            "task": "distributed_v2.tasks.autonomous_recon_loop",
            "schedule": 300.0,
        }
    },
)
