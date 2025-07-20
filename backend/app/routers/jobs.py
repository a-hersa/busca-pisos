from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import redis
import json
import os

from app.database import get_async_session
from app.models.user import User
from app.models.crawl_job import CrawlJob
from app.schemas.crawl_job import CrawlJobCreate, CrawlJobResponse, CrawlJobUpdate
from app.core.deps import get_current_user, log_action

# Redis client for caching
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

router = APIRouter()

@router.get("/debug-all")
async def debug_all_jobs(session: AsyncSession = Depends(get_async_session)):
    """Debug endpoint to see all jobs in database"""
    result = await session.execute(select(CrawlJob))
    jobs = result.scalars().all()
    
    return {
        "total_jobs": len(jobs),
        "jobs": [{"job_id": job.job_id, "job_name": job.job_name, "created_by": job.created_by, "status": job.status} for job in jobs]
    }

@router.get("/", response_model=List[CrawlJobResponse])
async def list_user_jobs(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    # FORCE FRESH DATA - NO CACHING WHATSOEVER
    print(f"🔍 API CALL: User {current_user.user_id} ({current_user.username}) requesting jobs")
    
    # Direct database query with explicit refresh
    await session.commit()  # Ensure any pending transactions are committed
    
    result = await session.execute(
        select(CrawlJob).where(CrawlJob.created_by == current_user.user_id)
    )
    jobs = result.scalars().all()
    
    print(f"📊 QUERY RESULT: Found {len(jobs)} jobs for user {current_user.user_id}")
    
    # Log each job found
    job_list = []
    for job in jobs:
        job_data = {
            "job_id": job.job_id,
            "job_name": job.job_name,
            "status": job.status,
            "created_by": job.created_by,
            "spider_name": job.spider_name,
            "schedule_type": job.schedule_type,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None
        }
        job_list.append(job_data)
        print(f"✅ Job: {job.job_id} - {job.job_name} ({job.status})")
    
    print(f"🚀 SENDING RESPONSE: {len(job_list)} jobs")
    return jobs

@router.post("/", response_model=CrawlJobResponse)
async def create_crawl_job(
    job_data: CrawlJobCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    print(f"🆕 CREATING JOB: User {current_user.user_id} ({current_user.username})")
    print(f"📝 JOB DATA: {job_data}")
    
    new_job = CrawlJob(
        job_name=job_data.job_name,
        spider_name=job_data.spider_name,
        start_urls=job_data.start_urls,
        created_by=current_user.user_id,
        schedule_type=job_data.schedule_type,
        cron_expression=job_data.cron_expression,
        job_config=job_data.job_config
    )
    
    session.add(new_job)
    await session.commit()
    await session.refresh(new_job)
    
    print(f"✅ JOB CREATED: ID={new_job.job_id}, Name='{new_job.job_name}', CreatedBy={new_job.created_by}")
    print(f"🎯 JOB DETAILS: Status={new_job.status}, Spider={new_job.spider_name}")
    
    # Invalidate cache immediately
    try:
        redis_client.delete(f"user_jobs:{current_user.user_id}")
    except:
        pass
    
    # Send real-time WebSocket notification
    try:
        from app.websocket import manager
        await manager.send_personal_message({
            "type": "job_created",
            "job_id": new_job.job_id,
            "job_name": new_job.job_name,
            "status": new_job.status
        }, current_user.user_id)
    except:
        pass  # Don't fail if WebSocket fails
    
    # Log job creation asynchronously (non-blocking)
    await log_action("job_create", current_user.user_id, "crawl_job", new_job.job_id,
                    {"job_name": job_data.job_name, "spider_name": job_data.spider_name,
                     "schedule_type": job_data.schedule_type}, 
                    request, session)
    
    # Schedule job asynchronously for non-manual jobs
    if new_job.schedule_type != 'manual':
        from app.tasks.job_scheduler import schedule_job_async
        schedule_job_async.delay(new_job.job_id)
    
    return new_job

@router.get("/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(CrawlJob).where(
            CrawlJob.job_id == job_id,
            CrawlJob.created_by == current_user.user_id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job

@router.put("/{job_id}", response_model=CrawlJobResponse)
async def update_crawl_job(
    job_id: int,
    job_update: CrawlJobUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(CrawlJob).where(
            CrawlJob.job_id == job_id,
            CrawlJob.created_by == current_user.user_id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Update job fields
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    await session.commit()
    await session.refresh(job)
    
    # Invalidate cache
    try:
        redis_client.delete(f"user_jobs:{current_user.user_id}")
    except:
        pass
    
    # Log job update
    await log_action("job_update", current_user.user_id, "crawl_job", job.job_id,
                    {"updated_fields": list(update_data.keys())}, request, session)
    
    return job

@router.delete("/{job_id}")
async def delete_crawl_job(
    job_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(CrawlJob).where(
            CrawlJob.job_id == job_id,
            CrawlJob.created_by == current_user.user_id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    await session.delete(job)
    await session.commit()
    
    # Invalidate cache
    try:
        redis_client.delete(f"user_jobs:{current_user.user_id}")
    except:
        pass
    
    # Log job deletion
    await log_action("job_delete", current_user.user_id, "crawl_job", job_id,
                    {"job_name": job.job_name}, request, session)
    
    return {"message": "Job deleted successfully"}

@router.post("/{job_id}/run")
async def run_crawl_job(
    job_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    from app.services.job_runner import JobRunnerService
    
    result = await session.execute(
        select(CrawlJob).where(
            CrawlJob.job_id == job_id,
            CrawlJob.created_by == current_user.user_id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    try:
        result = await JobRunnerService.execute_job(job_id, session)
        
        # Send real-time WebSocket notification
        try:
            from app.websocket import manager
            await manager.send_personal_message({
                "type": "job_started",
                "job_id": job.job_id,
                "job_name": job.job_name,
                "task_id": result["task_id"]
            }, current_user.user_id)
        except:
            pass
        
        # Invalidate cache for instant updates
        try:
            redis_client.delete(f"user_jobs:{current_user.user_id}")
        except:
            pass
        
        # Log job execution
        await log_action("job_run", current_user.user_id, "crawl_job", job.job_id,
                        {"manual_execution": True, "task_id": result["task_id"]}, request, session)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{job_id}/status")
async def get_job_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    from app.services.job_runner import JobRunnerService
    
    result = await session.execute(
        select(CrawlJob).where(
            CrawlJob.job_id == job_id,
            CrawlJob.created_by == current_user.user_id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    try:
        return await JobRunnerService.get_job_status(job_id, session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{job_id}/cancel")
async def cancel_crawl_job(
    job_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    from app.services.job_runner import JobRunnerService
    
    result = await session.execute(
        select(CrawlJob).where(
            CrawlJob.job_id == job_id,
            CrawlJob.created_by == current_user.user_id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    try:
        result = await JobRunnerService.cancel_job(job_id, session)
        
        # Log job cancellation
        await log_action("job_cancel", current_user.user_id, "crawl_job", job.job_id,
                        {"manual_cancellation": True}, request, session)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{job_id}/executions")
async def get_job_executions(
    job_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    from app.services.job_runner import JobRunnerService
    
    result = await session.execute(
        select(CrawlJob).where(
            CrawlJob.job_id == job_id,
            CrawlJob.created_by == current_user.user_id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return await JobRunnerService.get_job_executions(job_id, session)