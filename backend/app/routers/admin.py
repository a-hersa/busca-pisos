from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from app.database import get_async_session
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.crawl_job import CrawlJob
from app.schemas.user import UserResponse
from app.core.deps import get_current_admin_user

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users

@router.get("/audit-logs")
async def get_audit_logs(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(AuditLog).order_by(desc(AuditLog.created_at)).limit(100)
    )
    logs = result.scalars().all()
    return [
        {
            "log_id": log.log_id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": str(log.ip_address) if log.ip_address else None,
            "user_agent": log.user_agent,
            "created_at": log.created_at
        }
        for log in logs
    ]

@router.get("/system-stats")
async def get_system_stats(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Count users
    user_result = await session.execute(select(User))
    total_users = len(user_result.scalars().all())
    
    # Count jobs
    job_result = await session.execute(select(CrawlJob))
    total_jobs = len(job_result.scalars().all())
    
    # Count active jobs
    active_job_result = await session.execute(
        select(CrawlJob).where(CrawlJob.status.in_(["pending", "running"]))
    )
    active_jobs = len(active_job_result.scalars().all())
    
    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs
    }