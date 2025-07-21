# FastAPI Testing, Validation, and Error Handling

## Testing FastAPI Applications

FastAPI provides excellent testing support through integration with pytest and the TestClient from Starlette.

## Basic Testing Setup

### 1. Test Configuration

Create `backend/tests/conftest.py`:

```python
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_async_session
from app.models.user import User
from app.models.property import Property
from app.core.security import hash_password

# Test database URL (SQLite in memory for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestAsyncSession = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_test_session():
    """Test database session dependency override"""
    async with TestAsyncSession() as session:
        try:
            yield session
        finally:
            await session.close()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_db():
    """Create and drop test database for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
def client(test_db):
    """FastAPI test client with database override"""
    app.dependency_overrides[get_async_session] = get_test_session
    
    with TestClient(app) as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(client):
    """Create a test user"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    
    return response.json()

@pytest.fixture
async def admin_user(client):
    """Create an admin user"""
    async with TestAsyncSession() as session:
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=hash_password("adminpass123"),
            role="admin",
            is_active=True,
            email_confirmed=True
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        
        return admin

@pytest.fixture
async def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
```

### 2. Testing Authentication

Create `backend/tests/test_auth.py`:

```python
import pytest
from fastapi.testclient import TestClient

def test_register_user(client: TestClient):
    """Test user registration"""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepassword123"
    }
    
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "password" not in data  # Password should not be returned
    assert data["role"] == "user"  # Default role
    assert data["is_active"] is True

def test_register_duplicate_username(client: TestClient, test_user):
    """Test registration with duplicate username"""
    user_data = {
        "username": "testuser",  # Already exists
        "email": "different@example.com",
        "password": "password123"
    }
    
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

def test_login_success(client: TestClient, test_user):
    """Test successful login"""
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["user"]["username"] == "testuser"

def test_login_invalid_credentials(client: TestClient, test_user):
    """Test login with invalid credentials"""
    login_data = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    
    response = client.post("/auth/login", json=login_data)
    
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]

def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user"""
    login_data = {
        "username": "nonexistent",
        "password": "password"
    }
    
    response = client.post("/auth/login", json=login_data)
    
    assert response.status_code == 401

def test_protected_route_without_token(client: TestClient):
    """Test accessing protected route without authentication"""
    response = client.get("/api/users/profile")
    
    assert response.status_code == 401

def test_protected_route_with_token(client: TestClient, auth_headers):
    """Test accessing protected route with valid token"""
    response = client.get("/api/users/profile", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"

def test_invalid_token(client: TestClient):
    """Test with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/users/profile", headers=headers)
    
    assert response.status_code == 401
```

### 3. Testing API Endpoints

Create `backend/tests/test_properties.py`:

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
async def sample_property():
    """Sample property data for testing"""
    return {
        "nombre": "Test Property",
        "precio": 150000.50,
        "metros": "85",
        "poblacion": "Test City",
        "url": "https://test.com/property/123",
        "estatus": "activo"
    }

def test_get_properties_empty(client: TestClient):
    """Test getting properties when database is empty"""
    response = client.get("/api/properties/")
    
    assert response.status_code == 200
    assert response.json() == []

def test_create_property(client: TestClient, auth_headers, sample_property):
    """Test creating a new property"""
    response = client.post(
        "/api/properties/", 
        json=sample_property,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == sample_property["nombre"]
    assert data["precio"] == sample_property["precio"]
    assert data["url"] == sample_property["url"]
    assert "p_id" in data
    assert "fecha_updated" in data

def test_create_property_unauthorized(client: TestClient, sample_property):
    """Test creating property without authentication"""
    response = client.post("/api/properties/", json=sample_property)
    
    assert response.status_code == 401

def test_create_property_duplicate_url(client: TestClient, auth_headers, sample_property):
    """Test creating property with duplicate URL"""
    # Create first property
    client.post("/api/properties/", json=sample_property, headers=auth_headers)
    
    # Try to create duplicate
    response = client.post("/api/properties/", json=sample_property, headers=auth_headers)
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_get_property_by_id(client: TestClient, auth_headers, sample_property):
    """Test getting property by ID"""
    # Create property first
    create_response = client.post(
        "/api/properties/", 
        json=sample_property,
        headers=auth_headers
    )
    property_id = create_response.json()["p_id"]
    
    # Get property by ID
    response = client.get(f"/api/properties/{property_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["p_id"] == property_id
    assert data["nombre"] == sample_property["nombre"]

def test_get_nonexistent_property(client: TestClient):
    """Test getting non-existent property"""
    response = client.get("/api/properties/999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_update_property(client: TestClient, auth_headers, sample_property):
    """Test updating property"""
    # Create property first
    create_response = client.post(
        "/api/properties/", 
        json=sample_property,
        headers=auth_headers
    )
    property_id = create_response.json()["p_id"]
    
    # Update property
    update_data = {"precio": 175000.00, "estatus": "vendido"}
    response = client.put(
        f"/api/properties/{property_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["precio"] == 175000.00
    assert data["estatus"] == "vendido"
    assert data["nombre"] == sample_property["nombre"]  # Unchanged

def test_search_properties(client: TestClient, auth_headers):
    """Test property search functionality"""
    # Create test properties
    properties = [
        {
            "nombre": "Madrid Apartment",
            "precio": 200000,
            "poblacion": "Madrid",
            "url": "https://test.com/madrid/1",
        },
        {
            "nombre": "Barcelona House", 
            "precio": 350000,
            "poblacion": "Barcelona",
            "url": "https://test.com/barcelona/1",
        },
    ]
    
    for prop in properties:
        client.post("/api/properties/", json=prop, headers=auth_headers)
    
    # Search by location
    response = client.get("/api/properties/search?poblacion=Madrid")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["poblacion"] == "Madrid"
    
    # Search by price range
    response = client.get("/api/properties/search?precio_min=300000")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["precio"] >= 300000

def test_pagination(client: TestClient, auth_headers):
    """Test property pagination"""
    # Create multiple properties
    for i in range(15):
        property_data = {
            "nombre": f"Property {i}",
            "url": f"https://test.com/property/{i}",
            "precio": 100000 + i * 1000
        }
        client.post("/api/properties/", json=property_data, headers=auth_headers)
    
    # Test first page
    response = client.get("/api/properties/?skip=0&limit=10")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 10
    
    # Test second page
    response = client.get("/api/properties/?skip=10&limit=10")
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 5  # Remaining properties
```

### 4. Testing Async Operations

Create `backend/tests/test_async.py`:

```python
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    """Test async endpoint using httpx AsyncClient"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling multiple concurrent requests"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create multiple concurrent requests
        tasks = [
            ac.get("/health"),
            ac.get("/"),
            ac.get("/health"),
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

@pytest.mark.asyncio
async def test_database_concurrent_operations(test_db):
    """Test concurrent database operations"""
    from app.database import TestAsyncSession
    from app.models.property import Property
    
    async def create_property(name: str):
        async with TestAsyncSession() as session:
            prop = Property(
                nombre=name,
                url=f"https://test.com/{name}",
                precio=100000
            )
            session.add(prop)
            await session.commit()
            await session.refresh(prop)
            return prop
    
    # Create properties concurrently
    tasks = [
        create_property(f"property_{i}")
        for i in range(5)
    ]
    
    properties = await asyncio.gather(*tasks)
    
    assert len(properties) == 5
    for prop in properties:
        assert prop.p_id is not None
```

## Validation with Pydantic

### 1. Advanced Pydantic Models

```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import re

class PropertyCreate(BaseModel):
    """Property creation with advanced validation"""
    nombre: str = Field(..., min_length=5, max_length=500, description="Property title")
    precio: Optional[Decimal] = Field(None, ge=0, le=10_000_000, description="Price in euros")
    metros: Optional[str] = Field(None, max_length=50, description="Square meters")
    poblacion: Optional[str] = Field(None, max_length=200, description="Location/City")
    url: str = Field(..., min_length=10, description="Property URL")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v
    
    @validator('metros')
    def validate_metros(cls, v):
        """Validate metros field - should be numeric or contain numeric value"""
        if v is None:
            return v
        
        # Extract numeric value from string like "85 m²" or "85m2"
        numeric_match = re.search(r'(\d+(?:\.\d+)?)', v)
        if not numeric_match:
            raise ValueError('Metros must contain a numeric value')
        
        numeric_value = float(numeric_match.group(1))
        if numeric_value <= 0 or numeric_value > 10000:
            raise ValueError('Metros must be between 0 and 10000')
        
        return v
    
    @validator('poblacion')
    def validate_poblacion(cls, v):
        """Validate location name"""
        if v is None:
            return v
        
        # Remove extra whitespace
        v = ' '.join(v.split())
        
        # Check for minimum length
        if len(v) < 2:
            raise ValueError('Location must be at least 2 characters')
        
        return v
    
    @root_validator
    def validate_property_data(cls, values):
        """Cross-field validation"""
        precio = values.get('precio')
        poblacion = values.get('poblacion', '').lower()
        
        # Expensive properties should have location
        if precio and precio > 500000 and not poblacion:
            raise ValueError('Expensive properties must specify location')
        
        # Madrid properties price validation
        if 'madrid' in poblacion and precio and precio < 100000:
            raise ValueError('Madrid properties are typically above 100,000€')
        
        return values

class PropertyUpdate(BaseModel):
    """Property update with optional fields"""
    nombre: Optional[str] = Field(None, min_length=5, max_length=500)
    precio: Optional[Decimal] = Field(None, ge=0, le=10_000_000)
    metros: Optional[str] = Field(None, max_length=50)
    poblacion: Optional[str] = Field(None, max_length=200)
    estatus: Optional[str] = Field(None, regex=r'^(activo|inactivo|vendido)$')
    
    @validator('estatus')
    def validate_status(cls, v):
        """Validate property status"""
        if v is None:
            return v
        
        valid_statuses = ['activo', 'inactivo', 'vendido']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        
        return v.lower()

class PropertyFilter(BaseModel):
    """Property filtering with validation"""
    poblacion: Optional[str] = None
    precio_min: Optional[int] = Field(None, ge=0)
    precio_max: Optional[int] = Field(None, ge=0)
    metros_min: Optional[int] = Field(None, ge=10)
    metros_max: Optional[int] = Field(None, le=1000)
    
    @root_validator
    def validate_price_range(cls, values):
        """Ensure price_min <= price_max"""
        precio_min = values.get('precio_min')
        precio_max = values.get('precio_max')
        
        if precio_min and precio_max and precio_min > precio_max:
            raise ValueError('precio_min cannot be greater than precio_max')
        
        return values
    
    @root_validator
    def validate_metros_range(cls, values):
        """Ensure metros_min <= metros_max"""
        metros_min = values.get('metros_min')
        metros_max = values.get('metros_max')
        
        if metros_min and metros_max and metros_min > metros_max:
            raise ValueError('metros_min cannot be greater than metros_max')
        
        return values

class BulkPropertyCreate(BaseModel):
    """Bulk property creation with validation"""
    properties: List[PropertyCreate] = Field(..., min_items=1, max_items=100)
    
    @validator('properties')
    def validate_unique_urls(cls, v):
        """Ensure all URLs in bulk operation are unique"""
        urls = [prop.url for prop in v]
        if len(urls) != len(set(urls)):
            raise ValueError('All property URLs must be unique')
        return v
```

### 2. Custom Validators

```python
from pydantic import BaseModel, validator
import requests
from urllib.parse import urlparse

class PropertyWithValidation(BaseModel):
    url: str
    precio: Optional[Decimal] = None
    
    @validator('url')
    def validate_url_accessibility(cls, v):
        """Validate that URL is accessible (optional validation)"""
        # Note: This makes HTTP requests, so use cautiously in production
        try:
            parsed = urlparse(v)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError('Invalid URL format')
            
            # Optional: Check if URL is accessible
            # response = requests.head(v, timeout=5)
            # if response.status_code >= 400:
            #     raise ValueError('URL is not accessible')
            
        except Exception as e:
            raise ValueError(f'URL validation failed: {str(e)}')
        
        return v
    
    @validator('precio')
    def validate_reasonable_price(cls, v):
        """Validate that price is reasonable"""
        if v is None:
            return v
        
        # Check for reasonable price ranges
        if v < 1000:
            raise ValueError('Price seems too low (minimum 1,000€)')
        if v > 50_000_000:
            raise ValueError('Price seems too high (maximum 50M€)')
        
        return v

class UserRegistration(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username requirements"""
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        
        # Check for prohibited usernames
        prohibited = ['admin', 'root', 'system', 'api']
        if v.lower() in prohibited:
            raise ValueError('This username is not allowed')
        
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @root_validator
    def validate_password_confirmation(cls, values):
        """Validate password confirmation matches"""
        password = values.get('password')
        confirm_password = values.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValueError('Passwords do not match')
        
        return values
```

### 3. Testing Validation

```python
import pytest
from pydantic import ValidationError
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyFilter

def test_property_create_valid():
    """Test valid property creation"""
    data = {
        "nombre": "Beautiful apartment in Madrid",
        "precio": 250000.50,
        "metros": "85 m²",
        "poblacion": "Madrid",
        "url": "https://idealista.com/inmueble/12345"
    }
    
    property_obj = PropertyCreate(**data)
    assert property_obj.nombre == data["nombre"]
    assert property_obj.precio == data["precio"]

def test_property_create_invalid_url():
    """Test property creation with invalid URL"""
    data = {
        "nombre": "Test property",
        "url": "not-a-valid-url"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        PropertyCreate(**data)
    
    errors = exc_info.value.errors()
    assert any(error['field'] == 'url' for error in errors)

def test_property_create_invalid_price():
    """Test property creation with invalid price"""
    data = {
        "nombre": "Test property",
        "url": "https://example.com/property",
        "precio": -1000  # Negative price
    }
    
    with pytest.raises(ValidationError) as exc_info:
        PropertyCreate(**data)
    
    errors = exc_info.value.errors()
    assert any(error['field'] == 'precio' for error in errors)

def test_property_filter_validation():
    """Test property filter validation"""
    # Valid filter
    filter_obj = PropertyFilter(
        precio_min=100000,
        precio_max=500000,
        metros_min=50,
        metros_max=200
    )
    assert filter_obj.precio_min == 100000
    
    # Invalid filter - min > max
    with pytest.raises(ValidationError) as exc_info:
        PropertyFilter(precio_min=500000, precio_max=100000)
    
    assert 'precio_min cannot be greater than precio_max' in str(exc_info.value)

def test_cross_field_validation():
    """Test cross-field validation"""
    # Expensive property without location should fail
    with pytest.raises(ValidationError) as exc_info:
        PropertyCreate(
            nombre="Luxury apartment",
            precio=600000,  # Expensive
            url="https://example.com/luxury",
            # poblacion not provided
        )
    
    assert 'Expensive properties must specify location' in str(exc_info.value)

def test_custom_validator_edge_cases():
    """Test custom validators with edge cases"""
    # Test metros validation
    valid_metros = ["85", "85 m²", "85m2", "85.5"]
    for metros in valid_metros:
        property_obj = PropertyCreate(
            nombre="Test property",
            url="https://example.com/test",
            metros=metros
        )
        assert property_obj.metros == metros
    
    # Invalid metros
    invalid_metros = ["abc", "", "0", "15000"]
    for metros in invalid_metros:
        with pytest.raises(ValidationError):
            PropertyCreate(
                nombre="Test property",
                url="https://example.com/test",
                metros=metros
            )
```

## Error Handling

### 1. Custom Exception Classes

```python
from fastapi import HTTPException, status

class PropertyNotFoundError(HTTPException):
    def __init__(self, property_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property with ID {property_id} not found"
        )

class DuplicatePropertyError(HTTPException):
    def __init__(self, url: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property with URL '{url}' already exists"
        )

class InsufficientPermissionsError(HTTPException):
    def __init__(self, required_permission: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{required_permission}' required"
        )

class RateLimitExceededError(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )
```

### 2. Global Exception Handlers

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The provided data is invalid",
            "details": exc.errors()
        }
    )

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    logger.error(f"Database integrity error: {exc}")
    
    if "duplicate key" in str(exc.orig).lower():
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Duplicate Entry",
                "message": "A record with this information already exists"
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "A database error occurred"
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors"""
    logger.warning(f"Value error on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Invalid Value",
            "message": str(exc)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error on {request.url}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )
```

### 3. Testing Error Handling

```python
def test_validation_error_response(client: TestClient):
    """Test validation error response format"""
    invalid_data = {
        "nombre": "",  # Too short
        "precio": -1000,  # Invalid price
        "url": "invalid-url"  # Invalid URL
    }
    
    response = client.post("/api/properties/", json=invalid_data)
    
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert "details" in data
    assert len(data["details"]) >= 3  # At least 3 validation errors

def test_duplicate_entry_error(client: TestClient, auth_headers):
    """Test duplicate entry error handling"""
    property_data = {
        "nombre": "Test Property",
        "url": "https://test.com/unique",
        "precio": 100000
    }
    
    # Create first property
    response1 = client.post("/api/properties/", json=property_data, headers=auth_headers)
    assert response1.status_code == 201
    
    # Try to create duplicate
    response2 = client.post("/api/properties/", json=property_data, headers=auth_headers)
    assert response2.status_code == 409  # Conflict
    assert "duplicate" in response2.json()["message"].lower()

def test_not_found_error(client: TestClient):
    """Test 404 error handling"""
    response = client.get("/api/properties/99999")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_permission_error(client: TestClient, test_user):
    """Test permission denied error"""
    # Try to access admin endpoint as regular user
    headers = {"Authorization": f"Bearer {get_user_token(test_user)}"}
    response = client.get("/api/admin/users", headers=headers)
    
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()
```

## Performance Testing

```python
import pytest
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_concurrent_requests_performance(client: TestClient):
    """Test API performance under concurrent load"""
    def make_request():
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        return response.status_code, end_time - start_time
    
    # Make 50 concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(50)]
        results = [future.result() for future in as_completed(futures)]
    
    # All requests should succeed
    status_codes = [result[0] for result in results]
    assert all(code == 200 for code in status_codes)
    
    # Check average response time
    response_times = [result[1] for result in results]
    avg_response_time = sum(response_times) / len(response_times)
    assert avg_response_time < 1.0  # Average should be under 1 second

@pytest.mark.asyncio
async def test_database_query_performance(test_db):
    """Test database query performance"""
    from app.database import TestAsyncSession
    from app.models.property import Property
    from sqlalchemy import select
    
    # Create test data
    async with TestAsyncSession() as session:
        properties = [
            Property(
                nombre=f"Property {i}",
                url=f"https://test.com/property/{i}",
                precio=100000 + i * 1000
            )
            for i in range(1000)
        ]
        session.add_all(properties)
        await session.commit()
    
    # Test query performance
    start_time = time.time()
    
    async with TestAsyncSession() as session:
        result = await session.execute(select(Property).limit(100))
        properties = result.scalars().all()
    
    end_time = time.time()
    query_time = end_time - start_time
    
    assert len(properties) == 100
    assert query_time < 0.5  # Query should complete in under 500ms
```

## Best Practices

1. **Use fixtures effectively** - Create reusable test data and setup
2. **Test edge cases** - Invalid inputs, boundary conditions, empty data
3. **Mock external dependencies** - Don't depend on external services in tests
4. **Test both success and failure paths** - Ensure error handling works
5. **Use async tests for async code** - Properly test async operations
6. **Validate error responses** - Ensure proper error messages and status codes
7. **Test authentication and authorization** - Security is critical
8. **Performance testing** - Ensure API can handle expected load
9. **Clean up test data** - Use database transactions or cleanup fixtures

## Practice Exercises

1. **Create integration tests** for the complete job creation and execution flow
2. **Add performance benchmarks** for critical API endpoints
3. **Implement property validation** that checks external APIs for data accuracy
4. **Create stress tests** for WebSocket connections
5. **Add monitoring and health check endpoints** with comprehensive tests

## Conclusion

You now have comprehensive learning materials covering all major aspects of FastAPI development, using real examples from the inmobiliario-tools project. These guides cover:

1. **FastAPI Basics** - Application setup and core concepts
2. **Routing and Endpoints** - Creating and organizing API routes
3. **Dependency Injection** - Managing dependencies and authentication
4. **Database Integration** - SQLAlchemy with async operations
5. **Authentication and Security** - JWT tokens and role-based access
6. **Async Programming** - Non-blocking operations and concurrency
7. **Middleware and CORS** - Request/response processing
8. **WebSockets** - Real-time communication
9. **Testing and Validation** - Comprehensive testing strategies

Each guide includes practical examples, best practices, and exercises to help you master FastAPI development.