# Memory-Agents

A comprehensive memory management system for multi-agent AI systems, implementing four cognitive memory types inspired by human memory systems with stable API contracts and dynamic entity support.

## Features

- **Working Memory**: Short-term operational memory for active sessions (Redis)
- **Episodic Memory**: Long-term memory for specific events and interactions (MongoDB)
- **Semantic Memory**: Generalized knowledge with vector search (MongoDB + Qdrant)
- **Procedural Memory**: Skills, procedures, and executable code (MongoDB)
- **User Facts**: Personal information with full version history (MongoDB)
- **Dynamic Entities**: Schema-driven business entities with validation
- **Stable API Contracts**: Versioned, idempotent operations
- **Multi-Agent Support**: Memory isolation and sharing between agents
- **Vector Search**: High-performance semantic search with temporal decay
- **TTL Management**: Automatic cleanup of expired memories
- **Health Monitoring**: Comprehensive health checks and metrics

## Quick Start

```python
from memory_agents import get_memory_facade

# Get memory facade
memory = get_memory_facade()

# Create an episode
await memory.create_episode(
    episode_id="ep_001",
    context={"agent_id": "agent_001", "user_id": "user_001"},
    scope="user_private",
    episode_type="interaction",
    title="User interaction",
    trajectory=[{
        "step_id": "1",
        "timestamp": "2024-01-01T10:00:00Z",
        "role": "user",
        "action": "message",
        "content": "Hello!"
    }]
)

# Retrieve comprehensive context
context = await memory.retrieve_comprehensive_context(
    agent_id="agent_001",
    user_id="user_001"
)
```

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set up your environment variables:

```bash
# Redis
export REDIS_URL="redis://localhost:6379"
export REDIS_SESSION_TTL=3600

# MongoDB
export MONGODB_URL="mongodb://localhost:27017"
export MONGODB_DATABASE="agent_memory"

# Qdrant
export QDRANT_URL="http://localhost:6333"
export QDRANT_API_KEY="your_api_key"

# PostgreSQL
export POSTGRES_URL="postgresql://postgres:password@localhost:5432/memory_logs"

# Embeddings
export OPENAI_API_KEY="your_openai_key"
export EMBEDDING_MODEL="text-embedding-3-small"
```

## Architecture

The system follows a layered architecture with stable API contracts:

```
API Layer (Stable Contracts)
    ↓
Business Logic Layer (Validation & Idempotency)
    ↓
Domain Layer (Memory Services)
    ↓
Storage Layer (Redis, MongoDB, Qdrant, PostgreSQL)
```

### Key Principles

- **Stable API Contracts**: External interfaces never break
- **Idempotent Operations**: All write operations are idempotent
- **Versioned APIs**: Explicit versioning with backward compatibility
- **Dynamic Schemas**: Business entities with runtime schema validation
- **Temporal Decay**: Knowledge naturally ages over time
- **Access Control**: Granular permissions and data isolation

## Memory Types

### Working Memory (Redis)
- Session management with TTL
- Temporary variables and context
- RAG result caching
- Agent coordination via pub/sub
- Idempotency caching

### Episodic Memory (MongoDB)
- Event trajectories with full history
- Temporal context and metadata
- Success/failure tracking
- Automatic consolidation into knowledge
- TTL-based cleanup by scope

### Semantic Memory (MongoDB + Qdrant)
- Generalized knowledge with confidence scores
- Vector embeddings for semantic search
- Temporal decay for knowledge aging
- Hybrid search (dense + sparse vectors)
- Access control and filtering

### Procedural Memory (MongoDB)
- Executable procedures in multiple languages
- Usage metrics and success rate tracking
- Code versioning and validation
- Performance monitoring
- Soft deletion (deactivation)

### User Facts (MongoDB)
- Personal information with full version history
- Conflict resolution with confidence scoring
- Temporal validity periods
- Automatic fact extraction from text
- Access control and privacy

## Usage Examples

### Basic Memory Operations

```python
# Working Memory
await memory.working.store_session("session_1", {
    "current_message": "User needs help",
    "conversation_history": [...],
    "temporary_variables": {"user_tier": "premium"}
})

# Episodic Memory
await memory.create_episode(
    episode_id="ep_001",
    context={"agent_id": "support_001", "user_id": "user_123"},
    scope="user_private",
    episode_type="interaction",
    title="Support interaction",
    trajectory=[...],
    success=True,
    importance=0.8
)

# Semantic Memory
await memory.create_knowledge(
    knowledge_id="kb_001",
    knowledge="Premium users have priority support",
    source="system",
    confidence=1.0,
    agent_id="support_001",
    temporal_scope="always"
)

# Procedural Memory
await memory.procedural.store_procedure(
    procedure_id="proc_001",
    name="resolve_billing_issue",
    description="Resolve billing issues",
    code="def resolve_billing_issue(account): ...",
    language="python"
)

# User Facts
await memory.facts.store_fact(
    fact_id="fact_001",
    user_id="user_123",
    fact_type="personal",
    key="name",
    value="John Doe",
    confidence=1.0,
    source="user_stated"
)
```

### Semantic Search with Temporal Decay

```python
# Search for relevant knowledge
knowledge_items = await memory.semantic_search(
    query_embedding=[0.1, 0.2, ...],  # Your embedding vector
    agent_id="support_001",
    limit=10,
    include_temporal_decay=True
)

# Results include similarity scores and temporal scores
for item in knowledge_items:
    print(f"Knowledge: {item['knowledge']}")
    print(f"Similarity: {item['similarity_score']}")
    print(f"Temporal: {item['temporal_score']}")
    print(f"Combined: {item['combined_score']}")
```

### Multi-Agent Coordination

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

### Comprehensive Context Retrieval

```python
# Get all relevant context for an agent
context = await memory.retrieve_comprehensive_context(
    agent_id="support_001",
    user_id="user_123",
    session_id="session_001",
    query="billing question",
    include_episodes=True,
    include_knowledge=True,
    include_facts=True
)

print(f"Working memory: {context['working_memory']}")
print(f"Episodes: {len(context['episodes'])}")
print(f"Knowledge: {len(context['knowledge'])}")
print(f"User facts: {context['facts']}")
```

## API Contracts

The system provides stable, versioned API contracts:

### Entity Operations
```python
from memory_agents import UniversalEntityWriteRequest

request = UniversalEntityWriteRequest(
    idempotency_key="create-employee-12345",
    requesting_agent_id="hr_agent_001",
    entity_namespace="hr",
    entity_type="employee",
    entity_data={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@company.com",
        "department_id": "dept_001"
    },
    access_scope="team_shared"
)
```

### Episode Operations
```python
from memory_agents import UniversalEpisodeWriteRequest, EpisodeContext

request = UniversalEpisodeWriteRequest(
    idempotency_key="episode-001",
    context=EpisodeContext(
        user_id="user_123",
        agent_id="support_001",
        session_id="session_001"
    ),
    scope="user_private",
    episode_type="interaction",
    title="Support interaction",
    trajectory=[...],
    success=True,
    importance=0.8
)
```

## Health Monitoring

```python
# Check system health
health = await memory.health_check()
print(f"Overall status: {health['status']}")
print(f"Working memory: {health['services']['working_memory']['status']}")
print(f"Episodic memory: {health['services']['episodic_memory']['status']}")

# Get detailed metrics
metrics = await memory.get_metrics()
print(f"Active sessions: {metrics['working_memory']['active_sessions']}")
print(f"Total episodes: {metrics['episodic_memory']['total_episodes']}")
print(f"Total knowledge: {metrics['semantic_memory']['total_knowledge']}")
print(f"Total procedures: {metrics['procedural_memory']['total_procedures']}")
print(f"Total facts: {metrics['facts']['total_facts']}")
```

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy .

# Run example
python examples/memory_usage_example.py
```

## Examples

See `examples/memory_usage_example.py` for a comprehensive example demonstrating all memory types and operations.

## License

MIT License - see LICENSE file for details.
