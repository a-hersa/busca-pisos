#!/usr/bin/env python3
"""
Script to create a test user for development
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.security import get_password_hash

async def create_test_user():
    # Database connection
    DATABASE_URL = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER', 'inmobiliario_user')}:{os.getenv('POSTGRES_PASSWORD', 'inmobiliario_pass')}@{os.getenv('POSTGRES_HOST', 'localhost')}:5432/{os.getenv('POSTGRES_DB', 'inmobiliario_db')}"
    
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if test user already exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == 'testuser'))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print("Test user already exists!")
            return
        
        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=get_password_hash('testpass123'),
            role='user',
            is_active=True
        )
        
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        print(f"Test user created successfully!")
        print(f"Username: testuser")
        print(f"Password: testpass123")
        print(f"Email: test@example.com")
        print(f"User ID: {test_user.user_id}")

if __name__ == "__main__":
    asyncio.run(create_test_user())