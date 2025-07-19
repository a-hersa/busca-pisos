from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_async_session
from app.models.user import User
from app.models.crawl_job import CrawlJob
from app.schemas.crawl_job import CrawlJobCreate, CrawlJobResponse, CrawlJobUpdate
from app.core.deps import get_current_user, log_action

router = APIRouter()

@router.get("/", response_model=List[CrawlJobResponse])
async def list_user_jobs(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(CrawlJob).where(CrawlJob.created_by == current_user.user_id)
    )
    jobs = result.scalars().all()
    return jobs

@router.post("/", response_model=CrawlJobResponse)
async def create_crawl_job(
    job_data: CrawlJobCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
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
    
    # Log job creation
    await log_action("job_create", current_user.user_id, "crawl_job", new_job.job_id,
                    {"job_name": job_data.job_name, "spider_name": job_data.spider_name}, 
                    request, session)
    
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
    
    # TODO: Integrate with Celery to actually run the job
    # For now, just mark as running
    job.status = "running"
    await session.commit()
    
    # Log job execution
    await log_action("job_run", current_user.user_id, "crawl_job", job.job_id,
                    {"manual_execution": True}, request, session)
    
    return {"message": "Job execution started", "job_id": job_id}