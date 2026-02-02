"""Celery worker configuration and tasks."""

from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "complianceagent",
    broker=settings.celery_broker,
    backend=settings.redis_url,
    include=[
        "app.workers.monitoring_tasks",
        "app.workers.analysis_tasks",
        "app.workers.notification_tasks",
        "app.workers.pr_bot_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-regulatory-sources": {
        "task": "app.workers.monitoring_tasks.check_all_sources",
        "schedule": 6 * 3600,  # Every 6 hours
    },
    "update-compliance-scores": {
        "task": "app.workers.analysis_tasks.update_all_compliance_scores",
        "schedule": 24 * 3600,  # Daily
    },
    "cleanup-old-audit-entries": {
        "task": "app.workers.analysis_tasks.cleanup_old_data",
        "schedule": 7 * 24 * 3600,  # Weekly
    },
}
