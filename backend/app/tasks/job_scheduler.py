from app.celery_app import celery_app
import asyncio
import asyncpg
import os
from datetime import datetime, timedelta

@celery_app.task
def schedule_job_async(job_id: int):
    """
    Asynchronously schedule a job without blocking the API response
    """
    try:
        asyncio.run(schedule_job_in_db(job_id))
    except Exception as e:
        print(f"Failed to schedule job {job_id}: {e}")

async def schedule_job_in_db(job_id: int):
    """
    Schedule job by updating next_run time in database
    """
    DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB', 'inmobiliario_db')}"
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Get job details
        job = await conn.fetchrow(
            "SELECT schedule_type, cron_expression FROM crawl_jobs WHERE job_id = $1",
            job_id
        )
        
        if not job or job['schedule_type'] == 'manual':
            await conn.close()
            return
        
        # Calculate next run time based on schedule type
        next_run = calculate_next_run(job['schedule_type'], job['cron_expression'])
        
        # Update job with next run time
        await conn.execute(
            "UPDATE crawl_jobs SET next_run = $1 WHERE job_id = $2",
            next_run, job_id
        )
        
        await conn.close()
        
    except Exception as e:
        print(f"Error scheduling job {job_id}: {e}")

def calculate_next_run(schedule_type: str, cron_expression: str = None) -> datetime:
    """
    Calculate next run time based on schedule type
    """
    now = datetime.utcnow()
    
    if schedule_type == 'daily':
        return now + timedelta(days=1)
    elif schedule_type == 'weekly':
        return now + timedelta(weeks=1)
    elif schedule_type == 'monthly':
        # Simple monthly scheduling - add 30 days
        return now + timedelta(days=30)
    elif schedule_type == 'custom' and cron_expression:
        # For now, just schedule for next hour - could implement full cron parsing later
        return now + timedelta(hours=1)
    else:
        return now + timedelta(hours=1)