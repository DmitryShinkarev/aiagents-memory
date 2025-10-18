"""
Working Memory Service - Short-term operational memory.

This service manages short-term memory for active sessions, including
conversation context, temporary variables, and cached retrieval results.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from ...storage.clients.redis_client import get_redis_client
from ...config.settings import get_settings

logger = logging.getLogger(__name__)


class WorkingMemoryService:
    """Service for managing working memory in Redis."""
    
    def __init__(self):
        self._redis_client = None
        self._settings = get_settings()
    
    async def _get_redis_client(self):
        """Get Redis client instance."""
        if self._redis_client is None:
            self._redis_client = await get_redis_client()
        return self._redis_client
    
    # Session management
    
    async def store_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Store session data with TTL.
        
        Args:
            session_id: Unique session identifier
            session_data: Session data to store
            ttl: Time to live in seconds (defaults to settings)
            
        Returns:
            True if successful
        """
        try:
            redis_client = await self._get_redis_client()
            
            if ttl is None:
                ttl = self._settings.redis_session_ttl
            
            # Add metadata
            session_data["_metadata"] = {
                "stored_at": datetime.utcnow().isoformat(),
                "ttl": ttl
            }
            
            success = await redis_client.store_session(session_id, session_data, ttl)
            
            if success:
                logger.debug(f"Stored session {session_id} with TTL {ttl}s")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store session {session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        try:
            redis_client = await self._get_redis_client()
            session_data = await redis_client.get_session(session_id)
            
            if session_data:
                logger.debug(f"Retrieved session {session_id}")
            
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def extend_session_ttl(
        self,
        session_id: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Extend session TTL.
        
        Args:
            session_id: Session identifier
            ttl: New TTL in seconds (defaults to settings)
            
        Returns:
            True if successful
        """
        try:
            redis_client = await self._get_redis_client()
            
            if ttl is None:
                ttl = self._settings.redis_session_ttl
            
            success = await redis_client.extend_session_ttl(session_id, ttl)
            
            if success:
                logger.debug(f"Extended session {session_id} TTL to {ttl}s")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to extend session {session_id} TTL: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            redis_client = await self._get_redis_client()
            key = f"session:{session_id}"
            deleted_count = await redis_client.delete(key)
            
            success = deleted_count > 0
            
            if success:
                logger.debug(f"Deleted session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    # Context management
    
    async def get_context(
        self,
        agent_id: str,
        session_id: Optional[str] = None,
        include_history: bool = True,
        max_messages: int = 50
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for an agent.
        
        Args:
            agent_id: Agent identifier
            session_id: Optional session identifier
            include_history: Whether to include conversation history
            max_messages: Maximum number of messages to include
            
        Returns:
            Context dictionary
        """
        try:
            context = {
                "agent_id": agent_id,
                "session_id": session_id,
                "current_message": None,
                "conversation_history": [],
                "retrieved_knowledge": [],
                "temporary_variables": {},
                "agent_state": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Get session data if session_id provided
            if session_id:
                session_data = await self.get_session(session_id)
                if session_data:
                    context.update({
                        "current_message": session_data.get("current_message"),
                        "conversation_history": session_data.get("conversation_history", []),
                        "retrieved_knowledge": session_data.get("retrieved_knowledge", []),
                        "temporary_variables": session_data.get("temporary_variables", {}),
                        "agent_state": session_data.get("agent_state", {})
                    })
            
            # Limit conversation history
            if include_history and context["conversation_history"]:
                context["conversation_history"] = context["conversation_history"][-max_messages:]
            
            logger.debug(f"Retrieved context for agent {agent_id}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context for agent {agent_id}: {e}")
            return {"agent_id": agent_id, "error": str(e)}
    
    async def update_context(
        self,
        agent_id: str,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update context for an agent session.
        
        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            updates: Updates to apply
            
        Returns:
            True if successful
        """
        try:
            # Get current session data
            session_data = await self.get_session(session_id)
            if not session_data:
                session_data = {
                    "agent_id": agent_id,
                    "current_message": None,
                    "conversation_history": [],
                    "retrieved_knowledge": [],
                    "temporary_variables": {},
                    "agent_state": {}
                }
            
            # Apply updates
            for key, value in updates.items():
                if key in ["conversation_history", "retrieved_knowledge"]:
                    # Append to lists
                    if key not in session_data:
                        session_data[key] = []
                    session_data[key].extend(value if isinstance(value, list) else [value])
                elif key in ["temporary_variables", "agent_state"]:
                    # Merge dictionaries
                    if key not in session_data:
                        session_data[key] = {}
                    session_data[key].update(value if isinstance(value, dict) else {})
                else:
                    # Direct assignment
                    session_data[key] = value
            
            # Store updated session
            success = await self.store_session(session_id, session_data)
            
            if success:
                logger.debug(f"Updated context for agent {agent_id}, session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update context for agent {agent_id}: {e}")
            return False
    
    # RAG caching
    
    async def cache_retrieval(
        self,
        query_hash: str,
        result: Any,
        ttl: int = 300
    ) -> bool:
        """
        Cache RAG retrieval result.
        
        Args:
            query_hash: Hash of the query
            result: Retrieval result to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            redis_client = await self._get_redis_client()
            success = await redis_client.cache_retrieval(query_hash, result, ttl)
            
            if success:
                logger.debug(f"Cached retrieval result for query {query_hash}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cache retrieval result: {e}")
            return False
    
    async def get_cached_retrieval(self, query_hash: str) -> Optional[Any]:
        """
        Get cached RAG retrieval result.
        
        Args:
            query_hash: Hash of the query
            
        Returns:
            Cached result or None if not found
        """
        try:
            redis_client = await self._get_redis_client()
            result = await redis_client.get_cached_retrieval(query_hash)
            
            if result:
                logger.debug(f"Retrieved cached result for query {query_hash}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get cached retrieval result: {e}")
            return None
    
    # Pub/Sub coordination
    
    async def publish_event(
        self,
        channel: str,
        message: Union[str, Dict[str, Any]]
    ) -> int:
        """
        Publish event to channel.
        
        Args:
            channel: Channel name
            message: Message to publish
            
        Returns:
            Number of subscribers that received the message
        """
        try:
            redis_client = await self._get_redis_client()
            
            if isinstance(message, dict):
                message = json.dumps(message, default=str)
            
            subscribers = await redis_client.publish(channel, message)
            
            logger.debug(f"Published event to channel {channel}, {subscribers} subscribers")
            return subscribers
            
        except Exception as e:
            logger.error(f"Failed to publish event to channel {channel}: {e}")
            return 0
    
    async def subscribe_events(
        self,
        channels: List[str],
        timeout: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Subscribe to events from channels.
        
        Args:
            channels: List of channel names
            timeout: Timeout in seconds (None for no timeout)
            
        Returns:
            List of received messages
        """
        try:
            redis_client = await self._get_redis_client()
            pubsub = await redis_client.subscribe(*channels)
            
            messages = []
            start_time = datetime.utcnow()
            
            try:
                while True:
                    if timeout and (datetime.utcnow() - start_time).seconds > timeout:
                        break
                    
                    message = await asyncio.wait_for(pubsub.get_message(), timeout=1.0)
                    if message and message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            messages.append({
                                "channel": message["channel"].decode(),
                                "data": data,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        except json.JSONDecodeError:
                            messages.append({
                                "channel": message["channel"].decode(),
                                "data": message["data"].decode(),
                                "timestamp": datetime.utcnow().isoformat()
                            })
                    
                    if len(messages) >= 100:  # Limit to prevent memory issues
                        break
                        
            finally:
                await pubsub.unsubscribe()
            
            logger.debug(f"Received {len(messages)} messages from channels {channels}")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            return []
    
    # Agent coordination
    
    async def coordinate_agents(
        self,
        task_id: str,
        message: Dict[str, Any],
        target_agents: Optional[List[str]] = None
    ) -> int:
        """
        Coordinate agents through pub/sub.
        
        Args:
            task_id: Task identifier
            message: Message to send
            target_agents: Optional list of target agents
            
        Returns:
            Number of agents that received the message
        """
        try:
            channel = f"task:{task_id}"
            
            # Add metadata
            message["_metadata"] = {
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
                "target_agents": target_agents
            }
            
            subscribers = await self.publish_event(channel, message)
            
            logger.info(f"Coordinated {subscribers} agents for task {task_id}")
            return subscribers
            
        except Exception as e:
            logger.error(f"Failed to coordinate agents for task {task_id}: {e}")
            return 0
    
    async def get_task_results(
        self,
        task_id: str,
        timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get results from task execution.
        
        Args:
            task_id: Task identifier
            timeout: Timeout in seconds
            
        Returns:
            List of task results
        """
        try:
            results_channel = f"results:{task_id}"
            results = await self.subscribe_events([results_channel], timeout)
            
            logger.debug(f"Retrieved {len(results)} results for task {task_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get task results for {task_id}: {e}")
            return []
    
    # Health and monitoring
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on working memory service."""
        try:
            redis_client = await self._get_redis_client()
            redis_health = await redis_client.health_check()
            
            return {
                "service": "working_memory",
                "status": "healthy" if redis_health["status"] == "healthy" else "unhealthy",
                "redis": redis_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Working memory health check failed: {e}")
            return {
                "service": "working_memory",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get working memory metrics."""
        try:
            redis_client = await self._get_redis_client()
            
            # Get session count (approximate)
            session_keys = await redis_client.execute("KEYS", "session:*")
            session_count = len(session_keys) if session_keys else 0
            
            # Get cache hit rate (approximate)
            cache_keys = await redis_client.execute("KEYS", "cache:rag:*")
            cache_count = len(cache_keys) if cache_keys else 0
            
            return {
                "active_sessions": session_count,
                "cached_retrievals": cache_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get working memory metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
