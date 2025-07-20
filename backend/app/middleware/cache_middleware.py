from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.cache import cache_service
import json
import hashlib

class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for caching GET API responses"""
    
    def __init__(self, app, cache_ttl: int = 300):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cacheable_paths = [
            "/api/properties",
            "/api/analytics"
            # Removed "/api/jobs" for instant updates
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests for specific paths
        if request.method != "GET" or not any(request.url.path.startswith(path) for path in self.cacheable_paths):
            return await call_next(request)
        
        # Generate cache key from URL and query params
        cache_key = self._generate_cache_key(request)
        
        # Try to get cached response
        cached_response = await cache_service.get(cache_key)
        if cached_response:
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
                media_type=cached_response["media_type"]
            )
        
        # Get fresh response
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Store in cache
            cache_data = {
                "content": response_body.decode(),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            }
            
            await cache_service.set(cache_key, cache_data, self.cache_ttl)
            
            # Return response with body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type
            )
        
        return response
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request URL and params"""
        url_parts = f"{request.url.path}?{request.url.query}"
        return f"api_cache:{hashlib.md5(url_parts.encode()).hexdigest()}"