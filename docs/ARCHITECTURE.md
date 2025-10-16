# Architecture Documentation

## System Overview

Memory-Agents implements a comprehensive four-tier cognitive memory architecture inspired by human memory systems, designed for production-ready multi-agent AI systems.

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

## Core Principles

### 1. Stable API Contracts
- **Versioned APIs**: Backward-compatible interfaces
- **Idempotent Operations**: Safe retry mechanisms
- **Schema Evolution**: Independent of internal changes
- **Type Safety**: Pydantic v2 validation

### 2. Multi-Agent Architecture
- **Agent Isolation**: Separate memory spaces
- **Team Sharing**: Controlled cross-agent access
- **User Privacy**: Protected user data
- **Coordination**: Pub/Sub messaging

### 3. Human-Like Memory
- **Working Memory**: Short-term operational buffer
- **Episodic Memory**: Event-specific experiences
- **Semantic Memory**: Generalized knowledge
- **Procedural Memory**: Skills and procedures

## Memory Types

### 1. Working Memory (Redis)

**Purpose**: Short-term operational memory for active sessions

**Technology**: Redis 7.x with Streams, TTL, and Pub/Sub

**Characteristics**:
- Ultra-fast access (< 1ms)
- Automatic expiration (configurable TTL)
- Session state management
- Real-time coordination
- RAG result caching

**Data Structures**:
```
agent:{agent_id}:session:{session_id}:messages -> STREAM
agent:{agent_id}:vars:{session_id}:{key} -> STRING
agent:{agent_id}:context:{session_id} -> HASH
agent:{agent_id}:cache:rag:{query_hash} -> STRING
task:{task_id}:results -> HASH
```

**Use Cases**:
- Active conversation context
- Session state management
- Temporary variable storage
- Multi-agent coordination
- RAG result caching

### 2. Episodic Memory (MongoDB + Qdrant)

**Purpose**: Long-term memory for specific events and interactions

**Technology**: MongoDB 7.x (documents) + Qdrant (vector search)

**Characteristics**:
- Searchable by similarity
- Importance scoring (0.0-1.0)
- User satisfaction tracking
- Temporal filtering
- Contextual retrieval

**Schema**:
```javascript
// MongoDB
{
  _id: ObjectId,
  episode_id: String,
  context: {
    user_id: String,
    agent_id: String,
    team_id: String,
    session_id: String
  },
  scope: String, // user_private, team_shared, etc.
  episode_type: String, // interaction, task_execution, etc.
  title: String,
  trajectory: [{
    step_id: String,
    timestamp: DateTime,
    role: String,
    action: String,
    content: Any,
    metadata: Object
  }],
  outcome: String,
  status: String,
  success: Boolean,
  importance: Float,
  user_satisfaction: Float,
  tags: [String],
  metadata: Object,
  created_at: DateTime,
  updated_at: DateTime
}

// Qdrant
{
  id: Int,
  vector: [Float], // Episode embedding
  payload: {
    episode_id: String,
    agent_id: String,
    user_id: String,
    importance: Float,
    created_at: String
  }
}
```

**Use Cases**:
- Historical context retrieval
- Pattern recognition
- Experience replay
- Few-shot learning
- User interaction analysis

### 3. Semantic Memory (MongoDB + Qdrant)

**Purpose**: Generalized knowledge with vector search and temporal decay

**Technology**: MongoDB 7.x (documents) + Qdrant (vector search)

**Characteristics**:
- Hybrid search (dense + sparse)
- Temporal decay (half-life based)
- Confidence scoring
- Access control
- Versioning support

**Schema**:
```javascript
// MongoDB
{
  _id: ObjectId,
  knowledge_id: String,
  knowledge: String,
  source: String, // user_stated, inferred, observed, etc.
  confidence: Float,
  agent_id: String,
  tags: [String],
  supporting_evidence: [String], // Episode IDs
  temporal_scope: String, // always, recent, deprecated
  half_life_days: Int,
  access_scope: String,
  allowed_teams: [String],
  allowed_agents: [String],
  created_at: DateTime,
  updated_at: DateTime
}

// Qdrant
{
  id: Int,
  vector: [Float], // Knowledge embedding
  payload: {
    knowledge_id: String,
    agent_id: String,
    confidence: Float,
    created_at: String,
    half_life_days: Int
  }
}
```

**Use Cases**:
- RAG (Retrieval-Augmented Generation)
- Knowledge base queries
- Fact checking
- Contextual knowledge retrieval
- Temporal knowledge management

### 4. Procedural Memory (MongoDB)

**Purpose**: Skills, procedures, and executable code with usage metrics

**Technology**: MongoDB 7.x

**Characteristics**:
- Executable code storage
- Usage statistics tracking
- Success rate monitoring
- Performance metrics
- Version control

**Schema**:
```javascript
{
  _id: ObjectId,
  procedure_id: String,
  name: String, // Unique procedure name
  description: String,
  code: String,
  language: String, // python, javascript, sql
  parameters_schema: Object, // JSON Schema
  return_schema: Object, // JSON Schema
  tags: [String],
  created_by: String,
  usage_count: Int,
  success_count: Int,
  failure_count: Int,
  average_execution_time_ms: Float,
  last_used_at: DateTime,
  created_at: DateTime,
  updated_at: DateTime
}
```

**Use Cases**:
- Code execution
- Skill management
- Workflow automation
- Performance optimization
- Best practice storage

### 5. User Facts (MongoDB)

**Purpose**: Personal information with full version history and conflict resolution

**Technology**: MongoDB 7.x

**Characteristics**:
- Full version history
- Conflict resolution
- Temporal validity
- Confidence tracking
- Evidence linking

**Schema**:
```javascript
{
  _id: ObjectId,
  fact_id: String,
  user_id: String,
  fact_type: String, // personal, location, preference, etc.
  key: String, // name, city, favorite_color, etc.
  value: String,
  confidence: Float,
  source: String,
  evidence: [String], // Episode IDs
  valid_from: DateTime,
  valid_until: DateTime,
  version: Int,
  previous_version_id: ObjectId,
  created_at: DateTime,
  updated_at: DateTime
}
```

**Use Cases**:
- User profile management
- Personalization
- Preference tracking
- Relationship management
- Fact verification

## Business Logic Layer

### IdempotencyGuard

Ensures operations are executed only once using request hashing and response caching.

**Features**:
- Collision detection
- Response caching
- TTL management
- Redis/PostgreSQL fallback

### RequestValidator

Validates incoming requests against business rules and constraints.

**Features**:
- Schema validation
- Business rule enforcement
- Access control validation
- Rate limiting

## Storage Layer

### Redis Client
- Connection pooling
- Health checks
- Pub/Sub messaging
- TTL management

### MongoDB Client
- Connection pooling
- Index management
- Health checks
- Transaction support

### Qdrant Client
- Vector operations
- Collection management
- Health checks
- Access control filters

### PostgreSQL Client
- Connection pooling
- Audit logging
- Idempotency storage
- Health checks

## Memory Facade

Unified interface that orchestrates all memory services:

```python
class MemoryFacade:
    def __init__(self):
        self.working = WorkingMemoryService()
        self.episodic = EpisodicMemoryService()
        self.semantic = SemanticMemoryService()
        self.procedural = ProceduralMemoryService()
        self.facts = FactsService()
    
    async def retrieve_comprehensive_context(self, agent_id, user_id=None, **kwargs):
        """Retrieve context from all memory types"""
        # Implementation combines all memory types
```

## Access Control

### Memory Scopes
- **USER_PRIVATE**: Only accessible to the user
- **AGENT_PRIVATE**: Only accessible to the agent
- **TEAM_SHARED**: Accessible within the team
- **CROSS_TEAM**: Accessible across teams
- **ORGANIZATION**: Organization-wide access
- **PUBLIC**: Publicly accessible

### Agent Isolation
- Each agent has isolated memory space
- Controlled sharing through scopes
- User data protection
- Team-based access control

## Performance Characteristics

### Latency Targets
- **Working Memory**: < 5ms
- **Episodic Search**: < 50ms
- **Semantic Search**: < 100ms
- **Procedural Lookup**: < 10ms
- **Facts Retrieval**: < 20ms

### Throughput Targets
- **Write Operations**: 1000+ ops/sec
- **Read Operations**: 5000+ ops/sec
- **Vector Search**: 100+ queries/sec
- **Concurrent Sessions**: 10000+

## Scalability

### Horizontal Scaling
- **MongoDB**: Sharding by agent_id
- **Redis**: Cluster mode
- **Qdrant**: Distributed collections
- **PostgreSQL**: Read replicas

### Vertical Optimization
- Connection pooling
- Query optimization
- Index management
- Caching strategies

## Security

### Data Protection
- Encryption in transit (TLS)
- Encryption at rest
- Access control
- Audit logging

### Privacy
- User data isolation
- TTL for automatic cleanup
- Consent management
- Data anonymization

## Monitoring

### Health Checks
- Service availability
- Database connectivity
- Performance metrics
- Error rates

### Metrics (Prometheus)
- `memory_operations_total`
- `memory_operation_duration_seconds`
- `active_sessions_count`
- `cache_hit_rate`
- `vector_search_latency`

### Logging
- Structured logging
- Request tracing
- Error tracking
- Performance monitoring

## Future Enhancements

### Phase 2: Dynamic Entities
- Entity schema registry
- Dynamic validation
- Universal entity contracts
- Schema evolution

### Phase 3: Advanced Features
- Multi-modal memory
- Advanced consolidation
- Cross-agent learning
- Human feedback integration

### Phase 4: Production Features
- Advanced monitoring
- Auto-scaling
- Disaster recovery
- Compliance tools