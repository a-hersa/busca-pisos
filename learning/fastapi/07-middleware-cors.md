# FastAPI Middleware and CORS

## What is Middleware?

Middleware is code that runs before and after your route handlers. It can modify requests and responses, handle authentication, logging, CORS, and more. FastAPI middleware is based on ASGI (Asynchronous Server Gateway Interface).

## Request-Response Flow

```
Client Request → Middleware 1 → Middleware 2 → Route Handler → Middleware 2 → Middleware 1 → Client Response
```

Each middleware gets the request on the way in and the response on the way out.

## Built-in Middleware

### 1. CORS Middleware

From our project's `backend/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # Next.js frontend
        "http://127.0.0.1:3000",   # Alternative localhost
    ],
    allow_credentials=True,         # Allow cookies and authorization headers
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)
```

**CORS Configuration Options:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://yourdomain.com"
    ],
    allow_origin_regex=r"https://.*\.yourdomain\.com",  # Regex for subdomains
    allow_methods=["GET", "POST", "PUT", "DELETE"],     # Specific methods
    allow_headers=["Authorization", "Content-Type"],     # Specific headers
    allow_credentials=True,
    expose_headers=["X-Total-Count"],                   # Headers exposed to client
    max_age=600,                                        # Preflight cache time
)
```

### 2. Trusted Host Middleware

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=[
        "localhost", 
        "127.0.0.1", 
        "*.yourdomain.com"
    ]
)
```

### 3. GZIP Compression Middleware

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Custom Middleware Implementation

### 1. Cache Middleware

From our project's `backend/app/middleware/cache_middleware.py`:

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import hashlib
import json
from typing import Dict, Any
import time

class CacheMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cache_ttl: int = 300):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        # Include URL path, query parameters, and method
        key_data = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers)
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cacheable(self, request: Request) -> bool:
        """Determine if request should be cached"""
        # Only cache GET requests
        if request.method != "GET":
            return False
        
        # Skip caching for authenticated requests (has Authorization header)
        if "authorization" in request.headers:
            return False
        
        # Cache specific paths
        cacheable_paths = ["/api/properties", "/api/analytics"]
        return any(request.url.path.startswith(path) for path in cacheable_paths)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through cache middleware"""
        
        if not self._is_cacheable(request):
            # Skip caching, proceed to next middleware/route
            return await call_next(request)
        
        cache_key = self._generate_cache_key(request)
        current_time = time.time()
        
        # Check if we have a valid cached response
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if current_time - cached_item["timestamp"] < self.cache_ttl:
                # Return cached response
                return StarletteResponse(
                    content=cached_item["content"],
                    status_code=cached_item["status_code"],
                    headers=cached_item["headers"],
                    media_type=cached_item["media_type"]
                )
        
        # No valid cache, proceed with request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Store in cache
            self.cache[cache_key] = {
                "content": response_body,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type,
                "timestamp": current_time
            }
            
            # Create new response with cached body
            return StarletteResponse(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        
        return response

# Add to main.py
app.add_middleware(CacheMiddleware, cache_ttl=300)  # 5 minutes cache
```

### 2. Request Logging Middleware

```python
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api_requests")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()
        
        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.4f}s"
        )
        
        # Add processing time to response headers
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

app.add_middleware(RequestLoggingMiddleware)
```

### 3. Rate Limiting Middleware

```python
import time
from collections import defaultdict, deque
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Max calls
        self.period = period  # Time period in seconds
        self.clients = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries for this client
        client_calls = self.clients[client_ip]
        while client_calls and current_time - client_calls[0] > self.period:
            client_calls.popleft()
        
        # Check rate limit
        if len(client_calls) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.calls} calls per {self.period} seconds",
                headers={"Retry-After": str(self.period)}
            )
        
        # Add current request
        client_calls.append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.calls - len(client_calls))
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
        
        return response

# Add to main.py with different limits for different paths
app.add_middleware(RateLimitMiddleware, calls=100, period=60)  # 100 calls per minute
```

### 4. Security Headers Middleware

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

## Function-Based Middleware

Alternative to class-based middleware:

```python
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Function-based middleware example"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """Global exception handling middleware"""
    try:
        return await call_next(request)
    except Exception as e:
        # Log the error
        logger.error(f"Unhandled exception: {e}")
        
        # Return generic error response
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )
```

## Middleware with Dependencies

```python
from fastapi import Depends
from app.core.deps import get_current_user

class AuthRequiredMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, protected_paths: list = None):
        super().__init__(app)
        self.protected_paths = protected_paths or ["/api/admin"]
    
    async def dispatch(self, request: Request, call_next):
        # Check if path requires authentication
        path_requires_auth = any(
            request.url.path.startswith(path) 
            for path in self.protected_paths
        )
        
        if path_requires_auth:
            # Check for authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"message": "Authentication required"}
                )
        
        return await call_next(request)

app.add_middleware(
    AuthRequiredMiddleware, 
    protected_paths=["/api/admin", "/api/users/profile"]
)
```

## Middleware Order

Middleware executes in the order it's added (LIFO for response processing):

```python
# This order:
app.add_middleware(SecurityHeadersMiddleware)     # 1st in, 4th out
app.add_middleware(CORSMiddleware, ...)           # 2nd in, 3rd out
app.add_middleware(RateLimitMiddleware, ...)      # 3rd in, 2nd out
app.add_middleware(RequestLoggingMiddleware)      # 4th in, 1st out

# Request flow:
# Request → Security → CORS → RateLimit → Logging → Route Handler
# Response ← Security ← CORS ← RateLimit ← Logging ← Route Handler
```

## Database Integration in Middleware

```python
from app.database import get_async_session
from app.models.audit_log import AuditLog

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Log to database (only for important endpoints)
        if request.url.path.startswith("/api/admin"):
            try:
                async with get_async_session() as session:
                    audit_log = AuditLog(
                        method=request.method,
                        path=request.url.path,
                        user_agent=request.headers.get("user-agent"),
                        ip_address=request.client.host if request.client else None,
                        status_code=response.status_code,
                        response_time=time.time() - start_time
                    )
                    session.add(audit_log)
                    await session.commit()
            except Exception as e:
                # Don't fail request if audit logging fails
                logger.error(f"Audit logging failed: {e}")
        
        return response
```

## WebSocket Middleware

```python
from fastapi import WebSocket
from starlette.middleware.base import BaseHTTPMiddleware

class WebSocketLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check if this is a WebSocket connection
        if request.url.path.startswith("/ws"):
            logger.info(f"WebSocket connection attempt from {request.client.host}")
        
        return await call_next(request)

# For WebSocket-specific middleware, you can also override the WebSocket endpoint:
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    # Log connection
    logger.info(f"WebSocket connection from user {user_id}")
    
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process message
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
```

## Testing Middleware

```python
import pytest
from fastapi.testclient import TestClient

def test_cors_middleware():
    """Test CORS headers are added"""
    client = TestClient(app)
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

def test_rate_limit_middleware():
    """Test rate limiting"""
    client = TestClient(app)
    
    # Make requests up to the limit
    for i in range(100):
        response = client.get("/")
        assert response.status_code == 200
    
    # Next request should be rate limited
    response = client.get("/")
    assert response.status_code == 429

def test_security_headers():
    """Test security headers are added"""
    client = TestClient(app)
    response = client.get("/")
    
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "X-Frame-Options" in response.headers
```

## Performance Considerations

### 1. Middleware Performance
```python
# Efficient middleware - minimal processing
class EfficientMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only process what's necessary
        if request.method == "OPTIONS":
            # Skip heavy processing for preflight requests
            return await call_next(request)
        
        # Minimal processing
        response = await call_next(request)
        response.headers["X-Custom"] = "value"
        return response

# Avoid heavy operations in middleware
class InefficientMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # DON'T do this - heavy database operation
        async with get_async_session() as session:
            stats = await session.execute("SELECT COUNT(*) FROM properties")
        
        response = await call_next(request)
        return response
```

### 2. Conditional Middleware Application
```python
class ConditionalMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, apply_to_paths: list = None):
        super().__init__(app)
        self.apply_to_paths = apply_to_paths or []
    
    async def dispatch(self, request: Request, call_next):
        should_apply = any(
            request.url.path.startswith(path) 
            for path in self.apply_to_paths
        )
        
        if not should_apply:
            return await call_next(request)
        
        # Apply middleware logic only when needed
        return await self.process_request(request, call_next)

# Apply only to API routes
app.add_middleware(
    ConditionalMiddleware,
    apply_to_paths=["/api/"]
)
```

## Best Practices

1. **Order matters** - Place authentication/security middleware early
2. **Keep middleware lightweight** - Avoid heavy operations
3. **Handle exceptions gracefully** - Don't let middleware crash the app
4. **Use appropriate caching** - Cache at the right granularity
5. **Test thoroughly** - Middleware affects all requests
6. **Monitor performance** - Track middleware impact on response times
7. **Be selective** - Don't apply middleware to routes that don't need it

## Practice Exercises

1. **Create request ID middleware** that adds unique IDs to each request for tracing
2. **Implement IP whitelist middleware** for admin endpoints
3. **Build response compression middleware** for large JSON responses
4. **Create database connection health check middleware**

## Next Steps

In the next guide, we'll explore:
- WebSocket implementation for real-time features
- Connection management and broadcasting
- WebSocket authentication and security