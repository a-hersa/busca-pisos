# FastAPI Authentication and Security

## Overview

This guide covers implementing authentication and security in FastAPI using JWT tokens, password hashing, and role-based access control as demonstrated in our busca-pisos project.

## Core Security Components

### 1. Password Hashing

From `backend/app/core/security.py`:

```python
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import os

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """Hash a plain password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def verify_token(token: str):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
            
        return username
    except jwt.PyJWTError:
        return None
```

### 2. User Authentication Schema

From `backend/app/schemas/user.py`:

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str

class UserResponse(BaseModel):
    """Schema for user data in responses (no password)"""
    user_id: int
    username: str
    email: str
    role: str
    is_active: bool
    email_confirmed: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class TokenData(BaseModel):
    """Schema for token payload data"""
    username: Optional[str] = None
```

## Authentication Routes

From `backend/app/routers/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.database import get_async_session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Register a new user"""
    
    # Check if username already exists
    existing_user = await session.execute(
        select(User).where(User.username == user_data.username)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await session.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="user"  # Default role
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user

@router.post("/login", response_model=Token)
async def login_user(
    credentials: UserLogin,
    session: AsyncSession = Depends(get_async_session)
):
    """Authenticate user and return JWT token"""
    
    # Find user by username
    result = await session.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Update last login
    user.last_login = func.now()
    await session.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        "user": user
    }

@router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout user (client should discard token)"""
    # In a stateless JWT system, logout is handled client-side
    # You could implement token blacklisting here if needed
    return {"message": "Successfully logged out"}
```

## Authentication Dependencies

From `backend/app/core/deps.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.database import get_async_session
from app.models.user import User
from app.core.security import SECRET_KEY, ALGORITHM

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Extract current user from JWT token
    This dependency can be used to protect routes
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Get user from database
    result = await session.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    return user

async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure current user has admin privileges
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

async def get_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure user account is active and email is confirmed
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    if not current_user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please confirm your email address"
        )
    
    return current_user
```

## Protecting Routes

### 1. Basic Authentication
```python
@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile - requires authentication"""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role
    }
```

### 2. Admin-Only Routes
```python
@router.delete("/properties/{property_id}")
async def delete_property(
    property_id: int,
    admin_user: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Delete property - admin only"""
    # Admin-only logic here
    pass
```

### 3. Owner or Admin Access
```python
async def get_job_owner_or_admin(
    job_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Ensure user owns the job or is admin"""
    
    result = await session.execute(
        select(CrawlJob).where(CrawlJob.job_id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user owns the job or is admin
    if job.created_by != current_user.user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return job

@router.get("/jobs/{job_id}")
async def get_job(
    job = Depends(get_job_owner_or_admin)
):
    """Get job details - owner or admin only"""
    return job
```

## Role-Based Access Control

### 1. Role Checking Decorator
```python
from functools import wraps
from typing import List

def require_roles(allowed_roles: List[str]):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires one of roles: {', '.join(allowed_roles)}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@router.get("/admin/stats")
@require_roles(["admin", "moderator"])
async def get_admin_stats(
    current_user: User = Depends(get_current_user)
):
    return {"stats": "admin_data"}
```

### 2. Permission System
```python
class Permission:
    """Define permissions"""
    CREATE_PROPERTY = "create:property"
    DELETE_PROPERTY = "delete:property"
    VIEW_ALL_JOBS = "view:all_jobs"
    MANAGE_USERS = "manage:users"

# Role-based permissions
ROLE_PERMISSIONS = {
    "user": [Permission.CREATE_PROPERTY],
    "admin": [
        Permission.CREATE_PROPERTY,
        Permission.DELETE_PROPERTY,
        Permission.VIEW_ALL_JOBS,
        Permission.MANAGE_USERS
    ]
}

def check_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission"""
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions

def require_permission(permission: str):
    """Dependency to require specific permission"""
    async def permission_dependency(
        current_user: User = Depends(get_current_user)
    ):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_dependency

# Usage
@router.delete("/properties/{property_id}")
async def delete_property(
    property_id: int,
    user: User = Depends(require_permission(Permission.DELETE_PROPERTY))
):
    # Delete property
    pass
```

## Email Confirmation System

From our project's email confirmation implementation:

```python
import secrets
from datetime import datetime, timedelta

async def send_confirmation_email(user: User, session: AsyncSession):
    """Generate confirmation token and send email"""
    
    # Generate secure token
    confirmation_token = secrets.token_urlsafe(32)
    
    # Set expiration (24 hours)
    expiration = datetime.utcnow() + timedelta(hours=24)
    
    # Update user with token
    user.email_confirmation_token = confirmation_token
    user.email_confirmation_expires = expiration
    
    await session.commit()
    
    # Send email (implementation depends on your email service)
    confirmation_url = f"http://localhost:3000/confirm-email?token={confirmation_token}"
    await send_email(
        to=user.email,
        subject="Confirm your email",
        body=f"Click here to confirm: {confirmation_url}"
    )

@router.post("/confirm-email")
async def confirm_email(
    token: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Confirm user email with token"""
    
    result = await session.execute(
        select(User).where(
            User.email_confirmation_token == token,
            User.email_confirmation_expires > datetime.utcnow()
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired confirmation token"
        )
    
    # Confirm email
    user.email_confirmed = True
    user.email_confirmation_token = None
    user.email_confirmation_expires = None
    
    await session.commit()
    
    return {"message": "Email confirmed successfully"}
```

## Security Best Practices

### 1. Environment Variables
```python
import os

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-change-in-production")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://...")

# Never commit secrets to version control
# Use strong, random secret keys in production
```

### 2. Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(request: Request, credentials: UserLogin):
    # Login logic
    pass
```

### 3. Input Validation
```python
from pydantic import validator
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    
    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
```

## Testing Authentication

```python
import pytest
from fastapi.testclient import TestClient

def test_register_user(client: TestClient):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "password" not in data  # Password should not be in response

def test_login_user(client: TestClient):
    # First register a user
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com", 
        "password": "TestPassword123"
    })
    
    # Then login
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "TestPassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_protected_route(client: TestClient):
    # Try without authentication
    response = client.get("/profile")
    assert response.status_code == 401
    
    # Login and get token
    login_response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "TestPassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try with authentication
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/profile", headers=headers)
    assert response.status_code == 200
```

## Practice Exercises

1. **Implement password reset** with email tokens
2. **Add two-factor authentication** using TOTP
3. **Create API key authentication** for service-to-service calls
4. **Implement session management** with refresh tokens
5. **Add OAuth2 integration** with Google or GitHub

## Next Steps

In the next guides, we'll explore:
- Async programming patterns in FastAPI
- Middleware and request processing
- WebSocket implementation for real-time features