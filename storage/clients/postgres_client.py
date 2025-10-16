"""
PostgreSQL client for audit logs and structured data.

This module provides an async PostgreSQL client with connection pooling,
health checks, and specialized methods for logging operations.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import asyncpg
from asyncpg import Connection, Pool
from asyncpg.exceptions import (
    ConnectionDoesNotExistError,
    InterfaceError,
    PostgresError
)

from ...config.settings import get_settings

logger = logging.getLogger(__name__)


class PostgresClient:
    """Async PostgreSQL client with connection pooling and health checks."""
    
    def __init__(
        self,
        url: str,
        max_pool_size: int = 20,
        min_pool_size: int = 5,
        command_timeout: int = 60,
        server_settings: Optional[Dict[str, str]] = None
    ):
        self.url = url
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.command_timeout = command_timeout
        self.server_settings = server_settings or {}
        
        self._pool: Optional[Pool] = None
        self._health_status = "unknown"
        self._last_health_check = None
        
    async def connect(self) -> None:
        """Initialize PostgreSQL connection pool."""
        try:
            self._pool = await asyncpg.create_pool(
                self.url,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
                command_timeout=self.command_timeout,
                server_settings=self.server_settings
            )
            
            # Test connection
            async with self._pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            self._health_status = "healthy"
            self._last_health_check = datetime.utcnow()
            
            # Initialize tables
            await self._initialize_tables()
            
            logger.info("PostgreSQL client connected successfully")
            
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool:
            await self._pool.close()
        logger.info("PostgreSQL client disconnected")
    
    async def _initialize_tables(self) -> None:
        """Initialize database tables and indexes."""
        try:
            async with self._pool.acquire() as conn:
                # Audit logs table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id SERIAL PRIMARY KEY,
                        agent_id VARCHAR(255) NOT NULL,
                        team_id VARCHAR(255),
                        user_id VARCHAR(255),
                        action VARCHAR(100) NOT NULL,
                        entity_type VARCHAR(100),
                        entity_id VARCHAR(255),
                        session_id VARCHAR(255),
                        request_id VARCHAR(255),
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        payload JSONB,
                        execution_time_ms INTEGER,
                        status VARCHAR(50),
                        error_message TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create indexes
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_logs_agent_id 
                    ON audit_logs(agent_id)
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp 
                    ON audit_logs(timestamp)
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_logs_action 
                    ON audit_logs(action)
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_logs_entity 
                    ON audit_logs(entity_type, entity_id)
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_logs_session 
                    ON audit_logs(session_id)
                """)
                
                # Idempotency table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS idempotency_cache (
                        id SERIAL PRIMARY KEY,
                        operation_type VARCHAR(100) NOT NULL,
                        idempotency_key VARCHAR(255) NOT NULL,
                        request_hash VARCHAR(64) NOT NULL,
                        response JSONB NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        UNIQUE(operation_type, idempotency_key)
                    )
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_idempotency_expires 
                    ON idempotency_cache(expires_at)
                """)
                
                # Memory metrics table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_metrics (
                        id SERIAL PRIMARY KEY,
                        metric_name VARCHAR(100) NOT NULL,
                        metric_value NUMERIC NOT NULL,
                        labels JSONB,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_memory_metrics_name_time 
                    ON memory_metrics(metric_name, timestamp)
                """)
                
                logger.info("PostgreSQL tables and indexes initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL tables: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on PostgreSQL connection."""
        try:
            if not self._pool:
                return {
                    "status": "unhealthy",
                    "error": "Connection pool not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Test basic operations
            start_time = datetime.utcnow()
            
            async with self._pool.acquire() as conn:
                # Test query
                result = await conn.fetchval("SELECT 1")
                
                # Get database info
                version = await conn.fetchval("SELECT version()")
                db_size = await conn.fetchval("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """)
                
                # Get connection pool info
                pool_size = self._pool.get_size()
                pool_idle = self._pool.get_idle_size()
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self._health_status = "healthy"
            self._last_health_check = datetime.utcnow()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "postgresql_version": version,
                "database_size": db_size,
                "pool_size": pool_size,
                "pool_idle": pool_idle,
                "timestamp": self._last_health_check.isoformat()
            }
            
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error(f"PostgreSQL health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @property
    def is_healthy(self) -> bool:
        """Check if PostgreSQL client is healthy."""
        return self._health_status == "healthy"
    
    # Basic operations
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query and return status."""
        if not self._pool:
            raise RuntimeError("PostgreSQL client not connected")
        
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value."""
        if not self._pool:
            raise RuntimeError("PostgreSQL client not connected")
        
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row."""
        if not self._pool:
            raise RuntimeError("PostgreSQL client not connected")
        
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows."""
        if not self._pool:
            raise RuntimeError("PostgreSQL client not connected")
        
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    # Audit logging operations
    
    async def log_audit_event(
        self,
        agent_id: str,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> int:
        """Log an audit event."""
        query = """
            INSERT INTO audit_logs (
                agent_id, team_id, user_id, action, entity_type, entity_id,
                session_id, request_id, payload, execution_time_ms, status, error_message
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id
        """
        
        return await self.fetchval(
            query,
            agent_id, team_id, user_id, action, entity_type, entity_id,
            session_id, request_id, json.dumps(payload) if payload else None,
            execution_time_ms, status, error_message
        )
    
    async def get_audit_logs(
        self,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filters."""
        conditions = []
        params = []
        param_count = 0
        
        if agent_id:
            param_count += 1
            conditions.append(f"agent_id = ${param_count}")
            params.append(agent_id)
        
        if team_id:
            param_count += 1
            conditions.append(f"team_id = ${param_count}")
            params.append(team_id)
        
        if user_id:
            param_count += 1
            conditions.append(f"user_id = ${param_count}")
            params.append(user_id)
        
        if action:
            param_count += 1
            conditions.append(f"action = ${param_count}")
            params.append(action)
        
        if entity_type:
            param_count += 1
            conditions.append(f"entity_type = ${param_count}")
            params.append(entity_type)
        
        if entity_id:
            param_count += 1
            conditions.append(f"entity_id = ${param_count}")
            params.append(entity_id)
        
        if session_id:
            param_count += 1
            conditions.append(f"session_id = ${param_count}")
            params.append(session_id)
        
        if start_time:
            param_count += 1
            conditions.append(f"timestamp >= ${param_count}")
            params.append(start_time)
        
        if end_time:
            param_count += 1
            conditions.append(f"timestamp <= ${param_count}")
            params.append(end_time)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT * FROM audit_logs
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        
        params.extend([limit, offset])
        
        rows = await self.fetch(query, *params)
        
        return [
            {
                "id": row["id"],
                "agent_id": row["agent_id"],
                "team_id": row["team_id"],
                "user_id": row["user_id"],
                "action": row["action"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "session_id": row["session_id"],
                "request_id": row["request_id"],
                "timestamp": row["timestamp"].isoformat(),
                "payload": row["payload"],
                "execution_time_ms": row["execution_time_ms"],
                "status": row["status"],
                "error_message": row["error_message"]
            }
            for row in rows
        ]
    
    # Idempotency operations
    
    async def store_idempotency_result(
        self,
        operation_type: str,
        idempotency_key: str,
        request_hash: str,
        response: Dict[str, Any],
        expires_at: datetime
    ) -> None:
        """Store idempotency result."""
        query = """
            INSERT INTO idempotency_cache (
                operation_type, idempotency_key, request_hash, response, expires_at
            ) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (operation_type, idempotency_key)
            DO UPDATE SET
                request_hash = EXCLUDED.request_hash,
                response = EXCLUDED.response,
                expires_at = EXCLUDED.expires_at
        """
        
        await self.execute(
            query,
            operation_type, idempotency_key, request_hash,
            json.dumps(response), expires_at
        )
    
    async def get_idempotency_result(
        self,
        operation_type: str,
        idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get idempotency result."""
        query = """
            SELECT request_hash, response, expires_at
            FROM idempotency_cache
            WHERE operation_type = $1 AND idempotency_key = $2
            AND expires_at > NOW()
        """
        
        row = await self.fetchrow(query, operation_type, idempotency_key)
        
        if row:
            return {
                "request_hash": row["request_hash"],
                "response": row["response"],
                "expires_at": row["expires_at"].isoformat()
            }
        
        return None
    
    async def cleanup_expired_idempotency(self) -> int:
        """Clean up expired idempotency records."""
        query = "DELETE FROM idempotency_cache WHERE expires_at <= NOW()"
        result = await self.execute(query)
        return int(result.split()[-1])  # Extract count from result
    
    # Metrics operations
    
    async def store_metric(
        self,
        metric_name: str,
        metric_value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Store a metric."""
        query = """
            INSERT INTO memory_metrics (metric_name, metric_value, labels)
            VALUES ($1, $2, $3)
        """
        
        await self.execute(
            query,
            metric_name, metric_value,
            json.dumps(labels) if labels else None
        )
    
    async def get_metrics(
        self,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get metrics."""
        conditions = []
        params = []
        param_count = 0
        
        if metric_name:
            param_count += 1
            conditions.append(f"metric_name = ${param_count}")
            params.append(metric_name)
        
        if start_time:
            param_count += 1
            conditions.append(f"timestamp >= ${param_count}")
            params.append(start_time)
        
        if end_time:
            param_count += 1
            conditions.append(f"timestamp <= ${param_count}")
            params.append(end_time)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT * FROM memory_metrics
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ${param_count + 1}
        """
        
        params.append(limit)
        
        rows = await self.fetch(query, *params)
        
        return [
            {
                "id": row["id"],
                "metric_name": row["metric_name"],
                "metric_value": float(row["metric_value"]),
                "labels": row["labels"],
                "timestamp": row["timestamp"].isoformat()
            }
            for row in rows
        ]
    
    # Transaction support
    
    async def transaction(self):
        """Create a transaction context manager."""
        if not self._pool:
            raise RuntimeError("PostgreSQL client not connected")
        
        return self._pool.acquire()


# Global PostgreSQL client instance
_postgres_client: Optional[PostgresClient] = None


async def get_postgres_client() -> PostgresClient:
    """Get or create global PostgreSQL client instance."""
    global _postgres_client
    
    if _postgres_client is None:
        settings = get_settings()
        _postgres_client = PostgresClient(
            url=settings.postgres_url,
            max_pool_size=settings.postgres_max_pool_size
        )
        await _postgres_client.connect()
    
    return _postgres_client


async def close_postgres_client():
    """Close global PostgreSQL client."""
    global _postgres_client
    
    if _postgres_client:
        await _postgres_client.disconnect()
        _postgres_client = None
