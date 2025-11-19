"""
Redis client for working memory and caching.

This module provides an async Redis client with connection pooling,
health checks, and specialized methods for memory operations.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from config.settings import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client with connection pooling and health checks."""
    
    def __init__(
        self,
        url: str,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30
    ):
        self.url = url
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval
        
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._health_status = "unknown"
        self._last_health_check = None
        
    async def connect(self) -> None:
        """Initialize Redis connection pool and client."""
        try:
            self._pool = ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout,
                health_check_interval=self.health_check_interval
            )
            
            self._client = Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            self._health_status = "healthy"
            self._last_health_check = datetime.utcnow()
            
            logger.info("Redis client connected successfully")
            
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis client disconnected")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection."""
        try:
            if not self._client:
                return {
                    "status": "unhealthy",
                    "error": "Client not connected",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Test basic operations
            start_time = datetime.utcnow()
            await self._client.ping()
            await self._client.set("health_check", "ok", ex=10)
            await self._client.get("health_check")
            await self._client.delete("health_check")
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Get Redis info
            info = await self._client.info()
            
            self._health_status = "healthy"
            self._last_health_check = datetime.utcnow()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "timestamp": self._last_health_check.isoformat()
            }
            
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @property
    def is_healthy(self) -> bool:
        """Check if Redis client is healthy."""
        return self._health_status == "healthy"
    
    # Basic Redis operations
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.get(key)
    
    async def set(
        self,
        key: str,
        value: Union[str, bytes, int, float],
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """Set key-value pair with optional expiration."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
    
    async def delete(self, *keys: str) -> int:
        """Delete keys."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.delete(*keys)
    
    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.exists(*keys)
    
    async def expire(self, key: str, time: int) -> bool:
        """Set expiration time for key."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.expire(key, time)
    
    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.ttl(key)
    
    # JSON operations
    
    async def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set JSON value."""
        json_value = json.dumps(value, default=str)
        return await self.set(key, json_value, ex=ex)
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value."""
        value = await self.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode JSON for key {key}")
            return None
    
    # Hash operations
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set hash fields."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.hset(name, mapping=mapping)
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.hget(name, key)
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.hgetall(name)
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.hdel(name, *keys)
    
    # List operations
    
    async def lpush(self, name: str, *values: Any) -> int:
        """Push values to left of list."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.lpush(name, *values)
    
    async def rpush(self, name: str, *values: Any) -> int:
        """Push values to right of list."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.rpush(name, *values)
    
    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """Get list range."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.lrange(name, start, end)
    
    async def ltrim(self, name: str, start: int, end: int) -> bool:
        """Trim list to range."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.ltrim(name, start, end)
    
    # Set operations
    
    async def sadd(self, name: str, *values: Any) -> int:
        """Add values to set."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.sadd(name, *values)
    
    async def smembers(self, name: str) -> set:
        """Get all set members."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.smembers(name)
    
    async def srem(self, name: str, *values: Any) -> int:
        """Remove values from set."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.srem(name, *values)
    
    # Pub/Sub operations
    
    async def publish(self, channel: str, message: Union[str, bytes, int, float]) -> int:
        """Publish message to channel."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.publish(channel, message)
    
    async def subscribe(self, *channels: str):
        """Subscribe to channels."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return self._client.pubsub().subscribe(*channels)
    
    # Memory-specific operations
    
    async def store_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Store session data with TTL."""
        key = f"session:{session_id}"
        return await self.set_json(key, session_data, ex=ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        key = f"session:{session_id}"
        return await self.get_json(key)
    
    async def extend_session_ttl(self, session_id: str, ttl: int = 3600) -> bool:
        """Extend session TTL."""
        key = f"session:{session_id}"
        return await self.expire(key, ttl)
    
    async def cache_retrieval(
        self,
        query_hash: str,
        result: Any,
        ttl: int = 300
    ) -> bool:
        """Cache RAG retrieval result."""
        key = f"cache:rag:{query_hash}"
        return await self.set_json(key, result, ex=ttl)
    
    async def get_cached_retrieval(self, query_hash: str) -> Optional[Any]:
        """Get cached RAG retrieval result."""
        key = f"cache:rag:{query_hash}"
        return await self.get_json(key)
    
    async def store_idempotency(
        self,
        operation_type: str,
        idempotency_key: str,
        request_hash: str,
        response: Any,
        ttl_days: int = 7
    ) -> bool:
        """Store idempotency result."""
        key = f"idempotency:{operation_type}:{idempotency_key}"
        ttl_seconds = ttl_days * 24 * 60 * 60
        
        data = {
            "request_hash": request_hash,
            "response": response,
            "stored_at": datetime.utcnow().isoformat()
        }
        
        return await self.set_json(key, data, ex=ttl_seconds)
    
    async def get_idempotency(
        self,
        operation_type: str,
        idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get idempotency result."""
        key = f"idempotency:{operation_type}:{idempotency_key}"
        return await self.get_json(key)
    
    # Batch operations
    
    async def mget(self, *keys: str) -> List[Optional[str]]:
        """Get multiple values."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.mget(*keys)
    
    async def mset(self, mapping: Dict[str, Any]) -> bool:
        """Set multiple key-value pairs."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return await self._client.mset(mapping)
    
    # Pipeline operations
    
    async def pipeline(self):
        """Create Redis pipeline for batch operations."""
        if not self._client:
            raise RuntimeError("Redis client not connected")
        return self._client.pipeline()


# Global Redis client instance
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Get or create global Redis client instance."""
    global _redis_client
    
    if _redis_client is None:
        settings = get_settings()
        _redis_client = RedisClient(
            url=settings.redis_url,
            max_connections=settings.redis_max_connections
        )
        await _redis_client.connect()
    
    return _redis_client


async def close_redis_client():
    """Close global Redis client."""
    global _redis_client
    
    if _redis_client:
        await _redis_client.disconnect()
        _redis_client = None
