"""System initialization utilities."""

from redis.asyncio import Redis
from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import AsyncQdrantClient
import asyncpg

from config.settings import get_settings
from storage.redis.working_store import RedisWorkingMemory
from storage.mongodb.episodic_store import EpisodicMemoryStore
from storage.mongodb.semantic_store import SemanticMemoryStore
from storage.mongodb.procedural_store import ProceduralMemoryStore
from storage.postgresql.event_logger import EventLogger
from core.memory_orchestrator import MemoryOrchestrator


async def initialize_memory_system(
    agent_id: str = "default_agent",
    settings = None
) -> MemoryOrchestrator:
    """
    Initialize complete memory system.
    
    Args:
        agent_id: Agent identifier
        settings: Optional settings override
        
    Returns:
        Initialized MemoryOrchestrator
    """
    if settings is None:
        settings = get_settings()
    
    # Initialize Redis
    redis_client = Redis.from_url(
        settings.redis_url,
        max_connections=settings.redis_max_connections,
        decode_responses=False
    )
    
    # Initialize MongoDB
    mongo_client = AsyncIOMotorClient(
        settings.mongodb_url,
        maxPoolSize=settings.mongodb_max_pool_size
    )
    
    # Initialize Qdrant (optional)
    qdrant_client = None
    if settings.qdrant_url:
        try:
            qdrant_client = AsyncQdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=settings.qdrant_timeout
            )
        except Exception as e:
            print(f"Warning: Could not initialize Qdrant: {e}")
    
    # Initialize PostgreSQL
    pg_pool = None
    if settings.postgres_url:
        try:
            pg_pool = await asyncpg.create_pool(
                settings.postgres_url,
                min_size=5,
                max_size=settings.postgres_max_pool_size
            )
        except Exception as e:
            print(f"Warning: Could not initialize PostgreSQL: {e}")
    
    # Create storage instances
    working_memory = RedisWorkingMemory(redis_client, agent_id)
    
    episodic_store = EpisodicMemoryStore(
        mongo_client,
        db_name=settings.mongodb_database
    )
    await episodic_store.initialize()
    
    semantic_store = SemanticMemoryStore(
        mongo_client,
        qdrant_client=qdrant_client,
        db_name=settings.mongodb_database
    )
    await semantic_store.initialize(vector_size=settings.semantic_memory_vector_size)
    
    procedural_store = ProceduralMemoryStore(
        mongo_client,
        db_name=settings.mongodb_database
    )
    await procedural_store.initialize()
    
    event_logger = None
    if pg_pool:
        event_logger = EventLogger(pg_pool)
        await event_logger.initialize()
    
    # Create orchestrator
    orchestrator = MemoryOrchestrator(
        working_memory=working_memory,
        episodic_store=episodic_store,
        semantic_store=semantic_store,
        procedural_store=procedural_store,
        event_logger=event_logger,
        embedding_service=None  # User should provide their own
    )
    
    return orchestrator


