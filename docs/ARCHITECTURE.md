# Architecture Documentation

## System Overview

Memory-Agents implements a four-tier cognitive memory architecture inspired by human memory systems:

```
┌─────────────────────────────────────────────────────────────┐
│                    USER / API LAYER                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│               MEMORY ORCHESTRATOR                            │
│  - Routing Logic                                             │
│  - Consistency Management                                    │
│  - Priority & Relevance Scoring                              │
└──────┬────────────┬────────────┬─────────────┬──────────────┘
       │            │            │             │
   ┌───▼───┐   ┌───▼───┐   ┌────▼────┐   ┌────▼─────┐
   │Working│   │Episode│   │Semantic │   │Procedural│
   │Memory │   │ Memory│   │ Memory  │   │  Memory  │
   │(Redis)│   │(Mongo)│   │ (Mongo  │   │ (Mongo)  │
   │       │   │       │   │ +Qdrant)│   │          │
   └───────┘   └───────┘   └─────────┘   └──────────┘
```

## Memory Types

### 1. Working Memory (Redis)

**Purpose**: Short-term buffer for active conversations and tasks

**Technology**: Redis 7.x with Streams and TTL

**Characteristics**:
- Fast access (< 1ms)
- Automatic expiration (1 hour default)
- Compression when threshold reached
- Temporary variables support

**Data Structures**:
```
agent:{agent_id}:session:{session_id}:messages -> STREAM
agent:{agent_id}:vars:{session_id}:{key} -> STRING
agent:{agent_id}:context:{session_id} -> HASH
```

**Use Cases**:
- Active conversation context
- Session state management
- Quick variable storage
- Real-time coordination

### 2. Episodic Memory (MongoDB)

**Purpose**: Historical interactions and events

**Technology**: MongoDB 7.x with Atlas Vector Search

**Characteristics**:
- Searchable by similarity
- Importance scoring
- Temporal decay
- User feedback integration

**Schema**:
```javascript
{
  _id: ObjectId,
  agent_id: String,
  session_id: String,
  messages: [EpisodeMessage],
  summary: String,
  importance: Float,
  relevance_decay: Float,
  tags: [String],
  embedding: [Float],
  created_at: DateTime
}
```

**Use Cases**:
- Few-shot learning
- Pattern recognition
- Historical context
- Experience replay

### 3. Semantic Memory (MongoDB + Qdrant)

**Purpose**: Facts, knowledge, and definitions

**Technology**: MongoDB (data) + Qdrant (vectors)

**Characteristics**:
- Hybrid search (vector + text)
- Versioning support
- Access tracking
- Confidence scoring

**Schema**:
```javascript
// MongoDB
{
  _id: ObjectId,
  content: String,
  knowledge_type: Enum,
  confidence: Float,
  namespace: String,
  tags: [String],
  entities: [String],
  version: Int
}

// Qdrant
{
  id: Int,
  vector: [Float],
  payload: {
    mongo_id: String,
    namespace: String,
    confidence: Float
  }
}
```

**Use Cases**:
- RAG (Retrieval-Augmented Generation)
- Knowledge base
- Fact checking
- Entity relationships

### 4. Procedural Memory (MongoDB)

**Purpose**: Skills, templates, and workflows

**Technology**: MongoDB 7.x

**Characteristics**:
- Usage statistics
- Success rate tracking
- Version control
- Performance metrics

**Schema**:
```javascript
{
  _id: ObjectId,
  name: String,
  procedure_type: Enum,
  content: String,
  parameters: [Parameter],
  usage_count: Int,
  success_rate: Float,
  average_execution_time: Float
}
```

**Use Cases**:
- Prompt templates
- Tool usage patterns
- Workflows
- Best practices

## Memory Orchestrator

Central coordinator implementing:

### Context Retrieval

Priority-based memory access with token budgeting:

```python
score = importance × decay × type_weight
```

### Session Consolidation

Pattern 4.9 Self-reflection:
1. Summarize session
2. Extract facts
3. Save to long-term memory
4. Clear working memory

### Periodic Maintenance

- Relevance decay application
- Cleanup unused procedures
- Archive old logs

## Logging Layer (PostgreSQL)

**Purpose**: Audit trail and analytics

**Schema**:
```sql
events (
  event_id UUID,
  timestamp TIMESTAMPTZ,
  event_type VARCHAR,
  agent_id VARCHAR,
  action VARCHAR,
  resource VARCHAR,
  details JSONB,
  latency_ms FLOAT,
  status VARCHAR
)
```

**Analytics**:
- Performance metrics
- Error tracking
- Resource usage
- Cost analysis

## Design Patterns

### Pattern 4.4: RAG
Semantic memory with vector search enables retrieval-augmented generation.

### Pattern 4.9: Self-reflection
Session consolidation implements agent self-reflection.

### Pattern 4.10: Cross-reflection
Shared memory enables inter-agent reflection.

### Pattern 4.11: Human reflection
User feedback integration in episodic memory.

## Scalability

### Horizontal Scaling
- MongoDB sharding by `agent_id`
- Redis Cluster for distributed cache
- Qdrant cluster for vector search

### Vertical Optimization
- Lua scripts for atomic Redis operations
- Compound indexes in MongoDB
- Query result caching
- Connection pooling

### Performance Targets
- Working memory: < 5ms
- Episodic search: < 50ms
- Semantic search: < 100ms
- Procedural lookup: < 10ms

## Security Considerations

1. **Authentication**: API key / token-based
2. **Isolation**: Namespace and agent_id separation
3. **Encryption**: TLS for data in transit
4. **Audit**: Complete event logging
5. **Privacy**: TTL for automatic cleanup

## Monitoring

### Metrics (Prometheus)
- `memory_operations_total`
- `memory_operation_latency_seconds`
- `memory_size_bytes`

### Alerts
- High error rate
- Slow queries
- Memory pressure
- Cost anomalies

## Future Enhancements

1. **ClickHouse Integration**: For high-volume analytics
2. **Distributed Tracing**: OpenTelemetry integration
3. **Advanced RAG**: Hybrid search optimization
4. **Auto-compression**: ML-based context summarization
5. **Multi-modal Memory**: Image/audio embeddings





