"""Redis-based working memory implementation."""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from redis.asyncio import Redis

from config.memory.working_memory import WorkingMemoryConfig


# Lua script for atomic message addition with trimming
TRIM_AND_ADD_MESSAGE = """
local stream_key = KEYS[1]
local maxlen = tonumber(ARGV[1])
local message_data = ARGV[2]
local ttl = tonumber(ARGV[3])

-- Add message with MAXLEN
local msg_id = redis.call('XADD', stream_key, 'MAXLEN', '~', maxlen, '*', 'data', message_data)

-- Set TTL
redis.call('EXPIRE', stream_key, ttl)

return msg_id
"""


class RedisWorkingMemory:
    """Working memory implementation using Redis."""
    
    def __init__(self, redis_client: Redis, agent_id: str, config: Optional[WorkingMemoryConfig] = None):
        """
        Initialize working memory.
        
        Args:
            redis_client: Async Redis client
            agent_id: Unique agent identifier
            config: Memory configuration (uses defaults if None)
        """
        self.redis = redis_client
        self.agent_id = agent_id
        self.config = config or WorkingMemoryConfig()
        
        # Register Lua script
        self._add_message_script = None
    
    async def _ensure_script_loaded(self):
        """Ensure Lua script is registered."""
        if self._add_message_script is None:
            self._add_message_script = self.redis.register_script(TRIM_AND_ADD_MESSAGE)
    
    # Redis key patterns
    def _session_key(self, session_id: str) -> str:
        """Get session key prefix."""
        return f"agent:{self.agent_id}:session:{session_id}"
    
    def _messages_key(self, session_id: str) -> str:
        """Get messages stream key."""
        return f"{self._session_key(session_id)}:messages"
    
    def _context_key(self, session_id: str) -> str:
        """Get context hash key."""
        return f"agent:{self.agent_id}:context:{session_id}"
    
    def _temp_vars_key(self, session_id: str, var_name: str) -> str:
        """Get temporary variable key."""
        return f"agent:{self.agent_id}:vars:{session_id}:{var_name}"
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Add a message to working memory.
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Message ID in the stream
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        stream_key = self._messages_key(session_id)
        
        # Use Lua script for atomic operation
        await self._ensure_script_loaded()
        msg_id = await self._add_message_script(
            keys=[stream_key],
            args=[
                self.config.max_messages,
                json.dumps(message),
                self.config.session_ttl
            ]
        )
        
        # Check if compression is needed
        await self._check_compression(session_id)
        
        return msg_id.decode() if isinstance(msg_id, bytes) else msg_id
    
    async def get_context(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get conversation context for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages (None = all)
            
        Returns:
            List of messages in chronological order
        """
        stream_key = self._messages_key(session_id)
        
        # Read messages from stream
        count = limit or self.config.max_messages
        messages = await self.redis.xrevrange(stream_key, count=count)
        
        # Parse and return in chronological order
        context = []
        for msg_id, data in reversed(messages):
            msg_data = data.get(b'data') or data.get('data')
            if msg_data:
                if isinstance(msg_data, bytes):
                    msg_data = msg_data.decode()
                msg = json.loads(msg_data)
                context.append(msg)
        
        return context
    
    async def get_recent_messages(self, session_id: str, count: int = 10) -> List[Dict]:
        """Get N most recent messages."""
        return await self.get_context(session_id, limit=count)
    
    async def set_temp_variable(
        self,
        session_id: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        Set a temporary variable in working memory.
        
        Args:
            session_id: Session identifier
            key: Variable name
            value: Variable value (will be JSON serialized)
            ttl: Time to live in seconds (None = use session TTL)
        """
        var_key = self._temp_vars_key(session_id, key)
        
        await self.redis.set(
            var_key,
            json.dumps(value),
            ex=ttl or self.config.session_ttl
        )
    
    async def get_temp_variable(self, session_id: str, key: str) -> Optional[Any]:
        """
        Get a temporary variable.
        
        Args:
            session_id: Session identifier
            key: Variable name
            
        Returns:
            Variable value or None if not found
        """
        var_key = self._temp_vars_key(session_id, key)
        value = await self.redis.get(var_key)
        
        if value:
            if isinstance(value, bytes):
                value = value.decode()
            return json.loads(value)
        return None
    
    async def delete_temp_variable(self, session_id: str, key: str):
        """Delete a temporary variable."""
        var_key = self._temp_vars_key(session_id, key)
        await self.redis.delete(var_key)
    
    async def set_context_metadata(self, session_id: str, metadata: Dict):
        """
        Set metadata for the session context.
        
        Args:
            session_id: Session identifier
            metadata: Metadata dictionary
        """
        context_key = self._context_key(session_id)
        
        # Store as hash
        pipeline = self.redis.pipeline()
        for key, value in metadata.items():
            pipeline.hset(context_key, key, json.dumps(value))
        pipeline.expire(context_key, self.config.session_ttl)
        await pipeline.execute()
    
    async def get_context_metadata(self, session_id: str) -> Dict:
        """Get session context metadata."""
        context_key = self._context_key(session_id)
        data = await self.redis.hgetall(context_key)
        
        result = {}
        for key, value in data.items():
            if isinstance(key, bytes):
                key = key.decode()
            if isinstance(value, bytes):
                value = value.decode()
            result[key] = json.loads(value)
        
        return result
    
    async def clear_session(self, session_id: str):
        """
        Clear all data for a session.
        
        Args:
            session_id: Session identifier
        """
        # Find all keys matching the session pattern
        pattern = f"{self._session_key(session_id)}*"
        vars_pattern = f"agent:{self.agent_id}:vars:{session_id}:*"
        context_pattern = self._context_key(session_id)
        
        # Delete keys
        for pattern in [pattern, vars_pattern, context_pattern]:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
    
    async def get_session_stats(self, session_id: str) -> Dict:
        """
        Get statistics for a session.
        
        Returns:
            Dictionary with message_count, created_at, last_activity
        """
        stream_key = self._messages_key(session_id)
        
        # Get stream info
        info = await self.redis.xinfo_stream(stream_key)
        
        stats = {
            "message_count": info.get(b'length') or info.get('length', 0),
            "first_entry": None,
            "last_entry": None
        }
        
        # Get first and last messages
        if stats["message_count"] > 0:
            first = await self.redis.xrange(stream_key, count=1)
            last = await self.redis.xrevrange(stream_key, count=1)
            
            if first:
                msg_id, data = first[0]
                msg_data = json.loads(data.get(b'data') or data.get('data'))
                stats["first_entry"] = msg_data.get("timestamp")
            
            if last:
                msg_id, data = last[0]
                msg_data = json.loads(data.get(b'data') or data.get('data'))
                stats["last_entry"] = msg_data.get("timestamp")
        
        return stats
    
    async def _check_compression(self, session_id: str):
        """
        Check if context needs compression.
        
        This is a placeholder for compression logic that would:
        1. Summarize old messages via LLM
        2. Save summary to episodic memory (MongoDB)
        3. Trim oldest messages from Redis
        """
        stats = await self.get_session_stats(session_id)
        message_count = stats["message_count"]
        
        if message_count >= self.config.compression_threshold:
            # TODO: Implement compression logic
            # For now, just mark that compression is needed
            await self.set_temp_variable(
                session_id,
                "_needs_compression",
                True,
                ttl=300
            )
    
    async def needs_compression(self, session_id: str) -> bool:
        """Check if session needs compression."""
        return await self.get_temp_variable(session_id, "_needs_compression") or False





