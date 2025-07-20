from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_session
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.security import verify_token

security = HTTPBearer(auto_error=True)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    username = payload.get("sub")
    
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def log_action(
    action: str,
    user_id: int,
    resource_type: str = None,
    resource_id: int = None,
    details: dict = None,
    request: Request = None,
    session: AsyncSession = Depends(get_async_session)
):
    # Queue audit logging asynchronously to avoid blocking the response
    from app.tasks.audit_logger import log_audit_async
    
    audit_data = {
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details,
        "ip_address": request.client.host if request else None,
        "user_agent": request.headers.get("user-agent") if request else None
    }
    
    # Fire and forget - don't block the API response
    log_audit_async.delay(audit_data)