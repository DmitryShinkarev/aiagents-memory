"""
Idempotency mechanism for ensuring operation safety.

This module provides idempotency guards and decorators to ensure that
operations can be safely retried without side effects.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from pydantic import BaseModel

from api.contracts.common import IdempotencyGuard as IdempotencyGuardModel
from storage.clients.redis_client import get_redis_client
from storage.clients.postgres_client import get_postgres_client

logger = logging.getLogger(__name__)

T = TypeVar('T')


class IdempotencyError(Exception):
    """Raised when idempotency key collision is detected."""
    pass


class IdempotencyGuard:
    """Guard for ensuring operation idempotency."""
    
    def __init__(
        self,
        operation_type: str,
        idempotency_key: str,
        ttl_days: int = 7
    ):
        self.operation_type = operation_type
        self.idempotency_key = idempotency_key
        self.ttl_days = ttl_days
        self._request_hash: Optional[str] = None
        self._cached_response: Optional[Dict[str, Any]] = None
        self._is_idempotent = False
    
    def _compute_request_hash(self, request_data: Dict[str, Any]) -> str:
        """Compute SHA256 hash of critical request fields."""
        # Extract critical fields for hashing
        critical_fields = {
            "idempotency_key": self.idempotency_key,
            "operation_type": self.operation_type,
            "requesting_agent_id": request_data.get("requesting_agent_id"),
            "entity_namespace": request_data.get("entity_namespace"),
            "entity_type": request_data.get("entity_type"),
            "entity_id": request_data.get("entity_id"),
            "user_id": request_data.get("user_id"),
            "team_id": request_data.get("team_id"),
        }
        
        # Add entity data for write operations
        if "entity_data" in request_data:
            critical_fields["entity_data"] = request_data["entity_data"]
        
        if "update_data" in request_data:
            critical_fields["update_data"] = request_data["update_data"]
        
        # Add episode data for episode operations
        if "context" in request_data:
            critical_fields["context"] = request_data["context"]
        
        if "trajectory" in request_data:
            critical_fields["trajectory"] = request_data["trajectory"]
        
        # Sort keys for consistent hashing
        sorted_data = {k: v for k, v in sorted(critical_fields.items()) if v is not None}
        
        # Convert to JSON string and hash
        json_str = json.dumps(sorted_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    async def check_idempotency(
        self,
        request_data: Dict[str, Any],
        use_redis: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Check if operation is idempotent and return cached response if available.
        
        Args:
            request_data: Request data for hash computation
            use_redis: Whether to use Redis (True) or PostgreSQL (False) for caching
            
        Returns:
            Cached response if idempotent, None otherwise
            
        Raises:
            IdempotencyError: If idempotency key collision is detected
        """
        self._request_hash = self._compute_request_hash(request_data)
        
        try:
            if use_redis:
                cached_result = await self._check_redis_cache()
            else:
                cached_result = await self._check_postgres_cache()
            
            if cached_result:
                cached_hash = cached_result.get("request_hash")
                
                if cached_hash == self._request_hash:
                    # Same request - return cached response
                    self._cached_response = cached_result.get("response")
                    self._is_idempotent = True
                    logger.info(
                        f"Idempotent operation detected: {self.operation_type}:{self.idempotency_key}"
                    )
                    return self._cached_response
                else:
                    # Different request with same key - collision!
                    raise IdempotencyError(
                        f"Idempotency key collision detected for {self.operation_type}:{self.idempotency_key}. "
                        f"Request hash mismatch: {cached_hash} != {self._request_hash}"
                    )
            
            # No cached result - proceed with operation
            return None
            
        except Exception as e:
            logger.error(f"Idempotency check failed: {e}")
            # In case of error, proceed with operation (fail open)
            return None
    
    async def _check_redis_cache(self) -> Optional[Dict[str, Any]]:
        """Check Redis cache for idempotency result."""
        try:
            redis_client = await get_redis_client()
            return await redis_client.get_idempotency(
                self.operation_type,
                self.idempotency_key
            )
        except Exception as e:
            logger.warning(f"Redis idempotency check failed: {e}")
            return None
    
    async def _check_postgres_cache(self) -> Optional[Dict[str, Any]]:
        """Check PostgreSQL cache for idempotency result."""
        try:
            postgres_client = await get_postgres_client()
            return await postgres_client.get_idempotency_result(
                self.operation_type,
                self.idempotency_key
            )
        except Exception as e:
            logger.warning(f"PostgreSQL idempotency check failed: {e}")
            return None
    
    async def store_result(
        self,
        response: Dict[str, Any],
        use_redis: bool = True
    ) -> None:
        """
        Store operation result for future idempotency checks.
        
        Args:
            response: Operation response to cache
            use_redis: Whether to use Redis (True) or PostgreSQL (False) for caching
        """
        if not self._request_hash:
            logger.warning("Cannot store idempotency result without request hash")
            return
        
        try:
            if use_redis:
                await self._store_redis_result(response)
            else:
                await self._store_postgres_result(response)
                
            logger.debug(
                f"Stored idempotency result: {self.operation_type}:{self.idempotency_key}"
            )
            
        except Exception as e:
            logger.error(f"Failed to store idempotency result: {e}")
            # Don't raise - this is not critical for operation success
    
    async def _store_redis_result(self, response: Dict[str, Any]) -> None:
        """Store result in Redis cache."""
        redis_client = await get_redis_client()
        await redis_client.store_idempotency(
            self.operation_type,
            self.idempotency_key,
            self._request_hash,
            response,
            self.ttl_days
        )
    
    async def _store_postgres_result(self, response: Dict[str, Any]) -> None:
        """Store result in PostgreSQL cache."""
        postgres_client = await get_postgres_client()
        expires_at = datetime.utcnow() + timedelta(days=self.ttl_days)
        
        await postgres_client.store_idempotency_result(
            self.operation_type,
            self.idempotency_key,
            self._request_hash,
            response,
            expires_at
        )
    
    @property
    def is_idempotent(self) -> bool:
        """Check if the current operation was idempotent."""
        return self._is_idempotent
    
    @property
    def cached_response(self) -> Optional[Dict[str, Any]]:
        """Get cached response if operation was idempotent."""
        return self._cached_response


def idempotent_operation(
    operation_type: str,
    ttl_days: int = 7,
    use_redis: bool = True,
    fail_on_collision: bool = True
):
    """
    Decorator for making operations idempotent.
    
    Args:
        operation_type: Type of operation (e.g., 'entity_create', 'episode_create')
        ttl_days: Time to live for cached results in days
        use_redis: Whether to use Redis (True) or PostgreSQL (False) for caching
        fail_on_collision: Whether to raise exception on idempotency key collision
    
    Returns:
        Decorated function that handles idempotency
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Extract idempotency key from arguments
            idempotency_key = None
            
            # Look for idempotency_key in various argument positions
            if args and hasattr(args[0], 'idempotency_key'):
                idempotency_key = args[0].idempotency_key
            elif 'idempotency_key' in kwargs:
                idempotency_key = kwargs['idempotency_key']
            elif 'request' in kwargs and hasattr(kwargs['request'], 'idempotency_key'):
                idempotency_key = kwargs['request'].idempotency_key
            
            if not idempotency_key:
                logger.warning(f"No idempotency key found for operation {operation_type}")
                return await func(*args, **kwargs)
            
            # Create idempotency guard
            guard = IdempotencyGuard(operation_type, idempotency_key, ttl_days)
            
            # Convert arguments to dict for hash computation
            request_data = {}
            if args and hasattr(args[0], 'dict'):
                request_data = args[0].dict()
            elif args and hasattr(args[0], '__dict__'):
                request_data = args[0].__dict__
            elif 'request' in kwargs and hasattr(kwargs['request'], 'dict'):
                request_data = kwargs['request'].dict()
            
            # Check idempotency
            try:
                cached_response = await guard.check_idempotency(request_data, use_redis)
                
                if cached_response is not None:
                    # Return cached response
                    logger.info(f"Returning cached response for {operation_type}:{idempotency_key}")
                    return cached_response
                
            except IdempotencyError as e:
                if fail_on_collision:
                    logger.error(f"Idempotency collision: {e}")
                    raise
                else:
                    logger.warning(f"Idempotency collision (ignored): {e}")
            
            # Execute operation
            try:
                result = await func(*args, **kwargs)
                
                # Store result for future idempotency checks
                if hasattr(result, 'dict'):
                    response_data = result.dict()
                elif hasattr(result, '__dict__'):
                    response_data = result.__dict__
                else:
                    response_data = {"result": result}
                
                await guard.store_result(response_data, use_redis)
                
                # Mark response as idempotent if it was cached
                if hasattr(result, 'idempotent'):
                    result.idempotent = guard.is_idempotent
                elif hasattr(result, '__dict__'):
                    result.__dict__['idempotent'] = guard.is_idempotent
                
                return result
                
            except Exception as e:
                logger.error(f"Operation failed: {e}")
                raise
        
        return wrapper
    return decorator


class IdempotencyManager:
    """Manager for idempotency operations across the system."""
    
    def __init__(self):
        self._active_guards: Dict[str, IdempotencyGuard] = {}
    
    async def create_guard(
        self,
        operation_type: str,
        idempotency_key: str,
        ttl_days: int = 7
    ) -> IdempotencyGuard:
        """Create a new idempotency guard."""
        guard = IdempotencyGuard(operation_type, idempotency_key, ttl_days)
        self._active_guards[idempotency_key] = guard
        return guard
    
    async def cleanup_expired_guards(self) -> int:
        """Clean up expired idempotency records."""
        try:
            # Clean up Redis cache
            redis_client = await get_redis_client()
            # Redis TTL handles expiration automatically
            
            # Clean up PostgreSQL cache
            postgres_client = await get_postgres_client()
            deleted_count = await postgres_client.cleanup_expired_idempotency()
            
            logger.info(f"Cleaned up {deleted_count} expired idempotency records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired idempotency records: {e}")
            return 0
    
    def get_guard(self, idempotency_key: str) -> Optional[IdempotencyGuard]:
        """Get active guard by idempotency key."""
        return self._active_guards.get(idempotency_key)
    
    def remove_guard(self, idempotency_key: str) -> None:
        """Remove guard from active guards."""
        self._active_guards.pop(idempotency_key, None)


# Global idempotency manager
_idempotency_manager: Optional[IdempotencyManager] = None


def get_idempotency_manager() -> IdempotencyManager:
    """Get global idempotency manager instance."""
    global _idempotency_manager
    
    if _idempotency_manager is None:
        _idempotency_manager = IdempotencyManager()
    
    return _idempotency_manager


# Convenience functions for common operations

async def check_entity_create_idempotency(
    request_data: Dict[str, Any],
    use_redis: bool = True
) -> Optional[Dict[str, Any]]:
    """Check idempotency for entity creation."""
    guard = IdempotencyGuard("entity_create", request_data["idempotency_key"])
    return await guard.check_idempotency(request_data, use_redis)


async def check_episode_create_idempotency(
    request_data: Dict[str, Any],
    use_redis: bool = True
) -> Optional[Dict[str, Any]]:
    """Check idempotency for episode creation."""
    guard = IdempotencyGuard("episode_create", request_data["idempotency_key"])
    return await guard.check_idempotency(request_data, use_redis)


async def store_operation_result(
    operation_type: str,
    idempotency_key: str,
    request_hash: str,
    response: Dict[str, Any],
    ttl_days: int = 7,
    use_redis: bool = True
) -> None:
    """Store operation result for idempotency."""
    guard = IdempotencyGuard(operation_type, idempotency_key, ttl_days)
    guard._request_hash = request_hash
    await guard.store_result(response, use_redis)
