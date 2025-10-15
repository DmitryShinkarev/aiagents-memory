"""PostgreSQL-based event logging implementation."""

import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import asyncpg

from models.logging.event_log import EventLog


# SQL for creating tables and indexes
CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    
    agent_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    user_id VARCHAR(100),
    
    action VARCHAR(200) NOT NULL,
    resource VARCHAR(200) NOT NULL,
    details JSONB,
    
    latency_ms FLOAT,
    tokens_used INTEGER,
    cost FLOAT,
    
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    
    trace_id VARCHAR(100),
    span_id VARCHAR(100),
    parent_span_id VARCHAR(100)
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_events_agent_id ON events (agent_id, timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_events_session_id ON events (session_id) WHERE session_id IS NOT NULL;",
    "CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events (trace_id) WHERE trace_id IS NOT NULL;",
    "CREATE INDEX IF NOT EXISTS idx_events_type_status ON events (event_type, status);",
    "CREATE INDEX IF NOT EXISTS idx_events_details ON events USING GIN (details);",
]


class EventLogger:
    """Event logger using PostgreSQL for audit trail and analytics."""
    
    def __init__(self, pg_pool: asyncpg.Pool):
        """
        Initialize event logger.
        
        Args:
            pg_pool: asyncpg connection pool
        """
        self.pool = pg_pool
    
    async def initialize(self):
        """Create tables and indexes if they don't exist."""
        async with self.pool.acquire() as conn:
            # Create table
            await conn.execute(CREATE_EVENTS_TABLE)
            
            # Create indexes
            for index_sql in CREATE_INDEXES:
                await conn.execute(index_sql)
    
    async def log_event(self, event: EventLog):
        """
        Log an event to the database.
        
        Args:
            event: Event to log
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO events (
                    event_id, timestamp, event_type,
                    agent_id, session_id, user_id,
                    action, resource, details,
                    latency_ms, tokens_used, cost,
                    status, error_message,
                    trace_id, span_id, parent_span_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            """,
                event.event_id, event.timestamp, event.event_type.value,
                event.agent_id, event.session_id, event.user_id,
                event.action, event.resource, json.dumps(event.details),
                event.latency_ms, event.tokens_used, event.cost,
                event.status, event.error_message,
                event.trace_id, event.span_id, event.parent_span_id
            )
    
    async def log_batch(self, events: List[EventLog]):
        """
        Log multiple events in a batch.
        
        Args:
            events: List of events to log
        """
        async with self.pool.acquire() as conn:
            # Prepare data for executemany
            data = [
                (
                    e.event_id, e.timestamp, e.event_type.value,
                    e.agent_id, e.session_id, e.user_id,
                    e.action, e.resource, json.dumps(e.details),
                    e.latency_ms, e.tokens_used, e.cost,
                    e.status, e.error_message,
                    e.trace_id, e.span_id, e.parent_span_id
                )
                for e in events
            ]
            
            await conn.executemany("""
                INSERT INTO events (
                    event_id, timestamp, event_type,
                    agent_id, session_id, user_id,
                    action, resource, details,
                    latency_ms, tokens_used, cost,
                    status, error_message,
                    trace_id, span_id, parent_span_id
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            """, data)
    
    async def get_agent_timeline(
        self,
        agent_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[EventLog]:
        """
        Get event timeline for an agent.
        
        Args:
            agent_id: Agent identifier
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum events
            
        Returns:
            List of events
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM events
                WHERE agent_id = $1
                  AND timestamp BETWEEN $2 AND $3
                ORDER BY timestamp DESC
                LIMIT $4
            """, agent_id, start_time, end_time, limit)
            
            return [self._row_to_event(row) for row in rows]
    
    async def get_session_trace(self, session_id: str) -> List[EventLog]:
        """
        Get complete trace of a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of events in chronological order
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM events
                WHERE session_id = $1
                ORDER BY timestamp ASC
            """, session_id)
            
            return [self._row_to_event(row) for row in rows]
    
    async def get_events_by_trace(self, trace_id: str) -> List[EventLog]:
        """
        Get all events with a specific trace ID.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            List of events
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM events
                WHERE trace_id = $1
                ORDER BY timestamp ASC
            """, trace_id)
            
            return [self._row_to_event(row) for row in rows]
    
    async def analyze_performance(
        self,
        agent_id: str,
        time_window_hours: int = 24
    ) -> Dict:
        """
        Analyze agent performance metrics.
        
        Args:
            agent_id: Agent identifier
            time_window_hours: Time window for analysis
            
        Returns:
            Performance statistics
        """
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_events,
                    COUNT(DISTINCT session_id) as total_sessions,
                    AVG(latency_ms) as avg_latency,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99_latency,
                    SUM(tokens_used) as total_tokens,
                    SUM(cost) as total_cost,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) as error_rate
                FROM events
                WHERE agent_id = $1
                  AND timestamp > NOW() - INTERVAL '1 hour' * $2
            """, agent_id, time_window_hours)
            
            return dict(stats) if stats else {}
    
    async def get_error_summary(
        self,
        agent_id: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict]:
        """
        Get summary of errors.
        
        Args:
            agent_id: Optional agent filter
            hours: Time window in hours
            
        Returns:
            List of error summaries
        """
        query = """
            SELECT
                event_type,
                action,
                resource,
                error_message,
                COUNT(*) as error_count,
                MAX(timestamp) as last_occurrence
            FROM events
            WHERE status = 'error'
              AND timestamp > NOW() - INTERVAL '1 hour' * $1
        """
        
        params = [hours]
        
        if agent_id:
            query += " AND agent_id = $2"
            params.append(agent_id)
        
        query += """
            GROUP BY event_type, action, resource, error_message
            ORDER BY error_count DESC
            LIMIT 50
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_resource_usage(
        self,
        agent_id: str,
        hours: int = 24
    ) -> Dict:
        """
        Get resource usage breakdown by memory type.
        
        Args:
            agent_id: Agent identifier
            hours: Time window
            
        Returns:
            Usage statistics by resource
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    resource,
                    COUNT(*) as operation_count,
                    AVG(latency_ms) as avg_latency,
                    SUM(tokens_used) as total_tokens
                FROM events
                WHERE agent_id = $1
                  AND timestamp > NOW() - INTERVAL '1 hour' * $2
                GROUP BY resource
                ORDER BY operation_count DESC
            """, agent_id, hours)
            
            return {
                row["resource"]: {
                    "operation_count": row["operation_count"],
                    "avg_latency": float(row["avg_latency"]) if row["avg_latency"] else 0,
                    "total_tokens": row["total_tokens"] or 0
                }
                for row in rows
            }
    
    async def cleanup_old_events(self, days: int = 90) -> int:
        """
        Delete events older than specified days.
        
        Args:
            days: Age threshold
            
        Returns:
            Number of events deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM events
                WHERE timestamp < $1
            """, cutoff_date)
            
            # Extract count from result string like "DELETE 123"
            count = int(result.split()[-1]) if result else 0
            return count
    
    def _row_to_event(self, row) -> EventLog:
        """Convert database row to EventLog object."""
        from models.logging.event_log import EventType
        
        return EventLog(
            event_id=str(row["event_id"]),
            timestamp=row["timestamp"],
            event_type=EventType(row["event_type"]),
            agent_id=row["agent_id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            action=row["action"],
            resource=row["resource"],
            details=json.loads(row["details"]) if row["details"] else {},
            latency_ms=row["latency_ms"],
            tokens_used=row["tokens_used"],
            cost=row["cost"],
            status=row["status"],
            error_message=row["error_message"],
            trace_id=row["trace_id"],
            span_id=row["span_id"],
            parent_span_id=row["parent_span_id"]
        )


