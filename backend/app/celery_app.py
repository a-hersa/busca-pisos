from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Create Celery app
celery_app = Celery(
    "inmobiliario_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.scrapy_runner", "app.tasks.notifications"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Madrid",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "app.tasks.scrapy_runner.run_spider": {"queue": "scrapy_queue"},
        "app.services.scheduler.check_scheduled_jobs": {"queue": "scheduler_queue"},
    },
    beat_schedule={
        'check-scheduled-jobs': {
            'task': 'app.services.scheduler.check_scheduled_jobs',
            'schedule': 60.0,  # Run every minute
        },
        'send-weekly-summaries': {
            'task': 'app.tasks.notifications.send_weekly_summaries',
            'schedule': 604800.0,  # Run every week (7 days * 24 hours * 60 minutes * 60 seconds)
        },
    },
)