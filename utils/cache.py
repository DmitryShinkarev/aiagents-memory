"""Query caching utilities."""

import json
from typing import Any, Callable, Optional
from redis.asyncio import Redis


class QueryCache:
    """Cache for frequent queries using Redis."""
    
    def __init__(self, redis_client: Redis, ttl: int = 300, prefix: str = "cache"):
        """
        Initialize query cache.
        
        Args:
            redis_client: Async Redis client
            ttl: Time to live in seconds
            prefix: Key prefix
        """
        self.redis = redis_client
        self.ttl = ttl
        self.prefix = prefix
    
    def _make_key(self, cache_key: str) -> str:
        """Generate full cache key."""
        return f"{self.prefix}:{cache_key}"
    
    async def get(self, cache_key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached value or None
        """
        key = self._make_key(cache_key)
        value = await self.redis.get(key)
        
        if value:
            if isinstance(value, bytes):
                value = value.decode()
            return json.loads(value)
        
        return None
    
    async def set(self, cache_key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.
        
        Args:
            cache_key: Cache key
            value: Value to cache
            ttl: Optional custom TTL
        """
        key = self._make_key(cache_key)
        await self.redis.setex(
            key,
            ttl or self.ttl,
            json.dumps(value)
        )
    
    async def delete(self, cache_key: str):
        """Delete value from cache."""
        key = self._make_key(cache_key)
        await self.redis.delete(key)
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern."""
        full_pattern = self._make_key(pattern)
        
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=full_pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
    
    async def get_or_compute(
        self,
        cache_key: str,
        compute_func: Callable,
        ttl: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Get from cache or compute and cache.
        
        Args:
            cache_key: Cache key
            compute_func: Async function to compute value
            ttl: Optional custom TTL
            **kwargs: Arguments for compute_func
            
        Returns:
            Cached or computed value
        """
        # Try cache first
        cached = await self.get(cache_key)
        if cached is not None:
            return cached
        
        # Compute value
        result = await compute_func(**kwargs)
        
        # Cache result
        await self.set(cache_key, result, ttl=ttl)
        
        return result


