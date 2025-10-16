# Getting Started

This guide will help you understand the Memory-Agents system and get started with building memory-aware AI agents.

## What is Memory-Agents?

Memory-Agents is a comprehensive memory management system for multi-agent AI systems that implements four cognitive memory types inspired by human memory systems:

- **Working Memory**: Short-term operational memory for active sessions
- **Episodic Memory**: Long-term memory for specific events and interactions
- **Semantic Memory**: Generalized knowledge with vector search and temporal decay
- **Procedural Memory**: Skills, procedures, and executable code
- **User Facts**: Personal information with full version history

## Key Features

- 🧠 **Human-like Memory**: Four cognitive memory types
- 🔒 **Stable API Contracts**: Versioned, backward-compatible interfaces
- ⚡ **Idempotent Operations**: Safe retry mechanisms
- 🕒 **Temporal Decay**: Knowledge naturally ages over time
- 👥 **Multi-Agent Support**: Isolated memory spaces with controlled sharing
- 🔍 **Vector Search**: High-performance semantic search
- 📊 **Health Monitoring**: Comprehensive metrics and health checks
- 🔄 **Real-time Coordination**: Pub/Sub messaging between agents

## Architecture Overview

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

## Quick Start

### 1. Installation

```bash
git clone https://github.com/your-org/memory-agents.git
cd memory-agents
pip install -r requirements.txt
```

### 2. Start Dependencies

```bash
docker-compose up -d
```

### 3. Configure Environment

Create `.env` file:

```bash
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017
QDRANT_URL=http://localhost:6333
POSTGRES_URL=postgresql://postgres:password@localhost:5432/memory_logs
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Basic Usage

```python
import asyncio
from memory_agents import get_memory_facade

async def main():
    memory = get_memory_facade()
    
    # Create an episode
    await memory.create_episode(
        episode_id="ep_001",
        context={"agent_id": "agent_001", "user_id": "user_123"},
        scope="user_private",
        episode_type="interaction",
        title="User interaction",
        trajectory=[{
            "step_id": "1",
            "timestamp": "2024-01-01T10:00:00Z",
            "role": "user",
            "action": "message",
            "content": "Hello"
        }],
        success=True,
        importance=0.5
    )
    
    # Get context
    context = await memory.retrieve_comprehensive_context(
        agent_id="agent_001",
        user_id="user_123"
    )
    
    print(f"Retrieved context with {len(context.get('episodes', []))} episodes")

asyncio.run(main())
```

## Memory Types Deep Dive

### Working Memory

Working memory is your agent's short-term operational buffer, similar to human working memory.

**Use Cases**:
- Active conversation context
- Session state management
- Temporary variable storage
- Multi-agent coordination

**Example**:
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

### Episodic Memory

Episodic memory stores specific events and interactions, like human episodic memory.

**Use Cases**:
- Historical context retrieval
- Pattern recognition
- Experience replay
- Few-shot learning

**Example**:
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

### Semantic Memory

Semantic memory stores generalized knowledge with vector search and temporal decay.

**Use Cases**:
- RAG (Retrieval-Augmented Generation)
- Knowledge base queries
- Fact checking
- Contextual knowledge retrieval

**Example**:
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

### Procedural Memory

Procedural memory stores skills, procedures, and executable code.

**Use Cases**:
- Code execution
- Skill management
- Workflow automation
- Performance optimization

**Example**:
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

### User Facts

User facts store personal information with full version history and conflict resolution.

**Use Cases**:
- User profile management
- Personalization
- Preference tracking
- Relationship management

**Example**:
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

Memory-Agents supports multiple agents working together through pub/sub messaging.

**Example**:
```python
# Agent 1 publishes a task
await memory.working.publish_event(
    channel="task:analysis",
    message={
        "task_id": "task_001",
        "type": "analyze_billing_issue",
        "data": {"user_id": "user_123", "issue": "duplicate charge"}
    }
)

# Agent 2 subscribes to the task
events = await memory.working.subscribe_events(
    channels=["task:analysis"],
    timeout=10
)

# Agent 3 gets the results
results = await memory.working.get_task_results("task_001", timeout=30)
```

## Access Control

Memory-Agents provides granular access control through memory scopes:

- **USER_PRIVATE**: Only accessible to the user
- **AGENT_PRIVATE**: Only accessible to the agent
- **TEAM_SHARED**: Accessible within the team
- **CROSS_TEAM**: Accessible across teams
- **ORGANIZATION**: Organization-wide access
- **PUBLIC**: Publicly accessible

**Example**:
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

## Idempotent Operations

All write operations are idempotent, meaning they can be safely retried without side effects.

**Example**:
```python
# Create episode with idempotency key
idempotency_key = "create_episode_001"

# First call - creates the episode
result1 = await memory.create_episode(
    episode_id="ep_001",
    # ... parameters
    idempotency_key=idempotency_key
)

# Second call with same idempotency key - returns cached result
result2 = await memory.create_episode(
    episode_id="ep_001",
    # ... same parameters
    idempotency_key=idempotency_key
)

# Both calls return the same result
assert result1 == result2
```

## Health Monitoring

Memory-Agents provides comprehensive health monitoring and metrics.

**Example**:
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

## Best Practices

### 1. Use Appropriate Memory Types

- **Working Memory**: For active sessions and temporary data
- **Episodic Memory**: For specific events and interactions
- **Semantic Memory**: For generalized knowledge and facts
- **Procedural Memory**: For skills and executable code
- **User Facts**: For personal information and preferences

### 2. Set Appropriate Scopes

- Use `user_private` for user-specific data
- Use `agent_private` for agent-specific data
- Use `team_shared` for team collaboration
- Use `organization` for organization-wide data

### 3. Use Idempotency Keys

Always use idempotency keys for write operations to ensure safe retries.

### 4. Monitor Performance

- Check health status regularly
- Monitor metrics and logs
- Set up alerting for critical issues

### 5. Handle Errors Gracefully

- Implement proper error handling
- Use retry mechanisms
- Log errors for debugging

## Common Patterns

### 1. Context-Aware Responses

```python
async def get_context_aware_response(agent_id, user_id, message):
    # Get comprehensive context
    context = await memory.retrieve_comprehensive_context(
        agent_id=agent_id,
        user_id=user_id
    )
    
    # Use context to generate response
    episodes = context.get("episodes", [])
    knowledge = context.get("knowledge", [])
    facts = context.get("facts", [])
    
    # Generate response based on context
    if episodes:
        return f"I remember our previous conversation. {message}"
    elif knowledge:
        return f"Based on my knowledge, {message}"
    else:
        return f"I understand. {message}"
```

### 2. Learning from Interactions

```python
async def learn_from_interaction(agent_id, user_id, interaction):
    # Store the interaction as an episode
    await memory.create_episode(
        episode_id=f"ep_{int(time.time())}",
        context={"agent_id": agent_id, "user_id": user_id},
        scope="user_private",
        episode_type="interaction",
        title="User interaction",
        trajectory=interaction["trajectory"],
        success=interaction["success"],
        importance=interaction["importance"]
    )
    
    # Extract knowledge if important
    if interaction["importance"] > 0.8:
        await memory.create_knowledge(
            knowledge_id=f"kb_{int(time.time())}",
            knowledge=interaction["summary"],
            source="inferred",
            confidence=0.8,
            agent_id=agent_id
        )
```

### 3. Multi-Agent Collaboration

```python
async def collaborate_on_task(agents, task):
    # Publish task to all agents
    await memory.working.publish_event(
        channel="task:collaboration",
        message={
            "task_id": task["id"],
            "type": task["type"],
            "data": task["data"],
            "assigned_agents": agents
        }
    )
    
    # Collect results from all agents
    results = []
    for agent in agents:
        result = await memory.working.get_task_results(
            task["id"], 
            timeout=30
        )
        results.append(result)
    
    # Consolidate results
    consolidated_result = consolidate_results(results)
    
    # Store consolidated result
    await memory.create_knowledge(
        knowledge_id=f"kb_consolidated_{task['id']}",
        knowledge=consolidated_result,
        source="consolidated",
        confidence=0.9,
        agent_id="system"
    )
    
    return consolidated_result
```

## Next Steps

1. **Explore Examples**: Check out [Examples](EXAMPLES.md) for comprehensive usage examples
2. **Read API Reference**: See [API Reference](API_REFERENCE.md) for detailed API documentation
3. **Deploy to Production**: Follow the [Deployment Guide](DEPLOYMENT.md) for production setup
4. **Understand Architecture**: Read [Architecture](ARCHITECTURE.md) for system design details

## Getting Help

- 📖 **Documentation**: [docs/](docs/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/memory-agents/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-org/memory-agents/discussions)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.