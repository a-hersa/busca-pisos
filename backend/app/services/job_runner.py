from app.celery_app import celery_app
from app.tasks.scrapy_runner import run_spider
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.crawl_job import CrawlJob, JobExecution
from datetime import datetime
from typing import Dict, Any

class JobRunnerService:
    """
    Service for managing crawl job execution
    """
    
    @staticmethod
    async def execute_job(job_id: int, session: AsyncSession) -> Dict[str, Any]:
        """
        Execute a crawl job asynchronously using Celery
        """
        # Get job details
        result = await session.execute(select(CrawlJob).where(CrawlJob.job_id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status == "running":
            raise ValueError(f"Job {job_id} is already running")
        
        # Start Celery task
        task = run_spider.delay(
            job_id=job.job_id,
            spider_name=job.spider_name,
            start_urls=job.start_urls,
            job_config=job.job_config
        )
        
        return {
            "task_id": task.id,
            "job_id": job_id,
            "status": "started"
        }
    
    @staticmethod
    async def get_job_status(job_id: int, session: AsyncSession) -> Dict[str, Any]:
        """
        Get the current status of a job and its latest execution
        """
        # Get job details
        result = await session.execute(select(CrawlJob).where(CrawlJob.job_id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Get latest execution
        exec_result = await session.execute(
            select(JobExecution)
            .where(JobExecution.job_id == job_id)
            .order_by(JobExecution.started_at.desc())
            .limit(1)
        )
        latest_execution = exec_result.scalar_one_or_none()
        
        # Get Celery task status if running
        celery_status = None
        if latest_execution and latest_execution.celery_task_id:
            task_result = celery_app.AsyncResult(latest_execution.celery_task_id)
            celery_status = {
                "state": task_result.state,
                "info": task_result.info if task_result.info else {}
            }
        
        return {
            "job_id": job.job_id,
            "job_name": job.job_name,
            "status": job.status,
            "latest_execution": {
                "execution_id": latest_execution.execution_id if latest_execution else None,
                "status": latest_execution.status if latest_execution else None,
                "started_at": latest_execution.started_at if latest_execution else None,
                "completed_at": latest_execution.completed_at if latest_execution else None,
                "items_scraped": latest_execution.items_scraped if latest_execution else 0,
                "error_message": latest_execution.error_message if latest_execution else None,
                "celery_task_id": latest_execution.celery_task_id if latest_execution else None
            },
            "celery_status": celery_status
        }
    
    @staticmethod
    async def cancel_job(job_id: int, session: AsyncSession) -> Dict[str, Any]:
        """
        Cancel a running job
        """
        # Get job details
        result = await session.execute(select(CrawlJob).where(CrawlJob.job_id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status != "running":
            raise ValueError(f"Job {job_id} is not running")
        
        # Get latest execution to find Celery task ID
        exec_result = await session.execute(
            select(JobExecution)
            .where(JobExecution.job_id == job_id)
            .where(JobExecution.status == "running")
            .order_by(JobExecution.started_at.desc())
            .limit(1)
        )
        running_execution = exec_result.scalar_one_or_none()
        
        if running_execution and running_execution.celery_task_id:
            # Revoke Celery task
            celery_app.control.revoke(running_execution.celery_task_id, terminate=True)
            
            # Update execution status
            await session.execute(
                update(JobExecution)
                .where(JobExecution.execution_id == running_execution.execution_id)
                .values(
                    status="cancelled",
                    completed_at=datetime.utcnow(),
                    error_message="Job cancelled by user"
                )
            )
        
        # Update job status
        await session.execute(
            update(CrawlJob)
            .where(CrawlJob.job_id == job_id)
            .values(status="cancelled")
        )
        
        await session.commit()
        
        return {
            "job_id": job_id,
            "status": "cancelled"
        }
    
    @staticmethod
    async def get_job_executions(job_id: int, session: AsyncSession, limit: int = 10) -> list:
        """
        Get execution history for a job
        """
        result = await session.execute(
            select(JobExecution)
            .where(JobExecution.job_id == job_id)
            .order_by(JobExecution.started_at.desc())
            .limit(limit)
        )
        executions = result.scalars().all()
        
        return [
            {
                "execution_id": exec.execution_id,
                "status": exec.status,
                "started_at": exec.started_at,
                "completed_at": exec.completed_at,
                "items_scraped": exec.items_scraped,
                "error_message": exec.error_message,
                "execution_log": exec.execution_log
            }
            for exec in executions
        ]