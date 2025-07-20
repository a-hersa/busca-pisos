from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from pydantic import BaseModel

from app.database import get_async_session
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.crawl_job import CrawlJob
from app.schemas.user import UserResponse
from app.core.deps import get_current_admin_user, log_action

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

class UserActivationRequest(BaseModel):
    user_id: int
    is_active: bool

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Get the user to activate
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deactivating the first admin user
    if user.role == 'admin' and user.user_id == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate the first admin user"
        )
    
    # Activate the user
    user.is_active = True
    await session.commit()
    await session.refresh(user)
    
    # Log the action
    await log_action("user_activated", user.user_id, "user", current_user.user_id, 
                    {"activated_user": user.username}, request, session)
    
    return {"message": f"User {user.username} has been activated", "user": user}

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Get the user to deactivate
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow deactivating the first admin user
    if user.role == 'admin' and user.user_id == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate the first admin user"
        )
    
    # Don't allow user to deactivate themselves
    if user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Deactivate the user
    user.is_active = False
    await session.commit()
    await session.refresh(user)
    
    # Log the action
    await log_action("user_deactivated", user.user_id, "user", current_user.user_id, 
                    {"deactivated_user": user.username}, request, session)
    
    return {"message": f"User {user.username} has been deactivated", "user": user}