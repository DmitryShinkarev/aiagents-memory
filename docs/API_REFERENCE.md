# API Reference

This document provides detailed API reference for the Memory-Agents system.

## Table of Contents

- [Core Services](#core-services)
- [API Contracts](#api-contracts)
- [Memory Services](#memory-services)
- [Storage Clients](#storage-clients)
- [Configuration](#configuration)

## Core Services

### MemoryFacade

The main entry point for all memory operations.

```python
from memory_agents import get_memory_facade

memory = get_memory_facade()
```

#### Methods

##### `retrieve_comprehensive_context(agent_id, user_id=None, session_id=None, query=None, include_episodes=True, include_knowledge=True, include_facts=True, max_episodes=10, max_knowledge=10)`

Retrieve comprehensive context combining all memory types.

**Parameters:**
- `agent_id` (str): Agent identifier
- `user_id` (str, optional): User identifier
- `session_id` (str, optional): Session identifier
- `query` (str, optional): Query for semantic search
- `include_episodes` (bool): Whether to include relevant episodes
- `include_knowledge` (bool): Whether to include relevant knowledge
- `include_facts` (bool): Whether to include user facts
- `max_episodes` (int): Maximum number of episodes to include
- `max_knowledge` (int): Maximum number of knowledge items to include

**Returns:**
- `Dict[str, Any]`: Comprehensive context dictionary

##### `health_check()`

Perform health check on all memory services.

**Returns:**
- `Dict[str, Any]`: Health status of all services

##### `get_metrics()`

Get metrics from all memory services.

**Returns:**
- `Dict[str, Any]`: Metrics from all services

## API Contracts

### Common Types

#### APIVersion

```python
class APIVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
```

#### OperationStatus

```python
class OperationStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
```

#### MemoryScope

```python
class MemoryScope(str, Enum):
    USER_PRIVATE = "user_private"
    AGENT_PRIVATE = "agent_private"
    TEAM_SHARED = "team_shared"
    CROSS_TEAM = "cross_team"
    ORGANIZATION = "organization"
    PUBLIC = "public"
```

#### EpisodeScope

```python
class EpisodeScope(str, Enum):
    USER_PRIVATE = "user_private"
    AGENT_PRIVATE = "agent_private"
    TEAM_SHARED = "team_shared"
    CROSS_TEAM = "cross_team"
    ORGANIZATION = "organization"
```

#### EpisodeType

```python
class EpisodeType(str, Enum):
    INTERACTION = "interaction"
    TASK_EXECUTION = "task_execution"
    COLLABORATION = "collaboration"
    LEARNING = "learning"
    ERROR = "error"
    DECISION = "decision"
```

#### EpisodeStatus

```python
class EpisodeStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

#### SourceType

```python
class SourceType(str, Enum):
    USER_STATED = "user_stated"
    INFERRED = "inferred"
    OBSERVED = "observed"
    CONSOLIDATED = "consolidated"
    SYSTEM = "system"
```

### Entity Contracts

#### UniversalEntityWriteRequest

Request to create a new entity.

```python
class UniversalEntityWriteRequest(BaseRequest):
    entity_namespace: str
    entity_type: str
    entity_data: Dict[str, Any]
    access_scope: MemoryScope = MemoryScope.TEAM_SHARED
    allowed_teams: List[str] = []
    allowed_agents: List[str] = []
    allowed_users: List[str] = []
    business_context: Optional[Dict[str, Any]] = None
```

#### UniversalEntityUpdateRequest

Request to update an existing entity.

```python
class UniversalEntityUpdateRequest(BaseRequest):
    entity_namespace: str
    entity_type: str
    entity_id: str
    update_operation: UpdateOperation = UpdateOperation.MERGE
    update_data: Dict[str, Any]
    preconditions: Optional[Precondition] = None
    change_reason: Optional[str] = None
```

#### UniversalEntityReadRequest

Request to read an entity.

```python
class UniversalEntityReadRequest(BaseRequest):
    entity_namespace: str
    entity_type: str
    entity_id: str
    include_metadata: bool = True
    include_history: bool = False
    version: Optional[int] = None
    fields: Optional[List[str]] = None
```

#### UniversalEntityQueryRequest

Request to query entities.

```python
class UniversalEntityQueryRequest(BaseRequest, PaginationRequest):
    entity_namespace: str
    entity_type: str
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.ASC
    include_metadata: bool = True
    fields: Optional[List[str]] = None
```

### Episode Contracts

#### UniversalEpisodeWriteRequest

Request to create a new episode.

```python
class UniversalEpisodeWriteRequest(BaseRequest):
    context: EpisodeContext
    scope: EpisodeScope
    episode_type: EpisodeType
    title: str
    trajectory: List[EpisodeTrajectory]
    outcome: Optional[str] = None
    status: EpisodeStatus = EpisodeStatus.COMPLETED
    success: bool
    importance: float
    user_satisfaction: Optional[float] = None
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None
    embedding: Optional[List[float]] = None
```

#### EpisodeContext

Context information for an episode.

```python
class EpisodeContext(BaseModel):
    user_id: Optional[str] = None
    agent_id: str
    team_id: Optional[str] = None
    session_id: Optional[str] = None
    parent_episode_id: Optional[str] = None
    participating_agents: List[str] = []
```

#### EpisodeTrajectory

Single step in episode trajectory.

```python
class EpisodeTrajectory(BaseModel):
    step_id: str
    timestamp: datetime
    role: str
    action: str
    content: Any
    metadata: Optional[Dict[str, Any]] = None
```

### Knowledge Contracts

#### UniversalKnowledgeWriteRequest

Request to create or update knowledge.

```python
class UniversalKnowledgeWriteRequest(BaseRequest):
    knowledge: str
    source: SourceType
    confidence: float
    tags: List[str] = []
    supporting_evidence: List[str] = []
    temporal_scope: str = "always"
    half_life_days: Optional[int] = None
    embedding: Optional[List[float]] = None
    access_scope: str = "agent_private"
    allowed_teams: List[str] = []
    allowed_agents: List[str] = []
```

### Facts Contracts

#### UniversalFactWriteRequest

Request to create or update a user fact.

```python
class UniversalFactWriteRequest(BaseRequest):
    user_id: str
    fact_type: str
    key: str
    value: str
    confidence: float
    source: SourceType
    evidence: List[str] = []
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    force_update: bool = False
```

## Memory Services

### WorkingMemoryService

Manages short-term operational memory in Redis.

#### Methods

##### `store_session(session_id, session_data, ttl=None)`

Store session data with TTL.

**Parameters:**
- `session_id` (str): Unique session identifier
- `session_data` (Dict[str, Any]): Session data to store
- `ttl` (int, optional): Time to live in seconds

**Returns:**
- `bool`: True if successful

##### `get_session(session_id)`

Get session data.

**Parameters:**
- `session_id` (str): Session identifier

**Returns:**
- `Optional[Dict[str, Any]]`: Session data or None if not found

##### `get_context(agent_id, session_id=None, include_history=True, max_messages=50)`

Get comprehensive context for an agent.

**Parameters:**
- `agent_id` (str): Agent identifier
- `session_id` (str, optional): Session identifier
- `include_history` (bool): Whether to include conversation history
- `max_messages` (int): Maximum number of messages to include

**Returns:**
- `Dict[str, Any]`: Context dictionary

##### `cache_retrieval(query_hash, result, ttl=300)`

Cache RAG retrieval result.

**Parameters:**
- `query_hash` (str): Hash of the query
- `result` (Any): Retrieval result to cache
- `ttl` (int): Time to live in seconds

**Returns:**
- `bool`: True if successful

##### `publish_event(channel, message)`

Publish event to channel.

**Parameters:**
- `channel` (str): Channel name
- `message` (Union[str, Dict[str, Any]]): Message to publish

**Returns:**
- `int`: Number of subscribers that received the message

##### `subscribe_events(channels, timeout=None)`

Subscribe to events from channels.

**Parameters:**
- `channels` (List[str]): List of channel names
- `timeout` (int, optional): Timeout in seconds

**Returns:**
- `List[Dict[str, Any]]`: List of received messages

### EpisodicMemoryService

Manages episodic memory in MongoDB with vector search in Qdrant.

#### Methods

##### `create_episode(episode_id, context, scope, episode_type, title, trajectory, outcome=None, status=EpisodeStatus.COMPLETED, success=True, importance=0.5, user_satisfaction=None, tags=None, metadata=None, embedding=None, retention_days=None)`

Create a new episode.

**Parameters:**
- `episode_id` (str): Unique episode identifier
- `context` (EpisodeContext): Episode context
- `scope` (EpisodeScope): Episode scope
- `episode_type` (EpisodeType): Type of episode
- `title` (str): Episode title
- `trajectory` (List[EpisodeTrajectory]): Episode trajectory
- `outcome` (str, optional): Episode outcome
- `status` (EpisodeStatus): Episode status
- `success` (bool): Whether episode was successful
- `importance` (float): Episode importance (0.0-1.0)
- `user_satisfaction` (float, optional): User satisfaction rating (0.0-1.0)
- `tags` (List[str], optional): Episode tags
- `metadata` (Dict[str, Any], optional): Additional metadata
- `embedding` (List[float], optional): Episode embedding vector
- `retention_days` (int, optional): Retention period in days

**Returns:**
- `str`: Created episode ID

##### `get_episode(episode_id, include_trajectory=True)`

Get episode by ID.

**Parameters:**
- `episode_id` (str): Episode identifier
- `include_trajectory` (bool): Whether to include trajectory data

**Returns:**
- `Optional[Dict[str, Any]]`: Episode data or None if not found

##### `query_episodes(filter_by_user_id=None, filter_by_agent_id=None, filter_by_team_id=None, filter_by_session_id=None, filter_by_scope=None, filter_by_type=None, filter_by_status=None, filter_by_tags=None, time_range_start=None, time_range_end=None, min_importance=None, only_successful=None, semantic_query=None, sort_by="created_at", sort_order="desc", limit=50, offset=0)`

Query episodes with various filters.

**Parameters:**
- `filter_by_user_id` (str, optional): Filter by user ID
- `filter_by_agent_id` (str, optional): Filter by agent ID
- `filter_by_team_id` (str, optional): Filter by team ID
- `filter_by_session_id` (str, optional): Filter by session ID
- `filter_by_scope` (List[EpisodeScope], optional): Filter by scope
- `filter_by_type` (List[EpisodeType], optional): Filter by episode type
- `filter_by_status` (List[EpisodeStatus], optional): Filter by status
- `filter_by_tags` (List[str], optional): Filter by tags
- `time_range_start` (datetime, optional): Start of time range
- `time_range_end` (datetime, optional): End of time range
- `min_importance` (float, optional): Minimum importance threshold
- `only_successful` (bool, optional): Only successful episodes
- `semantic_query` (str, optional): Semantic search query
- `sort_by` (str): Field to sort by
- `sort_order` (str): Sort order (asc/desc)
- `limit` (int): Maximum number of results
- `offset` (int): Number of results to skip

**Returns:**
- `List[Dict[str, Any]]`: List of episodes

### SemanticMemoryService

Manages semantic memory with hybrid search and temporal decay.

#### Methods

##### `create_knowledge(knowledge_id, knowledge, source, confidence, agent_id, tags=None, supporting_evidence=None, temporal_scope="always", half_life_days=None, embedding=None, access_scope="agent_private", allowed_teams=None, allowed_agents=None)`

Create new knowledge item.

**Parameters:**
- `knowledge_id` (str): Unique knowledge identifier
- `knowledge` (str): Knowledge text
- `source` (SourceType): Source of the knowledge
- `confidence` (float): Confidence level (0.0-1.0)
- `agent_id` (str): Agent that owns this knowledge
- `tags` (List[str], optional): Knowledge tags
- `supporting_evidence` (List[str], optional): Episode IDs that support this knowledge
- `temporal_scope` (str): Temporal scope (always, recent, deprecated)
- `half_life_days` (int, optional): Half-life in days for temporal decay
- `embedding` (List[float], optional): Knowledge embedding vector
- `access_scope` (str): Access scope
- `allowed_teams` (List[str], optional): Teams with access
- `allowed_agents` (List[str], optional): Agents with access

**Returns:**
- `str`: Created knowledge ID

##### `semantic_search(query_embedding, agent_id, team_id=None, user_id=None, limit=10, score_threshold=None, include_temporal_decay=True, alpha=0.7)`

Perform semantic search with temporal decay.

**Parameters:**
- `query_embedding` (List[float]): Query embedding vector
- `agent_id` (str): Agent ID for access control
- `team_id` (str, optional): Team ID for access control
- `user_id` (str, optional): User ID for access control
- `limit` (int): Maximum number of results
- `score_threshold` (float, optional): Minimum similarity score
- `include_temporal_decay` (bool): Whether to include temporal decay
- `alpha` (float): Balance between dense and sparse search

**Returns:**
- `List[Dict[str, Any]]`: List of knowledge items with scores

### ProceduralMemoryService

Manages procedural memory with executable code and usage metrics.

#### Methods

##### `store_procedure(procedure_id, name, description, code, language="python", parameters_schema=None, return_schema=None, tags=None, created_by="system")`

Store a new procedure.

**Parameters:**
- `procedure_id` (str): Unique procedure identifier
- `name` (str): Procedure name (must be unique)
- `description` (str): Procedure description
- `code` (str): Executable code
- `language` (str): Programming language (python, javascript, sql)
- `parameters_schema` (Dict[str, Any], optional): JSON Schema for parameters
- `return_schema` (Dict[str, Any], optional): JSON Schema for return value
- `tags` (List[str], optional): Procedure tags
- `created_by` (str): Creator identifier

**Returns:**
- `str`: Created procedure ID

##### `execute_procedure(name, parameters=None, execution_context=None)`

Execute procedure and update metrics.

**Parameters:**
- `name` (str): Procedure name
- `parameters` (Dict[str, Any], optional): Procedure parameters
- `execution_context` (Dict[str, Any], optional): Execution context

**Returns:**
- `Dict[str, Any]`: Execution result with metadata

### FactsService

Manages user facts with full version history and conflict resolution.

#### Methods

##### `store_fact(fact_id, user_id, fact_type, key, value, confidence, source, evidence=None, valid_from=None, valid_until=None, force_update=False)`

Store or update a user fact.

**Parameters:**
- `fact_id` (str): Unique fact identifier
- `user_id` (str): User identifier
- `fact_type` (str): Type of fact (personal, location, preference, behavior, relationship)
- `key` (str): Fact key (e.g., 'name', 'city', 'favorite_color')
- `value` (str): Fact value
- `confidence` (float): Confidence level (0.0-1.0)
- `source` (SourceType): Source of the fact
- `evidence` (List[str], optional): Episode IDs that support this fact
- `valid_from` (datetime, optional): When this fact becomes valid
- `valid_until` (datetime, optional): When this fact expires
- `force_update` (bool): Force update even if confidence is lower

**Returns:**
- `str`: Created/updated fact ID

##### `get_user_profile(user_id, include_history=False, valid_at=None)`

Get comprehensive user profile.

**Parameters:**
- `user_id` (str): User identifier
- `include_history` (bool): Whether to include version history
- `valid_at` (datetime, optional): Point in time for fact validity

**Returns:**
- `Dict[str, Any]`: User profile data

## Storage Clients

### RedisClient

Async Redis client with connection pooling and health checks.

#### Methods

##### `store_session(session_id, session_data, ttl=3600)`

Store session data with TTL.

##### `get_session(session_id)`

Get session data.

##### `cache_retrieval(query_hash, result, ttl=300)`

Cache RAG retrieval result.

##### `publish(channel, message)`

Publish message to channel.

##### `subscribe(*channels)`

Subscribe to channels.

### MongoClient

Async MongoDB client with connection pooling and health checks.

#### Methods

##### `insert_one(collection, document)`

Insert one document.

##### `find_one(collection, filter, projection=None)`

Find one document.

##### `find_many(collection, filter, projection=None, sort=None, skip=0, limit=0)`

Find many documents.

##### `update_one(collection, filter, update, upsert=False)`

Update one document.

##### `delete_one(collection, filter)`

Delete one document.

##### `count_documents(collection, filter)`

Count documents.

### QdrantClient

Async Qdrant client with connection management and health checks.

#### Methods

##### `search(collection_name, query_vector, query_filter=None, limit=10, offset=0, with_payload=True, with_vectors=False, score_threshold=None)`

Search for similar vectors.

##### `upsert_points(collection_name, points)`

Upsert points to collection.

##### `delete_points(collection_name, points_selector)`

Delete points from collection.

##### `semantic_search(collection_name, query_vector, agent_id=None, team_id=None, user_id=None, limit=10, score_threshold=None)`

Perform semantic search with access control filters.

### PostgresClient

Async PostgreSQL client with connection pooling and health checks.

#### Methods

##### `log_audit_event(agent_id, action, entity_type=None, entity_id=None, team_id=None, user_id=None, session_id=None, request_id=None, payload=None, execution_time_ms=None, status="success", error_message=None)`

Log an audit event.

##### `store_idempotency_result(operation_type, idempotency_key, request_hash, response, expires_at)`

Store idempotency result.

##### `get_idempotency_result(operation_type, idempotency_key)`

Get idempotency result.

## Configuration

### Settings

The system uses Pydantic Settings for configuration management.

```python
from memory_agents import get_settings

settings = get_settings()
```

#### Redis Configuration
- `redis_url`: Redis connection URL
- `redis_session_ttl`: Session TTL in seconds
- `redis_max_connections`: Max connection pool size

#### MongoDB Configuration
- `mongodb_url`: MongoDB connection URL
- `mongodb_database`: Database name
- `mongodb_max_pool_size`: Max connection pool size

#### Qdrant Configuration
- `qdrant_url`: Qdrant server URL
- `qdrant_api_key`: API key
- `qdrant_timeout`: Request timeout

#### PostgreSQL Configuration
- `postgres_url`: PostgreSQL connection URL
- `postgres_max_pool_size`: Max connection pool size

#### Memory Configuration
- `working_memory_max_messages`: Max messages in working memory
- `episodic_memory_ttl_days`: Episodic memory TTL
- `semantic_memory_ttl_days`: Semantic memory TTL

#### Embedding Configuration
- `embedding_provider`: Embedding provider (openai, local)
- `openai_api_key`: OpenAI API key
- `embedding_model`: Embedding model name
- `embedding_batch_size`: Batch size for embeddings

#### Monitoring Configuration
- `prometheus_port`: Prometheus metrics port
- `enable_metrics`: Enable metrics collection
- `log_level`: Logging level

#### Feature Flags
- `enable_cross_agent_memory`: Enable cross-agent memory sharing
- `enable_self_reflection`: Enable self-reflection capabilities
- `enable_human_feedback`: Enable human feedback integration


