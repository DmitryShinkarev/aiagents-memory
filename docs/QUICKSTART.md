# Quick Start Guide

Get up and running with Memory-Agents in minutes.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- OpenAI API key (for embeddings)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/memory-agents.git
cd memory-agents
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Quick Setup

### 1. Start Dependencies

```bash
docker-compose up -d
```

This starts:
- Redis (port 6379)
- MongoDB (port 27017)
- Qdrant (port 6333)
- PostgreSQL (port 5432)

### 2. Configure Environment

Create `.env` file:

```bash
# Redis
REDIS_URL=redis://localhost:6379

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=agent_memory

# Qdrant
QDRANT_URL=http://localhost:6333

# PostgreSQL
POSTGRES_URL=postgresql://postgres:password@localhost:5432/memory_logs

# Embeddings (Required)
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small

# Optional
LOG_LEVEL=INFO
PROMETHEUS_PORT=8000
```

### 3. Initialize Databases

```bash
# MongoDB initialization
mongo < scripts/mongo-init.js

# PostgreSQL initialization
psql -d memory_logs -f scripts/postgres-init.sql
```

## Basic Usage

### Simple Example

```python
import asyncio
from memory_agents import get_memory_facade

async def main():
    # Get memory facade
    memory = get_memory_facade()
    
    # Create an episode
    await memory.create_episode(
        episode_id="ep_001",
        context={
            "agent_id": "support_agent_001",
            "user_id": "user_123",
            "session_id": "session_001"
        },
        scope="user_private",
        episode_type="interaction",
        title="Customer support interaction",
        trajectory=[{
            "step_id": "1",
            "timestamp": "2024-01-01T10:00:00Z",
            "role": "user",
            "action": "message",
            "content": "I need help with billing"
        }],
        success=True,
        importance=0.8
    )
    
    # Store knowledge
    await memory.create_knowledge(
        knowledge_id="kb_001",
        knowledge="Premium users have priority support",
        source="system",
        confidence=1.0,
        agent_id="support_agent_001"
    )
    
    # Get comprehensive context
    context = await memory.retrieve_comprehensive_context(
        agent_id="support_agent_001",
        user_id="user_123"
    )
    
    print(f"Retrieved context with {len(context.get('episodes', []))} episodes")

if __name__ == "__main__":
    asyncio.run(main())
```

### Run the Example

```bash
python examples/memory_usage_example.py
```

## Memory Types Overview

### 1. Working Memory (Redis)
Short-term operational memory for active sessions.

```python
# Store session data
await memory.working.store_session("session_001", {
    "current_message": "User needs help",
    "conversation_history": [...],
    "temporary_variables": {"user_tier": "premium"}
})

# Get context
context = await memory.working.get_context("agent_001", "session_001")
```

### 2. Episodic Memory (MongoDB + Qdrant)
Long-term memory for specific events.

```python
# Create episode
await memory.create_episode(
    episode_id="ep_001",
    context={"agent_id": "agent_001", "user_id": "user_123"},
    scope="user_private",
    episode_type="interaction",
    title="User support call",
    trajectory=[...],
    success=True,
    importance=0.8
)

# Query episodes
episodes = await memory.query_episodes(
    filter_by_agent_id="agent_001",
    filter_by_user_id="user_123",
    min_importance=0.5,
    limit=10
)
```

### 3. Semantic Memory (MongoDB + Qdrant)
Generalized knowledge with vector search.

```python
# Store knowledge
await memory.create_knowledge(
    knowledge_id="kb_001",
    knowledge="Premium users have priority support",
    source="system",
    confidence=1.0,
    agent_id="agent_001"
)

# Semantic search
knowledge_items = await memory.semantic_search(
    query_embedding=[0.1, 0.2, ...],  # Your embedding vector
    agent_id="agent_001",
    limit=10
)
```

### 4. Procedural Memory (MongoDB)
Skills and executable code.

```python
# Store procedure
await memory.procedural.store_procedure(
    procedure_id="proc_001",
    name="resolve_billing_issue",
    description="Resolve billing issues",
    code="def resolve_billing_issue(account): ...",
    language="python"
)

# Execute procedure
result = await memory.procedural.execute_procedure(
    name="resolve_billing_issue",
    parameters={"account": "12345"}
)
```

### 5. User Facts (MongoDB)
Personal information with versioning.

```python
# Store fact
await memory.facts.store_fact(
    fact_id="fact_001",
    user_id="user_123",
    fact_type="personal",
    key="name",
    value="John Doe",
    confidence=1.0,
    source="user_stated"
)

# Get user profile
profile = await memory.facts.get_user_profile("user_123")
```

## Multi-Agent Coordination

```python
# Coordinate agents through pub/sub
await memory.working.coordinate_agents(
    task_id="task_001",
    message={"action": "analyze", "data": "..."},
    target_agents=["agent_001", "agent_002"]
)

# Get task results
results = await memory.working.get_task_results("task_001", timeout=30)
```

## Health Monitoring

```python
# Health check
health = await memory.health_check()
print(f"System status: {health['status']}")

# Get metrics
metrics = await memory.get_metrics()
print(f"Active sessions: {metrics['working_memory']['active_sessions']}")
```

## Testing

### Run Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

### Type Checking

```bash
mypy .
```

## Next Steps

1. **Read the Documentation**: Check out [API Reference](API_REFERENCE.md) for detailed API documentation
2. **Explore Examples**: See [Examples](EXAMPLES.md) for comprehensive usage examples
3. **Deploy to Production**: Follow the [Deployment Guide](DEPLOYMENT.md) for production setup
4. **Understand Architecture**: Read [Architecture](ARCHITECTURE.md) for system design details

## Troubleshooting

### Common Issues

#### Connection Errors
- Ensure all services are running: `docker-compose ps`
- Check connection URLs in `.env`
- Verify ports are not in use

#### OpenAI API Errors
- Verify your API key is correct
- Check API quota and billing
- Ensure internet connectivity

#### Database Errors
- Check if databases are initialized
- Verify user permissions
- Check disk space

### Getting Help

- 📖 **Documentation**: [docs/](docs/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/memory-agents/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-org/memory-agents/discussions)

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` | Yes |
| `MONGODB_URL` | MongoDB connection URL | `mongodb://localhost:27017` | Yes |
| `QDRANT_URL` | Qdrant server URL | `http://localhost:6333` | Yes |
| `POSTGRES_URL` | PostgreSQL connection URL | `postgresql://postgres:password@localhost:5432/memory_logs` | Yes |
| `OPENAI_API_KEY` | OpenAI API key | None | Yes |
| `EMBEDDING_MODEL` | Embedding model name | `text-embedding-3-small` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Memory Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_SESSION_TTL` | Session TTL in seconds | `3600` |
| `MONGODB_DATABASE` | MongoDB database name | `agent_memory` |
| `WORKING_MEMORY_MAX_MESSAGES` | Max messages in working memory | `50` |
| `EPISODIC_MEMORY_TTL_DAYS` | Episodic memory TTL | `90` |
| `SEMANTIC_MEMORY_TTL_DAYS` | Semantic memory TTL | `365` |

## Production Considerations

### Security
- Use strong passwords for databases
- Enable TLS/SSL for all connections
- Implement proper access controls
- Regular security updates

### Performance
- Monitor resource usage
- Optimize database indexes
- Use connection pooling
- Implement caching strategies

### Monitoring
- Set up health checks
- Monitor metrics and logs
- Implement alerting
- Regular backups

### Scaling
- Use load balancers
- Implement horizontal scaling
- Optimize database queries
- Use CDN for static assets