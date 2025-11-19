"""
Memory-Agents: Comprehensive Memory System for Multi-Agent Systems

A production-ready memory management system implementing four cognitive memory types:
- Working Memory (Redis)
- Episodic Memory (MongoDB)
- Semantic Memory (MongoDB + Qdrant)
- Procedural Memory (MongoDB)

Usage:
    from memory_agents import get_memory_facade
    
    memory = get_memory_facade()
    
    # Create an episode
    await memory.create_episode(
        episode_id="ep_001",
        context={"agent_id": "agent_001", "user_id": "user_001"},
        scope="user_private",
        episode_type="interaction",
        title="User interaction",
        trajectory=[{"step_id": "1", "timestamp": "2024-01-01T10:00:00Z", "role": "user", "action": "message", "content": "Hello!"}]
    )
    
    # Retrieve comprehensive context
    context = await memory.retrieve_comprehensive_context(
        agent_id="agent_001",
        user_id="user_001"
    )
"""

__version__ = "0.2.0"
__author__ = "Memory-Agents Team"

# Core services
from services.memory_facade import MemoryFacade, get_memory_facade
from config.settings import Settings, get_settings

# API contracts
from api.contracts.common import (
    APIVersion,
    OperationStatus,
    MemoryScope,
    EpisodeScope,
    EpisodeType,
    EpisodeStatus,
    SourceType,
    FieldType,
    UpdateOperation,
    SortOrder
)

from api.contracts.entity import (
    UniversalEntityWriteRequest,
    UniversalEntityUpdateRequest,
    UniversalEntityReadRequest,
    UniversalEntityQueryRequest,
    UniversalEntityResponse
)

from api.contracts.episode import (
    UniversalEpisodeWriteRequest,
    UniversalEpisodeQueryRequest,
    UniversalEpisodeResponse,
    EpisodeContext,
    EpisodeTrajectory
)

from api.contracts.knowledge import (
    UniversalKnowledgeWriteRequest,
    UniversalKnowledgeQueryRequest,
    UniversalKnowledgeResponse
)

from api.contracts.facts import (
    UniversalFactWriteRequest,
    UniversalFactQueryRequest,
    UniversalFactResponse
)

# Business logic
from business.idempotency import IdempotencyGuard, idempotent_operation
from business.validation import RequestValidator, ValidationError

# Domain services
from domain.memory.working import WorkingMemoryService
from domain.memory.episodic import EpisodicMemoryService
from domain.memory.semantic import SemanticMemoryService
from domain.memory.procedural import ProceduralMemoryService
from domain.memory.facts import FactsService

# Storage clients
from storage.clients.redis_client import RedisClient, get_redis_client
from storage.clients.mongo_client import MongoClient, get_mongo_client
from storage.clients.qdrant_client import QdrantClient, get_qdrant_client
from storage.clients.postgres_client import PostgresClient, get_postgres_client

__all__ = [
    # Core services
    "MemoryFacade",
    "get_memory_facade",
    
    # Config
    "Settings",
    "get_settings",
    
    # API contracts - Common
    "APIVersion",
    "OperationStatus",
    "MemoryScope",
    "EpisodeScope",
    "EpisodeType",
    "EpisodeStatus",
    "SourceType",
    "FieldType",
    "UpdateOperation",
    "SortOrder",
    
    # API contracts - Entity
    "UniversalEntityWriteRequest",
    "UniversalEntityUpdateRequest",
    "UniversalEntityReadRequest",
    "UniversalEntityQueryRequest",
    "UniversalEntityResponse",
    
    # API contracts - Episode
    "UniversalEpisodeWriteRequest",
    "UniversalEpisodeQueryRequest",
    "UniversalEpisodeResponse",
    "EpisodeContext",
    "EpisodeTrajectory",
    
    # API contracts - Knowledge
    "UniversalKnowledgeWriteRequest",
    "UniversalKnowledgeQueryRequest",
    "UniversalKnowledgeResponse",
    
    # API contracts - Facts
    "UniversalFactWriteRequest",
    "UniversalFactQueryRequest",
    "UniversalFactResponse",
    
    # Business logic
    "IdempotencyGuard",
    "idempotent_operation",
    "RequestValidator",
    "ValidationError",
    
    # Domain services
    "WorkingMemoryService",
    "EpisodicMemoryService",
    "SemanticMemoryService",
    "ProceduralMemoryService",
    "FactsService",
    
    # Storage clients
    "RedisClient",
    "get_redis_client",
    "MongoClient",
    "get_mongo_client",
    "QdrantClient",
    "get_qdrant_client",
    "PostgresClient",
    "get_postgres_client",
]





