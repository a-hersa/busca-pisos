from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.database import get_async_session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.deps import get_current_user, log_action

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    # Check if user already exists
    result = await session.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Check if this is the first user (admin)
    result_count = await session.execute(select(User))
    existing_users = result_count.scalars().all()
    is_first_user = len(existing_users) == 0
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role='admin' if is_first_user else 'user',
        is_active=True  # First user doesn't need email confirmation
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    # Log registration
    await log_action("user_register", new_user.user_id, "user", new_user.user_id, 
                    {"email": user_data.email}, request, session)
    
    return new_user

@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    # Find user
    result = await session.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await session.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Log login
    await log_action("user_login", user.user_id, "user", user.user_id, 
                    {"login_time": datetime.utcnow().isoformat()}, request, session)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Log logout
    await log_action("user_logout", current_user.user_id, "user", current_user.user_id, 
                    {"logout_time": datetime.utcnow().isoformat()}, request, session)
    
    return {"message": "Successfully logged out"}