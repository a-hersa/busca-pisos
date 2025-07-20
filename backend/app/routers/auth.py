from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from app.database import get_async_session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    generate_email_confirmation_token, hash_confirmation_token, 
    verify_confirmation_token, get_confirmation_token_expiry
)
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
    from sqlalchemy import func
    result_count = await session.execute(select(func.count(User.user_id)))
    user_count = result_count.scalar()
    is_first_user = user_count == 0
    
    # Create new user - FORCE EXPLICIT VALUES
    hashed_password = get_password_hash(user_data.password)
    
    if is_first_user:
        # First user: admin, active, email confirmed
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            role='admin',
            is_active=True,
            email_confirmed=True
        )
    else:
        # Subsequent users: regular user, inactive, need email confirmation
        confirmation_token = generate_email_confirmation_token()
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            role='user',
            is_active=False,
            email_confirmed=False,
            email_confirmation_token=hash_confirmation_token(confirmation_token),
            email_confirmation_expires=get_confirmation_token_expiry()
        )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    # Send confirmation email for non-first users
    if not is_first_user:
        from app.services.notifications import EmailService
        email_service = EmailService()
        try:
            email_service.send_email_confirmation(
                user_email=new_user.email,
                username=new_user.username,
                confirmation_token=confirmation_token
            )
        except Exception as e:
            print(f"Failed to send confirmation email: {e}")
            # Don't fail registration if email fails
    
    # Log registration
    await log_action("user_register", new_user.user_id, "user", new_user.user_id, 
                    {"email": user_data.email, "email_confirmation_required": not is_first_user}, request, session)
    
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
    
    if not user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please confirm your email address before logging in"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await session.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Log login
    await log_action("user_login", user.user_id, "user", user.user_id, 
                    {"login_time": datetime.now(timezone.utc).isoformat()}, request, session)
    
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
                    {"logout_time": datetime.now(timezone.utc).isoformat()}, request, session)
    
    return {"message": "Successfully logged out"}

@router.post("/confirm-email/{token}")
async def confirm_email(
    token: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    # Find user by confirmation token
    result = await session.execute(
        select(User).where(User.email_confirmation_token.isnot(None))
    )
    users = result.scalars().all()
    
    # Find matching user by verifying token
    user = None
    for u in users:
        if verify_confirmation_token(token, u.email_confirmation_token):
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token"
        )
    
    # Check if token has expired
    if user.email_confirmation_expires and user.email_confirmation_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation token has expired"
        )
    
    # Confirm email and activate user
    user.email_confirmed = True
    user.is_active = True
    user.email_confirmation_token = None
    user.email_confirmation_expires = None
    
    await session.commit()
    await session.refresh(user)
    
    # Log confirmation
    await log_action("email_confirmed", user.user_id, "user", user.user_id, 
                    {"email": user.email}, request, session)
    
    return {"message": "Email confirmed successfully", "user": user}

from pydantic import BaseModel

class EmailRequest(BaseModel):
    email: str

@router.post("/resend-confirmation")
async def resend_confirmation(
    email_request: EmailRequest,
    request: Request,
    session: AsyncSession = Depends(get_async_session)
):
    # Find user by email
    result = await session.execute(select(User).where(User.email == email_request.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already confirmed"
        )
    
    # Generate new confirmation token
    token = generate_email_confirmation_token()
    user.email_confirmation_token = hash_confirmation_token(token)
    user.email_confirmation_expires = get_confirmation_token_expiry()
    
    await session.commit()
    
    # Send confirmation email
    from app.services.notifications import EmailService
    email_service = EmailService()
    try:
        email_service.send_email_confirmation(
            user_email=user.email,
            username=user.username,
            confirmation_token=token
        )
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send confirmation email"
        )
    
    # Log action
    await log_action("confirmation_resent", user.user_id, "user", user.user_id, 
                    {"email": user.email}, request, session)
    
    return {"message": "Confirmation email sent"}