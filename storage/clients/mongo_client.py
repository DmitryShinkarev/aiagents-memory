"""
MongoDB client for long-term memory storage.

This module provides an async MongoDB client with connection pooling,
health checks, and specialized methods for memory operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    OperationFailure,
    DuplicateKeyError
)
from pymongo import ASCENDING, DESCENDING, IndexModel, TEXT

from config.settings import get_settings

logger = logging.getLogger(__name__)


class MongoClient:
    """Async MongoDB client with connection pooling and health checks."""
    
    def __init__(
        self,
        url: str,
        database: str,
        max_pool_size: int = 100,
        server_selection_timeout_ms: int = 5000,
        connect_timeout_ms: int = 10000,
        socket_timeout_ms: int = 20000
    ):
        self.url = url
        self.database_name = database
        self.max_pool_size = max_pool_size
        self.server_selection_timeout_ms = server_selection_timeout_ms
        self.connect_timeout_ms = connect_timeout_ms
        self.socket_timeout_ms = socket_timeout_ms
        
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._health_status = "unknown"
        self._last_health_check = None
        
    async def connect(self) -> None:
        """Initialize MongoDB connection."""
        try:
            self._client = AsyncIOMotorClient(
                self.url,
                maxPoolSize=self.max_pool_size,
                serverSelectionTimeoutMS=self.server_selection_timeout_ms,
                connectTimeoutMS=self.connect_timeout_ms,
                socketTimeoutMS=self.socket_timeout_ms
            )
            
            self._database = self._client[self.database_name]
            
            # Test connection
            await self._client.admin.command('ping')
            self._health_status = "healthy"
            self._last_health_check = datetime.utcnow()
            
            # Initialize collections and indexes
            await self._initialize_collections()
            
            logger.info("MongoDB client connected successfully")
            
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client is not None:
            self._client.close()
        logger.info("MongoDB client disconnected")
    
    async def _initialize_collections(self) -> None:
        """Initialize collections and create indexes."""
        try:
            # Episodes collection
            episodes_collection = self._database.episodes
            await episodes_collection.create_indexes([
                IndexModel([("user_id", ASCENDING), ("agent_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("team_id", ASCENDING), ("scope", ASCENDING), ("importance", DESCENDING)]),
                IndexModel([("session_id", ASCENDING)]),
                IndexModel([("episode_type", ASCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("tags", ASCENDING)]),
                IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),  # TTL index
                IndexModel([("embedding", "2dsphere")], sparse=True)  # For semantic search
            ])
            
            # Semantic knowledge collection
            knowledge_collection = self._database.semantic_knowledge
            await knowledge_collection.create_indexes([
                IndexModel([("agent_id", ASCENDING), ("created_at", DESCENDING)]),
                IndexModel([("access_count", DESCENDING)]),
                IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),  # TTL index
                IndexModel([("embedding", "2dsphere")], sparse=True)  # For semantic search
            ])
            
            # Procedures collection
            procedures_collection = self._database.procedures
            await procedures_collection.create_indexes([
                IndexModel([("name", ASCENDING)], unique=True),
                IndexModel([("active", ASCENDING)]),
                IndexModel([("usage_count", DESCENDING)]),
                IndexModel([("tags", ASCENDING)])
            ])
            
            # User facts collection
            facts_collection = self._database.user_facts
            await facts_collection.create_indexes([
                IndexModel([("user_id", ASCENDING), ("key", ASCENDING)], unique=True),
                IndexModel([("fact_type", ASCENDING)]),
                IndexModel([("last_updated", DESCENDING)])
            ])
            
            # Entity schemas collection
            schemas_collection = self._database.entity_schemas
            await schemas_collection.create_indexes([
                IndexModel([("entity_type", ASCENDING), ("version", ASCENDING)], unique=True),
                IndexModel([("active", ASCENDING)]),
                IndexModel([("created_by", ASCENDING)])
            ])
            
            logger.info("MongoDB collections and indexes initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB collections: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on MongoDB connection."""
        try:
            if self._client is None:
                return {
                    "status": "unhealthy",
                    "error": "Client not connected",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Test basic operations
            start_time = datetime.utcnow()
            await self._client.admin.command('ping')
            
            # Get server info
            server_info = await self._client.server_info()
            db_stats = await self._database.command("dbStats")
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self._health_status = "healthy"
            self._last_health_check = datetime.utcnow()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "mongodb_version": server_info.get("version"),
                "database": self.database_name,
                "collections": db_stats.get("collections", 0),
                "data_size": db_stats.get("dataSize", 0),
                "index_size": db_stats.get("indexSize", 0),
                "timestamp": self._last_health_check.isoformat()
            }
            
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error(f"MongoDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @property
    def is_healthy(self) -> bool:
        """Check if MongoDB client is healthy."""
        return self._health_status == "healthy"
    
    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self._database is None:
            raise RuntimeError("MongoDB client not connected")
        return self._database
    
    # Collection access methods
    
    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Get collection by name."""
        return self.database[name]
    
    @property
    def episodes(self) -> AsyncIOMotorCollection:
        """Get episodes collection."""
        return self.get_collection("episodes")
    
    @property
    def semantic_knowledge(self) -> AsyncIOMotorCollection:
        """Get semantic knowledge collection."""
        return self.get_collection("semantic_knowledge")
    
    @property
    def procedures(self) -> AsyncIOMotorCollection:
        """Get procedures collection."""
        return self.get_collection("procedures")
    
    @property
    def user_facts(self) -> AsyncIOMotorCollection:
        """Get user facts collection."""
        return self.get_collection("user_facts")
    
    @property
    def entity_schemas(self) -> AsyncIOMotorCollection:
        """Get entity schemas collection."""
        return self.get_collection("entity_schemas")
    
    def get_entity_collection(self, entity_type: str) -> AsyncIOMotorCollection:
        """Get dynamic entity collection."""
        return self.get_collection(f"entities_{entity_type}")
    
    # Basic CRUD operations
    
    async def insert_one(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> str:
        """Insert one document."""
        coll = self.get_collection(collection)
        result = await coll.insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(
        self,
        collection: str,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Insert many documents."""
        coll = self.get_collection(collection)
        result = await coll.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    async def find_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Find one document."""
        coll = self.get_collection(collection)
        return await coll.find_one(filter, projection)
    
    async def find_many(
        self,
        collection: str,
        filter: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        skip: int = 0,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        """Find many documents."""
        coll = self.get_collection(collection)
        cursor = coll.find(filter, projection)
        
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        
        return await cursor.to_list(length=limit or None)
    
    async def update_one(
        self,
        collection: str,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> Dict[str, Any]:
        """Update one document."""
        coll = self.get_collection(collection)
        result = await coll.update_one(filter, update, upsert=upsert)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        }
    
    async def update_many(
        self,
        collection: str,
        filter: Dict[str, Any],
        update: Dict[str, Any]
    ) -> Dict[str, int]:
        """Update many documents."""
        coll = self.get_collection(collection)
        result = await coll.update_many(filter, update)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count
        }
    
    async def delete_one(
        self,
        collection: str,
        filter: Dict[str, Any]
    ) -> int:
        """Delete one document."""
        coll = self.get_collection(collection)
        result = await coll.delete_one(filter)
        return result.deleted_count
    
    async def delete_many(
        self,
        collection: str,
        filter: Dict[str, Any]
    ) -> int:
        """Delete many documents."""
        coll = self.get_collection(collection)
        result = await coll.delete_many(filter)
        return result.deleted_count
    
    async def count_documents(
        self,
        collection: str,
        filter: Dict[str, Any]
    ) -> int:
        """Count documents."""
        coll = self.get_collection(collection)
        return await coll.count_documents(filter)
    
    # Aggregation operations
    
    async def aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run aggregation pipeline."""
        coll = self.get_collection(collection)
        cursor = coll.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    # Index operations
    
    async def create_index(
        self,
        collection: str,
        index: Union[str, List[tuple], IndexModel]
    ) -> str:
        """Create index on collection."""
        coll = self.get_collection(collection)
        return await coll.create_index(index)
    
    async def create_indexes(
        self,
        collection: str,
        indexes: List[IndexModel]
    ) -> List[str]:
        """Create multiple indexes on collection."""
        coll = self.get_collection(collection)
        return await coll.create_indexes(indexes)
    
    async def list_indexes(self, collection: str) -> List[Dict[str, Any]]:
        """List indexes on collection."""
        coll = self.get_collection(collection)
        cursor = coll.list_indexes()
        return await cursor.to_list(length=None)
    
    # Transaction support
    
    async def start_session(self):
        """Start a MongoDB session for transactions."""
        if self._client is None:
            raise RuntimeError("MongoDB client not connected")
        return await self._client.start_session()

    async def with_transaction(self, callback, session=None):
        """Execute callback within a transaction."""
        if self._client is None:
            raise RuntimeError("MongoDB client not connected")
        
        if session is None:
            async with await self._client.start_session() as session:
                return await session.with_transaction(callback)
        else:
            return await session.with_transaction(callback)


# Global MongoDB client instance
_mongo_client: Optional[MongoClient] = None


async def get_mongo_client() -> MongoClient:
    """Get or create global MongoDB client instance."""
    global _mongo_client
    
    if _mongo_client is None:
        settings = get_settings()
        _mongo_client = MongoClient(
            url=settings.mongodb_url,
            database=settings.mongodb_database,
            max_pool_size=settings.mongodb_max_pool_size
        )
        await _mongo_client.connect()
    
    return _mongo_client


async def close_mongo_client():
    """Close global MongoDB client."""
    global _mongo_client
    
    if _mongo_client:
        await _mongo_client.disconnect()
        _mongo_client = None
