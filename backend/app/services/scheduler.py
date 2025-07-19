from celery import Celery
from celery.schedules import crontab
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.crawl_job import CrawlJob
from app.tasks.scrapy_runner import run_spider
from app.celery_app import celery_app
from datetime import datetime, timedelta
import asyncio
import asyncpg
import os
from typing import List

class JobScheduler:
    """
    Service for managing scheduled crawl jobs
    """
    
    @staticmethod
    async def schedule_job(job_id: int, session: AsyncSession) -> bool:
        """
        Schedule a job based on its schedule_type and cron_expression
        """
        result = await session.execute(select(CrawlJob).where(CrawlJob.job_id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            return False
        
        if job.schedule_type == 'manual':
            return True  # Manual jobs don't need scheduling
        
        # Calculate next run time
        next_run = JobScheduler._calculate_next_run(job.schedule_type, job.cron_expression)
        
        # Update job with next run time
        await session.execute(
            update(CrawlJob)
            .where(CrawlJob.job_id == job_id)
            .values(next_run=next_run)
        )
        await session.commit()
        
        # Register with Celery beat (dynamic scheduling)
        JobScheduler._register_periodic_task(job)
        
        return True
    
    @staticmethod
    async def unschedule_job(job_id: int) -> bool:
        """
        Remove a job from the schedule
        """
        task_name = f"scheduled_job_{job_id}"
        
        try:
            celery_app.control.revoke(task_name, terminate=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def _calculate_next_run(schedule_type: str, cron_expression: str = None) -> datetime:
        """
        Calculate the next run time for a job
        """
        now = datetime.utcnow()
        
        if cron_expression:
            # Parse cron expression (simplified implementation)
            return JobScheduler._parse_cron_next_run(cron_expression, now)
        
        # Default schedules
        if schedule_type == 'daily':
            return now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif schedule_type == 'weekly':
            days_ahead = 7 - now.weekday()  # Next Monday
            return (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
        elif schedule_type == 'monthly':
            next_month = now.replace(day=1) + timedelta(days=32)
            return next_month.replace(day=1, hour=9, minute=0, second=0, microsecond=0)
        
        return now + timedelta(hours=1)  # Default: 1 hour from now
    
    @staticmethod
    def _parse_cron_next_run(cron_expression: str, from_time: datetime) -> datetime:
        """
        Parse cron expression and calculate next run time
        Simplified implementation for common patterns
        """
        parts = cron_expression.split()
        if len(parts) != 5:
            # Invalid cron, default to 1 hour
            return from_time + timedelta(hours=1)
        
        minute, hour, day, month, weekday = parts
        
        # Simple implementation for daily schedules (0 9 * * *)
        if minute.isdigit() and hour.isdigit() and day == '*' and month == '*' and weekday == '*':
            target_hour = int(hour)
            target_minute = int(minute)
            
            next_run = from_time.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            
            # If time has passed today, schedule for tomorrow
            if next_run <= from_time:
                next_run += timedelta(days=1)
            
            return next_run
        
        # Default fallback
        return from_time + timedelta(hours=1)
    
    @staticmethod
    def _register_periodic_task(job: CrawlJob):
        """
        Register a periodic task with Celery beat
        This is a simplified implementation - in production you might use celery-beat-scheduler
        """
        task_name = f"scheduled_job_{job.job_id}"
        
        if job.cron_expression:
            # Parse cron expression to celery crontab
            parts = job.cron_expression.split()
            if len(parts) == 5:
                minute, hour, day_of_month, month_of_year, day_of_week = parts
                
                schedule = crontab(
                    minute=minute,
                    hour=hour,
                    day_of_month=day_of_month,
                    month_of_year=month_of_year,
                    day_of_week=day_of_week
                )
            else:
                # Invalid cron, use hourly
                schedule = crontab(minute=0)
        else:
            # Default schedules
            if job.schedule_type == 'daily':
                schedule = crontab(hour=9, minute=0)  # 9 AM daily
            elif job.schedule_type == 'weekly':
                schedule = crontab(hour=9, minute=0, day_of_week=1)  # Monday 9 AM
            elif job.schedule_type == 'monthly':
                schedule = crontab(hour=9, minute=0, day_of_month=1)  # 1st of month 9 AM
            else:
                schedule = crontab(minute=0)  # Hourly
        
        # Register the task (this would typically be done in celery beat configuration)
        celery_app.add_periodic_task(
            schedule,
            run_spider.s(
                job_id=job.job_id,
                spider_name=job.spider_name,
                start_urls=job.start_urls,
                job_config=job.job_config
            ),
            name=task_name
        )

class SchedulerManager:
    """
    Manager for checking and executing scheduled jobs
    """
    
    @staticmethod
    async def check_and_run_scheduled_jobs():
        """
        Check for jobs that need to be executed and run them
        This method should be called periodically (e.g., every minute)
        """
        DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB', 'inmobiliario_db')}"
        
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            
            # Find jobs that are due to run
            now = datetime.utcnow()
            rows = await conn.fetch("""
                SELECT job_id, job_name, spider_name, start_urls, job_config
                FROM crawl_jobs 
                WHERE schedule_type != 'manual' 
                AND next_run <= $1
                AND status != 'running'
            """, now)
            
            for row in rows:
                job_id = row['job_id']
                
                # Start the job
                task = run_spider.delay(
                    job_id=job_id,
                    spider_name=row['spider_name'],
                    start_urls=list(row['start_urls']),
                    job_config=dict(row['job_config']) if row['job_config'] else {}
                )
                
                # Calculate next run time
                next_run = await SchedulerManager._get_next_run_time(conn, job_id)
                
                # Update job status and next run time
                await conn.execute("""
                    UPDATE crawl_jobs 
                    SET status = 'running', next_run = $1 
                    WHERE job_id = $2
                """, next_run, job_id)
                
                print(f"Scheduled job {job_id} started with task ID: {task.id}")
            
            await conn.close()
            
        except Exception as e:
            print(f"Error checking scheduled jobs: {e}")
    
    @staticmethod
    async def _get_next_run_time(conn, job_id: int) -> datetime:
        """
        Calculate the next run time for a job
        """
        row = await conn.fetchrow("""
            SELECT schedule_type, cron_expression 
            FROM crawl_jobs 
            WHERE job_id = $1
        """, job_id)
        
        if row:
            return JobScheduler._calculate_next_run(
                row['schedule_type'], 
                row['cron_expression']
            )
        
        return datetime.utcnow() + timedelta(hours=1)

# Celery beat task to check for scheduled jobs
@celery_app.task
def check_scheduled_jobs():
    """
    Celery task to check and run scheduled jobs
    """
    asyncio.run(SchedulerManager.check_and_run_scheduled_jobs())