# FastAPI Dependency Injection System

## What is Dependency Injection?

Dependency Injection (DI) is a design pattern where objects receive their dependencies from external sources rather than creating them internally. FastAPI has a powerful DI system that helps with:

- Code reusability
- Testing
- Security
- Database connections
- Validation
- Authentication

## Basic Dependency Concept

```python
from fastapi import Depends

def get_database():
    db = create_database_connection()
    try:
        yield db
    finally:
        db.close()

@app.get("/items")
async def get_items(db = Depends(get_database)):
    # db is automatically injected
    return db.query("SELECT * FROM items")
```

## Real Examples from Our Project

### 1. Database Session Dependency

From `backend/app/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Create async engine
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncSession:
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

Used in routes:
```python
@router.get("/properties")
async def get_properties(
    session: AsyncSession = Depends(get_async_session)
):
    # session is automatically injected and managed
    result = await session.execute(select(Property))
    return result.scalars().all()
```

### 2. Authentication Dependency

From `backend/app/core/deps.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """Extract and validate user from JWT token"""
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        username: str = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
            
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Get user from database
    result = await session.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user
```

Used to protect routes:
```python
@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role
    }
```

### 3. Admin-Only Dependency

```python
async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.delete("/properties/{property_id}")
async def delete_property(
    property_id: int,
    admin_user: User = Depends(get_admin_user)
):
    # Only admins can access this endpoint
    pass
```

## Dependency Chains

Dependencies can depend on other dependencies:

```python
# Level 1: Database session
async def get_session():
    # Database connection logic
    pass

# Level 2: Current user (needs database)
async def get_current_user(session = Depends(get_session)):
    # User authentication logic
    pass

# Level 3: Admin user (needs current user)
async def get_admin_user(user = Depends(get_current_user)):
    # Admin verification logic
    pass

# Route uses the full chain
@app.get("/admin-only")
async def admin_route(admin = Depends(get_admin_user)):
    # FastAPI automatically resolves the entire dependency chain
    return {"message": "Admin access granted"}
```

## Class-Based Dependencies

You can also use classes as dependencies:

```python
class DatabaseManager:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session
    
    async def get_properties(self, limit: int = 10):
        result = await self.session.execute(
            select(Property).limit(limit)
        )
        return result.scalars().all()

@router.get("/properties")
async def get_properties(
    db_manager: DatabaseManager = Depends(DatabaseManager)
):
    return await db_manager.get_properties()
```

## Dependency Overrides (Testing)

FastAPI allows overriding dependencies for testing:

```python
# Test database
def get_test_db():
    return create_test_database()

# Override in tests
app.dependency_overrides[get_async_session] = get_test_db

def test_get_properties():
    # This will use test database instead
    response = client.get("/properties")
    assert response.status_code == 200
```

## Query Parameter Dependencies

From our analytics router:

```python
from typing import Optional

class PropertyFilters:
    def __init__(
        self,
        poblacion: Optional[str] = Query(None, description="Filter by location"),
        precio_min: Optional[int] = Query(None, ge=0, description="Minimum price"),
        precio_max: Optional[int] = Query(None, ge=0, description="Maximum price"),
        limit: int = Query(100, le=1000, description="Results limit")
    ):
        self.poblacion = poblacion
        self.precio_min = precio_min
        self.precio_max = precio_max
        self.limit = limit
    
    def apply_to_query(self, query):
        if self.poblacion:
            query = query.where(Property.poblacion.ilike(f"%{self.poblacion}%"))
        if self.precio_min:
            query = query.where(Property.precio >= self.precio_min)
        if self.precio_max:
            query = query.where(Property.precio <= self.precio_max)
        return query.limit(self.limit)

@router.get("/properties/search")
async def search_properties(
    filters: PropertyFilters = Depends(PropertyFilters),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(Property)
    query = filters.apply_to_query(query)
    result = await session.execute(query)
    return result.scalars().all()
```

## Global Dependencies

Apply dependencies to entire routers or applications:

```python
# Apply to all routes in router
router = APIRouter(dependencies=[Depends(get_current_user)])

# Apply to entire app
app = FastAPI(dependencies=[Depends(some_global_dependency)])
```

## Caching Dependencies

Dependencies are cached per request by default:

```python
def expensive_computation():
    print("This runs only once per request")
    return complex_calculation()

@app.get("/endpoint1")
async def endpoint1(result = Depends(expensive_computation)):
    return {"result": result}

@app.get("/endpoint2") 
async def endpoint2(result = Depends(expensive_computation)):
    # Same instance as endpoint1 if called in same request
    return {"result": result}
```

To disable caching:
```python
@app.get("/endpoint")
async def endpoint(result = Depends(expensive_computation, use_cache=False)):
    # Always runs fresh
    return {"result": result}
```

## Error Handling in Dependencies

```python
async def validate_api_key(api_key: str = Header(None)):
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not is_valid_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return api_key

@router.get("/protected")
async def protected_endpoint(api_key = Depends(validate_api_key)):
    return {"message": "Access granted", "api_key": api_key}
```

## Practice Exercises

1. **Create a logging dependency** that logs all requests with timestamp and user info

2. **Build a pagination dependency** that handles skip/limit parameters with validation

3. **Implement rate limiting** using a dependency that checks request frequency

4. **Create a cache dependency** that stores and retrieves frequently accessed data

## Common Patterns

### Repository Pattern
```python
class PropertyRepository:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session
    
    async def get_by_id(self, property_id: int):
        # Database logic here
        pass
    
    async def create(self, property_data):
        # Create logic here
        pass

@router.get("/{property_id}")
async def get_property(
    property_id: int,
    repo: PropertyRepository = Depends(PropertyRepository)
):
    return await repo.get_by_id(property_id)
```

## Next Steps

In the next guide, we'll explore:
- Database integration with SQLAlchemy
- Pydantic models for validation
- Async database operations