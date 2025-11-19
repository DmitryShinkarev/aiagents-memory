"""Storage layer for memory-agents system.

This package provides storage clients for different databases:
- Redis for Working Memory
- MongoDB for Episodic, Semantic, and Procedural Memory
- Qdrant for vector search in Semantic Memory
- PostgreSQL for Facts Memory and audit logs

All clients are available through storage.clients subpackage.
"""

# Re-export clients for convenience
from storage.clients import (
    RedisClient,
    get_redis_client,
    MongoClient,
    get_mongo_client,
    QdrantClient,
    get_qdrant_client,
    PostgresClient,
    get_postgres_client,
)

__all__ = [
    "RedisClient",
    "get_redis_client",
    "MongoClient",
    "get_mongo_client",
    "QdrantClient",
    "get_qdrant_client",
    "PostgresClient",
    "get_postgres_client",
]





