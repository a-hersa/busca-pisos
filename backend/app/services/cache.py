import redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class CacheService:
    """Redis-based caching service for API responses and data"""
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/1")  # Use different DB than Celery
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: Union[int, timedelta] = 300) -> bool:
        """Set cache value with TTL (default 5 minutes)"""
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            serialized_data = pickle.dumps(value)
            return self.redis_client.setex(key, ttl, serialized_data)
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception:
            return 0
    
    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and parameters"""
        params = "&".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
        return f"{prefix}:{params}" if params else prefix

# Global cache instance
cache_service = CacheService()