# FastAPI Async Programming

## Understanding Async in FastAPI

FastAPI is built from the ground up to support asynchronous programming, which allows handling many requests concurrently without blocking. This is crucial for I/O-intensive operations like database queries, API calls, and file operations.

## Async vs Sync Functions

### Sync Functions (Blocking)
```python
import time

def slow_operation():
    time.sleep(2)  # Blocks the entire thread
    return "Done"

@app.get("/sync")
def sync_endpoint():
    result = slow_operation()  # Blocks other requests
    return {"result": result}
```

### Async Functions (Non-Blocking)
```python
import asyncio

async def async_slow_operation():
    await asyncio.sleep(2)  # Yields control to other tasks
    return "Done"

@app.get("/async")
async def async_endpoint():
    result = await async_slow_operation()  # Other requests can be processed
    return {"result": result}
```

## Database Operations with Async

From our project's database integration:

### 1. Async Session Management
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Create async engine
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession)

async def get_async_session() -> AsyncSession:
    """Async generator for database sessions"""
    async with async_session() as session:
        try:
            yield session  # Yields control during I/O
        finally:
            await session.close()  # Async cleanup
```

### 2. Async Database Queries
From `backend/app/routers/properties.py`:

```python
@router.get("/properties")
async def get_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    session: AsyncSession = Depends(get_async_session)
):
    """Async database query with pagination"""
    
    # Build query (synchronous)
    query = select(Property).offset(skip).limit(limit)
    
    # Execute query (asynchronous I/O)
    result = await session.execute(query)
    
    # Process results (synchronous)
    properties = result.scalars().all()
    
    return properties

@router.get("/properties/{property_id}")
async def get_property_details(
    property_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Single property lookup with error handling"""
    
    query = select(Property).where(Property.p_id == property_id)
    result = await session.execute(query)
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return property_obj
```

### 3. Concurrent Database Operations
```python
import asyncio
from sqlalchemy import select

@router.get("/dashboard-data")
async def get_dashboard_data(
    session: AsyncSession = Depends(get_async_session)
):
    """Fetch multiple data sets concurrently"""
    
    # Define multiple queries
    properties_query = select(Property).limit(10)
    users_query = select(User).limit(5)
    jobs_query = select(CrawlJob).limit(5)
    
    # Execute all queries concurrently
    properties_task = session.execute(properties_query)
    users_task = session.execute(users_query)
    jobs_task = session.execute(jobs_query)
    
    # Wait for all to complete
    properties_result, users_result, jobs_result = await asyncio.gather(
        properties_task,
        users_task,
        jobs_task
    )
    
    return {
        "properties": properties_result.scalars().all(),
        "users": users_result.scalars().all(),
        "jobs": jobs_result.scalars().all()
    }
```

## Background Tasks with Celery

Our project uses Celery for background task processing:

### 1. Celery Setup
From `backend/app/celery_app.py`:

```python
from celery import Celery
import os

# Redis as message broker
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "inmobiliario_tools",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.scrapy_runner"]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
```

### 2. Async Task Runner
From `backend/app/services/job_runner.py`:

```python
from app.celery_app import celery_app
from app.tasks.scrapy_runner import run_spider_task

class JobRunner:
    @staticmethod
    async def start_crawl_job(job_id: int, session: AsyncSession):
        """Start a crawl job asynchronously"""
        
        # Get job from database
        result = await session.execute(
            select(CrawlJob).where(CrawlJob.job_id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError("Job not found")
        
        # Update job status
        job.status = "running"
        await session.commit()
        
        # Send task to Celery (async)
        task = run_spider_task.delay(
            spider_name=job.spider_name,
            job_id=job.job_id,
            target_urls=job.target_urls
        )
        
        # Store task ID for tracking
        job.celery_task_id = task.id
        await session.commit()
        
        return task.id
```

### 3. WebSocket Integration for Real-time Updates
From `backend/app/websocket.py`:

```python
from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
    
    async def send_personal_message(self, message: str, user_id: int):
        """Send message to specific user's connections"""
        if user_id in self.active_connections:
            # Send to all user's active connections
            tasks = []
            for connection in self.active_connections[user_id]:
                tasks.append(connection.send_text(message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_admins(self, message: str):
        """Broadcast message to all admin users"""
        # This would require tracking admin users
        # Implementation depends on your user management
        pass

# Global connection manager
manager = ConnectionManager()

# WebSocket endpoint in main.py
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

## HTTP Client Operations

### 1. Async HTTP Requests
```python
import aiohttp
import asyncio
from typing import List

class AsyncHTTPClient:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_url(self, url: str) -> dict:
        """Fetch single URL"""
        async with self.session.get(url) as response:
            return {
                "url": url,
                "status": response.status,
                "data": await response.text()
            }
    
    async def fetch_multiple_urls(self, urls: List[str]) -> List[dict]:
        """Fetch multiple URLs concurrently"""
        tasks = [self.fetch_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

@router.post("/check-urls")
async def check_property_urls(
    urls: List[str],
    current_user: User = Depends(get_current_user)
):
    """Check multiple property URLs concurrently"""
    
    async with AsyncHTTPClient() as client:
        results = await client.fetch_multiple_urls(urls)
    
    return {
        "checked_urls": len(urls),
        "results": results
    }
```

### 2. External API Integration
```python
import aiohttp
from typing import Optional

class PropertyPriceChecker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.property-service.com"
    
    async def get_market_price(self, location: str, property_type: str) -> Optional[float]:
        """Get market price from external API"""
        
        url = f"{self.base_url}/market-price"
        params = {
            "location": location,
            "type": property_type,
            "api_key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("estimated_price")
                    return None
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error fetching market price: {e}")
            return None

@router.get("/properties/{property_id}/market-analysis")
async def get_property_market_analysis(
    property_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get property with market analysis"""
    
    # Fetch property from database
    property_result = await session.execute(
        select(Property).where(Property.p_id == property_id)
    )
    property_obj = property_result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Fetch market price concurrently (if external API available)
    price_checker = PropertyPriceChecker(api_key="your-api-key")
    market_price_task = price_checker.get_market_price(
        location=property_obj.poblacion,
        property_type="apartment"
    )
    
    # Wait for external API (with timeout)
    try:
        market_price = await asyncio.wait_for(market_price_task, timeout=5.0)
    except asyncio.TimeoutError:
        market_price = None
    
    return {
        "property": property_obj,
        "market_analysis": {
            "estimated_market_price": market_price,
            "current_price": float(property_obj.precio) if property_obj.precio else None,
            "price_difference": (
                float(property_obj.precio) - market_price 
                if property_obj.precio and market_price 
                else None
            )
        }
    }
```

## Error Handling in Async Code

### 1. Timeout Handling
```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def timeout_context(seconds: float):
    """Context manager for operation timeouts"""
    try:
        async with asyncio.timeout(seconds):
            yield
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Operation timed out after {seconds} seconds"
        )

@router.get("/slow-operation")
async def slow_operation():
    """Endpoint with timeout protection"""
    
    async with timeout_context(10.0):  # 10 second timeout
        # Simulate slow operation
        await asyncio.sleep(5)
        return {"message": "Operation completed"}
```

### 2. Exception Handling with Multiple Async Operations
```python
@router.get("/properties/{property_id}/enhanced")
async def get_enhanced_property(
    property_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get property with enhanced data from multiple sources"""
    
    # Primary data (must succeed)
    property_result = await session.execute(
        select(Property).where(Property.p_id == property_id)
    )
    property_obj = property_result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Optional enhancements (failures are acceptable)
    async def safe_fetch_market_data():
        try:
            # Market data fetch
            return await fetch_market_data(property_obj.poblacion)
        except Exception as e:
            print(f"Market data fetch failed: {e}")
            return None
    
    async def safe_fetch_nearby_properties():
        try:
            # Nearby properties
            nearby_query = select(Property).where(
                Property.poblacion == property_obj.poblacion,
                Property.p_id != property_id
            ).limit(5)
            result = await session.execute(nearby_query)
            return result.scalars().all()
        except Exception as e:
            print(f"Nearby properties fetch failed: {e}")
            return []
    
    # Execute optional operations concurrently
    market_data, nearby_properties = await asyncio.gather(
        safe_fetch_market_data(),
        safe_fetch_nearby_properties(),
        return_exceptions=True
    )
    
    return {
        "property": property_obj,
        "market_data": market_data,
        "nearby_properties": nearby_properties
    }
```

## Performance Optimization

### 1. Connection Pooling
```python
# Database connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Number of connections to maintain
    max_overflow=10,       # Additional connections when needed
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    echo=False             # Disable SQL logging in production
)

# HTTP client connection pooling
class HTTPClientManager:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,           # Total connection pool size
                limit_per_host=30,   # Connections per host
                ttl_dns_cache=300,   # DNS cache TTL
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()

# Global HTTP client
http_client = HTTPClientManager()

# Cleanup on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await http_client.close()

app = FastAPI(lifespan=lifespan)
```

### 2. Caching with Async
```python
import aioredis
from typing import Optional

class AsyncCacheManager:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
    
    async def get_redis(self):
        if not self.redis:
            self.redis = await aioredis.from_url(self.redis_url)
        return self.redis
    
    async def get(self, key: str) -> Optional[str]:
        redis = await self.get_redis()
        return await redis.get(key)
    
    async def set(self, key: str, value: str, expire: int = 300):
        redis = await self.get_redis()
        await redis.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        redis = await self.get_redis()
        await redis.delete(key)

# Usage in routes
cache = AsyncCacheManager("redis://localhost:6379")

@router.get("/properties/{property_id}")
async def get_cached_property(
    property_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get property with caching"""
    
    cache_key = f"property:{property_id}"
    
    # Try cache first
    cached_data = await cache.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch from database
    result = await session.execute(
        select(Property).where(Property.p_id == property_id)
    )
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Cache the result
    property_data = {
        "p_id": property_obj.p_id,
        "nombre": property_obj.nombre,
        "precio": float(property_obj.precio) if property_obj.precio else None,
        "poblacion": property_obj.poblacion
    }
    
    await cache.set(cache_key, json.dumps(property_data), expire=300)
    
    return property_data
```

## Testing Async Code

```python
import pytest
import asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_async_endpoint():
    """Test async endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/properties")
        assert response.status_code == 200

@pytest.mark.asyncio  
async def test_concurrent_requests():
    """Test handling concurrent requests"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send multiple concurrent requests
        tasks = [
            client.get("/properties/1"),
            client.get("/properties/2"),
            client.get("/properties/3")
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code in [200, 404]

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

## Best Practices

1. **Use async for I/O operations** (database, HTTP requests, file operations)
2. **Don't use async for CPU-intensive tasks** (use thread pools instead)
3. **Always await async operations**
4. **Use connection pooling** for better performance
5. **Handle timeouts** for external operations
6. **Use asyncio.gather()** for concurrent operations
7. **Clean up resources** properly (sessions, connections)

## Practice Exercises

1. **Create an async file upload handler** that processes files concurrently
2. **Implement async batch processing** for property updates
3. **Build a real-time notification system** using WebSockets
4. **Create async data synchronization** between multiple external APIs

## Next Steps

In the next guide, we'll explore:
- Middleware implementation and CORS handling
- Request/response processing
- Custom middleware creation