# FastAPI Database Integration with SQLAlchemy

## Overview

This guide covers how FastAPI integrates with databases using SQLAlchemy, specifically focusing on async operations as implemented in our busca-pisos project.

## Database Setup

### 1. Database Configuration

From `backend/app/database.py`:

```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Environment configuration
DATABASE_URL = os.getenv("DATABASE_URL", 
    "postgresql+asyncpg://user:password@localhost/dbname"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL statements (disable in production)
    pool_size=20,
    max_overflow=0,
)

# Session factory
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for models
class Base(DeclarativeBase):
    pass

async def get_async_session() -> AsyncSession:
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database - create tables if they don't exist"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

### 2. Database Models

From `backend/app/models/property.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric
from sqlalchemy.sql import func
from app.database import Base

class Property(Base):
    __tablename__ = "propiedades"
    
    # Primary key
    p_id = Column(Integer, primary_key=True, index=True)
    
    # Property details
    nombre = Column(String(500), nullable=False)
    precio = Column(Numeric(12, 2), index=True)  # Index for filtering
    metros = Column(String(50))
    poblacion = Column(String(200), index=True)  # Index for searching
    url = Column(Text, unique=True, nullable=False)
    
    # Status and timestamps
    estatus = Column(String(50), default="activo", index=True)
    fecha_updated = Column(DateTime(timezone=True), 
                          server_default=func.now(), 
                          onupdate=func.now())
    fecha_crawl = Column(DateTime(timezone=True), 
                        server_default=func.now())
    
    def __repr__(self):
        return f"<Property(id={self.p_id}, nombre='{self.nombre[:50]}...')>"
```

User model from `backend/app/models/user.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User metadata
    role = Column(String(20), default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    email_confirmed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Email confirmation
    email_confirmation_token = Column(String(100))
    email_confirmation_expires = Column(DateTime(timezone=True))
```

## Pydantic Schemas for Validation

From `backend/app/schemas/property.py`:

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal

class PropertyBase(BaseModel):
    """Base schema with common fields"""
    nombre: str = Field(..., min_length=1, max_length=500)
    precio: Optional[Decimal] = Field(None, ge=0)
    metros: Optional[str] = Field(None, max_length=50)
    poblacion: Optional[str] = Field(None, max_length=200)

class PropertyCreate(PropertyBase):
    """Schema for creating new properties"""
    url: str = Field(..., min_length=1)
    estatus: str = Field(default="activo")

class PropertyUpdate(BaseModel):
    """Schema for updating properties (all fields optional)"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=500)
    precio: Optional[Decimal] = Field(None, ge=0)
    metros: Optional[str] = Field(None, max_length=50)
    poblacion: Optional[str] = Field(None, max_length=200)
    estatus: Optional[str] = None

class PropertyResponse(PropertyBase):
    """Schema for API responses"""
    model_config = ConfigDict(from_attributes=True)
    
    p_id: int
    url: str
    estatus: str
    fecha_updated: datetime
    fecha_crawl: datetime
```

## Database Operations in Routes

### 1. Reading Data

From `backend/app/routers/properties.py`:

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.database import get_async_session
from app.models.property import Property

router = APIRouter()

@router.get("/", response_model=List[PropertyResponse])
async def get_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    session: AsyncSession = Depends(get_async_session)
):
    """Get paginated list of properties"""
    
    # Build query with pagination
    query = select(Property).offset(skip).limit(limit)
    result = await session.execute(query)
    
    # Convert to list
    properties = result.scalars().all()
    return properties

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get single property by ID"""
    
    query = select(Property).where(Property.p_id == property_id)
    result = await session.execute(query)
    
    property_obj = result.scalar_one_or_none()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return property_obj
```

### 2. Complex Queries with Filters

```python
@router.get("/search", response_model=List[PropertyResponse])
async def search_properties(
    poblacion: Optional[str] = Query(None),
    precio_min: Optional[int] = Query(None, ge=0),
    precio_max: Optional[int] = Query(None, ge=0),
    metros_min: Optional[int] = Query(None, ge=0),
    session: AsyncSession = Depends(get_async_session)
):
    """Search properties with multiple filters"""
    
    # Start with base query
    query = select(Property).where(Property.estatus == "activo")
    
    # Add filters conditionally
    if poblacion:
        query = query.where(Property.poblacion.ilike(f"%{poblacion}%"))
    
    if precio_min is not None:
        query = query.where(Property.precio >= precio_min)
    
    if precio_max is not None:
        query = query.where(Property.precio <= precio_max)
    
    if metros_min is not None:
        # Convert string metros to integer for comparison
        query = query.where(
            and_(
                Property.metros.regexp_match(r'^\d+$'),  # Only numeric values
                Property.metros.cast(Integer) >= metros_min
            )
        )
    
    # Execute with limit
    query = query.limit(100)
    result = await session.execute(query)
    
    return result.scalars().all()
```

### 3. Creating Data

```python
@router.post("/", response_model=PropertyResponse, status_code=201)
async def create_property(
    property_data: PropertyCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create new property"""
    
    # Check if URL already exists
    existing_query = select(Property).where(Property.url == property_data.url)
    existing = await session.execute(existing_query)
    
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="Property with this URL already exists"
        )
    
    # Create new property
    property_obj = Property(**property_data.model_dump())
    
    session.add(property_obj)
    await session.commit()
    await session.refresh(property_obj)  # Get updated data from DB
    
    return property_obj
```

### 4. Updating Data

```python
@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update existing property"""
    
    # Find existing property
    query = select(Property).where(Property.p_id == property_id)
    result = await session.execute(query)
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Update only provided fields
    update_data = property_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(property_obj, field, value)
    
    await session.commit()
    await session.refresh(property_obj)
    
    return property_obj
```

### 5. Deleting Data

```python
@router.delete("/{property_id}", status_code=204)
async def delete_property(
    property_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_admin_user)  # Admin only
):
    """Delete property (admin only)"""
    
    query = select(Property).where(Property.p_id == property_id)
    result = await session.execute(query)
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    await session.delete(property_obj)
    await session.commit()
    
    # Returns 204 No Content (empty response)
```

## Advanced Database Operations

### 1. Aggregation Queries

From `backend/app/routers/analytics.py`:

```python
from sqlalchemy import text, func, case

@router.get("/stats")
async def get_property_stats(
    session: AsyncSession = Depends(get_async_session)
):
    """Get property statistics using aggregation"""
    
    # Count by location
    location_query = select(
        Property.poblacion,
        func.count().label('count'),
        func.avg(Property.precio).label('avg_price'),
        func.min(Property.precio).label('min_price'),
        func.max(Property.precio).label('max_price')
    ).where(
        Property.poblacion.is_not(None)
    ).group_by(
        Property.poblacion
    ).order_by(
        func.count().desc()
    ).limit(10)
    
    result = await session.execute(location_query)
    location_stats = [
        {
            "location": row.poblacion,
            "count": row.count,
            "avg_price": float(row.avg_price) if row.avg_price else 0,
            "min_price": float(row.min_price) if row.min_price else 0,
            "max_price": float(row.max_price) if row.max_price else 0,
        }
        for row in result
    ]
    
    return {"location_stats": location_stats}
```

### 2. Raw SQL Queries

```python
@router.get("/complex-analytics")
async def complex_analytics(
    session: AsyncSession = Depends(get_async_session)
):
    """Complex analytics using raw SQL"""
    
    # Use text() for complex SQL
    query = text("""
        WITH monthly_data AS (
            SELECT 
                DATE_TRUNC('month', fecha_crawl) as month,
                COUNT(*) as properties_count,
                AVG(precio) as avg_price,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY precio) as median_price
            FROM propiedades 
            WHERE fecha_crawl >= NOW() - INTERVAL '6 months'
                AND precio IS NOT NULL
            GROUP BY DATE_TRUNC('month', fecha_crawl)
        )
        SELECT * FROM monthly_data
        ORDER BY month DESC
    """)
    
    result = await session.execute(query)
    
    return [
        {
            "month": row.month.isoformat(),
            "properties_count": row.properties_count,
            "avg_price": float(row.avg_price),
            "median_price": float(row.median_price)
        }
        for row in result
    ]
```

### 3. Relationships (Joins)

```python
# In models - define relationships
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"
    
    job_id = Column(Integer, primary_key=True)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Relationship
    creator = relationship("User", back_populates="jobs")

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True)
    
    # Back reference
    jobs = relationship("CrawlJob", back_populates="creator")

# In routes - use joins
@router.get("/jobs-with-users")
async def get_jobs_with_users(
    session: AsyncSession = Depends(get_async_session)
):
    """Get jobs with user information using joins"""
    
    query = select(CrawlJob, User).join(
        User, CrawlJob.created_by == User.user_id
    )
    
    result = await session.execute(query)
    
    return [
        {
            "job_id": job.job_id,
            "job_name": job.job_name,
            "creator_username": user.username,
            "creator_email": user.email
        }
        for job, user in result
    ]
```

## Database Performance Tips

### 1. Use Indexes
```python
# In model definitions
poblacion = Column(String(200), index=True)  # Single column index
precio = Column(Numeric(12, 2), index=True)

# Composite indexes
__table_args__ = (
    Index('idx_poblacion_precio', 'poblacion', 'precio'),
)
```

### 2. Optimize Queries
```python
# Use select_related equivalent with options
from sqlalchemy.orm import selectinload

query = select(CrawlJob).options(
    selectinload(CrawlJob.creator)  # Eager load relationship
)
```

### 3. Connection Pooling
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Number of connections to maintain
    max_overflow=10,       # Additional connections allowed
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

## Error Handling

```python
from sqlalchemy.exc import IntegrityError

@router.post("/properties")
async def create_property(
    property_data: PropertyCreate,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        property_obj = Property(**property_data.model_dump())
        session.add(property_obj)
        await session.commit()
        await session.refresh(property_obj)
        return property_obj
        
    except IntegrityError as e:
        await session.rollback()
        if "duplicate key" in str(e.orig):
            raise HTTPException(
                status_code=400,
                detail="Property with this URL already exists"
            )
        raise HTTPException(status_code=400, detail="Database error")
```

## Practice Exercises

1. **Create a favorites system** with many-to-many relationships between users and properties

2. **Implement full-text search** using PostgreSQL's text search features

3. **Add audit logging** that tracks all changes to properties with timestamps

4. **Create aggregation endpoints** for property statistics by location, price range, etc.

## Next Steps

In the next guide, we'll explore:
- Authentication and security implementation
- JWT tokens and password hashing
- Role-based access control