-- PostgreSQL initialization script for memory-agents

-- Create events table
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_agent_id ON events (agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_session_id ON events (session_id) WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events (trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_type_status ON events (event_type, status);
CREATE INDEX IF NOT EXISTS idx_events_details ON events USING GIN (details);

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON TABLE events TO memory_agent_user;





