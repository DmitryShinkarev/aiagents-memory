# Memory-Agents

A comprehensive memory management system for multi-agent AI systems, implementing four cognitive memory types inspired by human memory systems with stable API contracts and dynamic entity support.

## 🧠 Overview

Memory-Agents provides a production-ready memory architecture for AI agents that mimics human cognitive memory systems. It supports multiple agents working together while maintaining data isolation, versioning, and temporal decay of knowledge.

## ✨ Key Features

- **🧠 Four Memory Types**: Working, Episodic, Semantic, and Procedural memory
- **🔒 Stable API Contracts**: Versioned, backward-compatible interfaces
- **⚡ Idempotent Operations**: Safe retry mechanisms with collision detection
- **🕒 Temporal Decay**: Knowledge naturally ages over time
- **👥 Multi-Agent Support**: Isolated memory spaces with controlled sharing
- **🔍 Vector Search**: High-performance semantic search with Qdrant
- **📊 Health Monitoring**: Comprehensive metrics and health checks
- **🔄 Real-time Coordination**: Pub/Sub messaging between agents

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (Stable Contracts)             │
│  • UniversalEntityWriteRequest                             │
│  • UniversalEpisodeWriteRequest                            │
│  • UniversalKnowledgeWriteRequest                          │
│  • Versioned APIs with backward compatibility              │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Business Logic Layer                           │
│  • IdempotencyGuard with collision detection               │
│  • RequestValidator with business rules                    │
│  • Contract adapters between layers                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Domain Layer                                │
│  • WorkingMemoryService (Redis)                            │
│  • EpisodicMemoryService (MongoDB + Qdrant)                │
│  • SemanticMemoryService (MongoDB + Qdrant)                │
│  • ProceduralMemoryService (MongoDB)                       │
│  • FactsService (MongoDB)                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                Storage Layer                                │
│  • Redis (Working Memory, Cache, Pub/Sub)                  │
│  • MongoDB (Long-term Memory, Documents)                   │
│  • Qdrant (Vector Search, Embeddings)                      │
│  • PostgreSQL (Audit Logs, Metrics)                        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/your-org/memory-agents.git
cd memory-agents
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:

```bash
# Redis
REDIS_URL=redis://localhost:6379
REDIS_SESSION_TTL=3600

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=agent_memory

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_api_key

# PostgreSQL
POSTGRES_URL=postgresql://postgres:password@localhost:5432/memory_logs

# Embeddings
OPENAI_API_KEY=your_openai_key
EMBEDDING_MODEL=text-embedding-3-small
```

### Basic Usage

```python
import asyncio
from memory_agents import get_memory_facade

async def main():
    # Get memory facade
    memory = get_memory_facade()
    
    # Create an episode
    await memory.create_episode(
        episode_id="ep_001",
        context={"agent_id": "support_001", "user_id": "user_123"},
        scope="user_private",
        episode_type="interaction",
        title="Support interaction",
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
        agent_id="support_001"
    )
    
    # Get comprehensive context
    context = await memory.retrieve_comprehensive_context(
        agent_id="support_001",
        user_id="user_123"
    )
    
    print(f"Retrieved context with {len(context.get('episodes', []))} episodes")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧠 Memory Types

### Working Memory (Redis)
Short-term operational memory for active sessions.

```python
# Store session data
await memory.working.store_session("session_001", {
    "current_message": "User needs help",
    "conversation_history": [...],
    "temporary_variables": {"user_tier": "premium"}
})

# Get context
context = await memory.get_context("agent_001", "session_001")

# Cache RAG results
await memory.working.cache_retrieval("query_hash", result, ttl=300)
```

### Episodic Memory (MongoDB + Qdrant)
Long-term memory for specific events and interactions.

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
    importance=0.8,
    user_satisfaction=0.9
)

# Query episodes
episodes = await memory.query_episodes(
    filter_by_agent_id="agent_001",
    filter_by_user_id="user_123",
    min_importance=0.5,
    limit=10
)
```

### Semantic Memory (MongoDB + Qdrant)
Generalized knowledge with vector search and temporal decay.

```python
# Store knowledge
await memory.create_knowledge(
    knowledge_id="kb_001",
    knowledge="Premium users have priority support",
    source="system",
    confidence=1.0,
    agent_id="agent_001",
    temporal_scope="always",
    half_life_days=365
)

# Semantic search with temporal decay
knowledge_items = await memory.semantic_search(
    query_embedding=[0.1, 0.2, ...],  # Your embedding vector
    agent_id="agent_001",
    limit=10,
    include_temporal_decay=True
)
```

### Procedural Memory (MongoDB)
Skills, procedures, and executable code with usage metrics.

```python
# Store procedure
await memory.procedural.store_procedure(
    procedure_id="proc_001",
    name="resolve_billing_issue",
    description="Resolve billing issues for customers",
    code="""
def resolve_billing_issue(account_number, issue_type):
    # Implementation here
    return {"status": "resolved"}
    """,
    language="python",
    parameters_schema={
        "type": "object",
        "properties": {
            "account_number": {"type": "string"},
            "issue_type": {"type": "string"}
        }
    }
)

# Execute procedure
result = await memory.procedural.execute_procedure(
    name="resolve_billing_issue",
    parameters={"account_number": "12345", "issue_type": "overcharge"}
)
```

### User Facts (MongoDB)
Personal information with full version history and conflict resolution.

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

# Query facts
facts = await memory.facts.query_facts(
    user_id="user_123",
    filter_by_fact_type=["personal", "preference"],
    min_confidence=0.8
)
```

## 🔄 Multi-Agent Coordination

```python
# Coordinate agents through pub/sub
await memory.working.coordinate_agents(
    task_id="task_001",
    message={"action": "analyze", "data": "..."},
    target_agents=["agent_001", "agent_002"]
)

# Get task results
results = await memory.working.get_task_results("task_001", timeout=30)

# Subscribe to events
events = await memory.working.subscribe_events(
    channels=["task:analysis", "results:task_001"],
    timeout=10
)
```

## 📊 Monitoring and Health

```python
# Health check
health = await memory.health_check()
print(f"System status: {health['status']}")
print(f"Working memory: {health['services']['working_memory']['status']}")

# Get metrics
metrics = await memory.get_metrics()
print(f"Active sessions: {metrics['working_memory']['active_sessions']}")
print(f"Total episodes: {metrics['episodic_memory']['total_episodes']}")
print(f"Total knowledge: {metrics['semantic_memory']['total_knowledge']}")
```

## 🔒 Security and Access Control

The system provides granular access control:

- **Memory Scopes**: `USER_PRIVATE`, `AGENT_PRIVATE`, `TEAM_SHARED`, `CROSS_TEAM`, `ORGANIZATION`
- **Agent Isolation**: Each agent has isolated memory space
- **Team Sharing**: Controlled sharing within teams
- **User Privacy**: User data is protected and isolated

```python
# Create episode with specific scope
await memory.create_episode(
    episode_id="ep_001",
    context={"agent_id": "agent_001", "user_id": "user_123"},
    scope="user_private",  # Only accessible to the user
    # ... other parameters
)

# Create knowledge with team access
await memory.create_knowledge(
    knowledge_id="kb_001",
    knowledge="Team best practices",
    source="system",
    confidence=1.0,
    agent_id="agent_001",
    access_scope="team_shared",
    allowed_teams=["team_001", "team_002"]
)
```

## 🎯 API Contracts

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
        "email": "john@company.com"
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

## 🛠️ Development

### Running Tests
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

### Running Examples
```bash
python examples/memory_usage_example.py
```

## 📁 Project Structure

```
memory-agents/
├── api/                    # Stable API contracts
│   ├── contracts/         # Pydantic DTOs
│   └── versioning.py      # API version management
├── business/              # Business logic layer
│   ├── idempotency.py    # Idempotency mechanisms
│   └── validation.py     # Request validation
├── domain/               # Domain services
│   └── memory/          # Memory type services
├── services/            # High-level services
│   └── memory_facade.py # Unified memory interface
├── storage/            # Storage clients
│   └── clients/       # Database clients
├── config/            # Configuration
├── examples/         # Usage examples
├── docs/            # Documentation
└── scripts/        # Database initialization
```

## 🔧 Configuration Options

### Redis Configuration
- `REDIS_URL`: Redis connection URL
- `REDIS_SESSION_TTL`: Session TTL in seconds (default: 3600)
- `REDIS_MAX_CONNECTIONS`: Max connection pool size (default: 50)

### MongoDB Configuration
- `MONGODB_URL`: MongoDB connection URL
- `MONGODB_DATABASE`: Database name (default: "agent_memory")
- `MONGODB_MAX_POOL_SIZE`: Max connection pool size (default: 100)

### Qdrant Configuration
- `QDRANT_URL`: Qdrant server URL
- `QDRANT_API_KEY`: API key (optional)
- `QDRANT_TIMEOUT`: Request timeout (default: 30)

### PostgreSQL Configuration
- `POSTGRES_URL`: PostgreSQL connection URL
- `POSTGRES_MAX_POOL_SIZE`: Max connection pool size (default: 20)

### Memory Configuration
- `WORKING_MEMORY_MAX_MESSAGES`: Max messages in working memory (default: 50)
- `EPISODIC_MEMORY_TTL_DAYS`: Episodic memory TTL (default: 90)
- `SEMANTIC_MEMORY_TTL_DAYS`: Semantic memory TTL (default: 365)

## 📚 Examples

See the `examples/` directory for comprehensive usage examples:

- `memory_usage_example.py`: Complete example showing all memory types
- Basic operations for each memory type
- Multi-agent coordination examples
- Health monitoring and metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 Documentation: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/memory-agents/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-org/memory-agents/discussions)

## 🗺️ Roadmap

- [ ] **Phase 2**: Dynamic entity schemas and validation
- [ ] **Phase 3**: Advanced fact extraction and consolidation
- [ ] **Phase 4**: Multi-agent team coordination
- [ ] **Phase 5**: Specialized memory for different domains (HR, Finance, etc.)
- [ ] **Phase 6**: Advanced analytics and insights
- [ ] **Phase 7**: Production deployment tools and monitoring