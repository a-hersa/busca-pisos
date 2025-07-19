from app.celery_app import celery_app
from app.services.notifications import notification_manager
import asyncio

@celery_app.task
def send_weekly_summaries():
    """
    Celery task to send weekly summary emails
    """
    asyncio.run(notification_manager.send_weekly_summaries())