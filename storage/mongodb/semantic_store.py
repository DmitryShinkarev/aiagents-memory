"""MongoDB + Qdrant hybrid semantic memory implementation."""

import hashlib
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("Warning: Qdrant client not available. Vector search will be limited.")

from models.memory.semantic import SemanticKnowledge, KnowledgeType, SEMANTIC_MEMORY_INDEXES
from config.settings import get_settings


class SemanticMemoryStore:
    """Semantic memory storage using MongoDB (data) + Qdrant (vectors)."""
    
    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        qdrant_client: Optional[AsyncQdrantClient] = None,
        db_name: Optional[str] = None,
        collection_name: str = "semantic_memory"
    ):
        """
        Initialize semantic memory store.
        
        Args:
            mongo_client: Motor async MongoDB client
            qdrant_client: Optional Qdrant client for vector search
            db_name: Database name
            collection_name: MongoDB collection and Qdrant collection name
        """
        settings = get_settings()
        self.db: AsyncIOMotorDatabase = mongo_client[db_name or settings.mongodb_database]
        self.mongo_collection = self.db[collection_name]
        self.qdrant = qdrant_client
        self.qdrant_collection = collection_name
        self.settings = settings
    
    async def initialize(self, vector_size: Optional[int] = None):
        """
        Initialize storage (create indexes and collections).
        
        Args:
            vector_size: Embedding vector size (default from settings)
        """
        # Create MongoDB indexes
        for index_spec in SEMANTIC_MEMORY_INDEXES:
            if len(index_spec) == 1:
                await self.mongo_collection.create_index(index_spec[0])
            else:
                await self.mongo_collection.create_index(index_spec[0])
        
        # TTL index
        ttl_seconds = self.settings.semantic_memory_ttl_days * 24 * 3600
        await self.mongo_collection.create_index(
            "created_at",
            expireAfterSeconds=ttl_seconds
        )
        
        # Initialize Qdrant collection if available
        if self.qdrant and QDRANT_AVAILABLE:
            vector_size = vector_size or self.settings.semantic_memory_vector_size
            
            try:
                # Check if collection exists
                collections = await self.qdrant.get_collections()
                collection_exists = any(
                    col.name == self.qdrant_collection 
                    for col in collections.collections
                )
                
                if not collection_exists:
                    await self.qdrant.create_collection(
                        collection_name=self.qdrant_collection,
                        vectors_config=VectorParams(
                            size=vector_size,
                            distance=Distance.COSINE
                        )
                    )
            except Exception as e:
                print(f"Warning: Could not initialize Qdrant collection: {e}")
    
    async def add_knowledge(
        self,
        knowledge: SemanticKnowledge,
        embedding: List[float]
    ) -> str:
        """
        Add knowledge to semantic memory.
        
        Args:
            knowledge: Knowledge object
            embedding: Vector embedding
            
        Returns:
            Knowledge ID
        """
        # Save to MongoDB
        knowledge_dict = knowledge.model_dump(by_alias=True, exclude_none=True)
        
        # Remove _id if None
        if knowledge_dict.get("_id") is None:
            knowledge_dict.pop("_id", None)
        
        result = await self.mongo_collection.insert_one(knowledge_dict)
        doc_id = str(result.inserted_id)
        
        # Index in Qdrant if available
        if self.qdrant and QDRANT_AVAILABLE:
            try:
                point_id = self._generate_point_id(doc_id)
                
                await self.qdrant.upsert(
                    collection_name=self.qdrant_collection,
                    points=[
                        PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload={
                                "mongo_id": doc_id,
                                "namespace": knowledge.namespace,
                                "knowledge_type": knowledge.knowledge_type.value,
                                "tags": knowledge.tags,
                                "confidence": knowledge.confidence
                            }
                        )
                    ]
                )
            except Exception as e:
                print(f"Warning: Could not index in Qdrant: {e}")
        
        return doc_id
    
    async def get_knowledge(self, knowledge_id: str) -> Optional[SemanticKnowledge]:
        """Get knowledge by ID."""
        doc = await self.mongo_collection.find_one({"_id": ObjectId(knowledge_id)})
        return SemanticKnowledge(**doc) if doc else None
    
    async def semantic_search(
        self,
        query_embedding: List[float],
        namespace: Optional[str] = None,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        limit: int = 5,
        min_confidence: float = 0.5
    ) -> List[SemanticKnowledge]:
        """
        Semantic search using vector similarity.
        
        Args:
            query_embedding: Query vector
            namespace: Optional namespace filter
            knowledge_types: Optional type filter
            limit: Maximum results
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of matching knowledge items
        """
        if not self.qdrant or not QDRANT_AVAILABLE:
            # Fallback to text search
            return await self.text_search("", namespace=namespace, limit=limit)
        
        try:
            # Build Qdrant filter
            filter_conditions = []
            
            filter_conditions.append(
                FieldCondition(
                    key="confidence",
                    range={"gte": min_confidence}
                )
            )
            
            if namespace:
                filter_conditions.append(
                    FieldCondition(
                        key="namespace",
                        match=MatchValue(value=namespace)
                    )
                )
            
            if knowledge_types:
                filter_conditions.append(
                    FieldCondition(
                        key="knowledge_type",
                        match=MatchValue(any=[kt.value for kt in knowledge_types])
                    )
                )
            
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Search in Qdrant
            search_result = await self.qdrant.search(
                collection_name=self.qdrant_collection,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                with_payload=True
            )
            
            # Get full documents from MongoDB
            mongo_ids = [ObjectId(hit.payload["mongo_id"]) for hit in search_result]
            
            cursor = self.mongo_collection.find({"_id": {"$in": mongo_ids}})
            documents = await cursor.to_list(length=limit)
            
            # Update access stats
            await self._update_access_stats([str(doc["_id"]) for doc in documents])
            
            return [SemanticKnowledge(**doc) for doc in documents]
        
        except Exception as e:
            print(f"Vector search failed: {e}. Using fallback.")
            return await self.text_search("", namespace=namespace, limit=limit)
    
    async def text_search(
        self,
        query: str,
        namespace: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[SemanticKnowledge]:
        """
        Text-based search in MongoDB.
        
        Args:
            query: Search query
            namespace: Optional namespace filter
            tags: Optional tag filter
            limit: Maximum results
            
        Returns:
            List of matching knowledge items
        """
        search_filter: Dict = {}
        
        if query:
            search_filter["$text"] = {"$search": query}
        
        if namespace:
            search_filter["namespace"] = namespace
        
        if tags:
            search_filter["tags"] = {"$in": tags}
        
        cursor = self.mongo_collection.find(search_filter)
        
        if query:
            cursor = cursor.sort([("score", {"$meta": "textScore"})])
        else:
            cursor = cursor.sort("access_count", -1)
        
        cursor = cursor.limit(limit)
        
        documents = await cursor.to_list(length=limit)
        return [SemanticKnowledge(**doc) for doc in documents]
    
    async def hybrid_search(
        self,
        query_embedding: List[float],
        keyword_query: str,
        namespace: Optional[str] = None,
        limit: int = 10
    ) -> List[SemanticKnowledge]:
        """
        Hybrid search combining vector and text search.
        
        Args:
            query_embedding: Query vector
            keyword_query: Text query
            namespace: Optional namespace filter
            limit: Maximum results
            
        Returns:
            Combined and ranked results
        """
        # Get results from both searches
        vector_results = await self.semantic_search(
            query_embedding,
            namespace=namespace,
            limit=limit * 2
        )
        
        text_results = await self.text_search(
            keyword_query,
            namespace=namespace,
            limit=limit * 2
        )
        
        # Merge results (simple deduplication by ID)
        seen_ids = set()
        merged = []
        
        # Interleave results
        max_len = max(len(vector_results), len(text_results))
        for i in range(max_len):
            if i < len(vector_results):
                item = vector_results[i]
                if item.id not in seen_ids:
                    merged.append(item)
                    seen_ids.add(item.id)
            
            if i < len(text_results):
                item = text_results[i]
                if item.id not in seen_ids:
                    merged.append(item)
                    seen_ids.add(item.id)
            
            if len(merged) >= limit:
                break
        
        return merged[:limit]
    
    async def update_knowledge(
        self,
        knowledge_id: str,
        updates: Dict,
        new_embedding: Optional[List[float]] = None
    ):
        """
        Update knowledge with versioning.
        
        Args:
            knowledge_id: Knowledge ID
            updates: Update dictionary
            new_embedding: Optional new embedding
        """
        # Get current version
        current = await self.mongo_collection.find_one({"_id": ObjectId(knowledge_id)})
        
        if not current:
            raise ValueError(f"Knowledge {knowledge_id} not found")
        
        # Create new version
        new_version = current.get("version", 1) + 1
        
        updates.update({
            "version": new_version,
            "previous_version_id": knowledge_id,
            "updated_at": datetime.utcnow()
        })
        
        # Update MongoDB
        await self.mongo_collection.update_one(
            {"_id": ObjectId(knowledge_id)},
            {"$set": updates}
        )
        
        # Update Qdrant if embedding changed
        if new_embedding and self.qdrant and QDRANT_AVAILABLE:
            try:
                point_id = self._generate_point_id(knowledge_id)
                
                await self.qdrant.set_payload(
                    collection_name=self.qdrant_collection,
                    payload={"version": new_version},
                    points=[point_id]
                )
                
                # Update vector if provided
                await self.qdrant.update_vectors(
                    collection_name=self.qdrant_collection,
                    points=[
                        PointStruct(
                            id=point_id,
                            vector=new_embedding
                        )
                    ]
                )
            except Exception as e:
                print(f"Warning: Could not update Qdrant: {e}")
    
    async def delete_knowledge(self, knowledge_id: str):
        """Delete knowledge from both MongoDB and Qdrant."""
        # Delete from MongoDB
        await self.mongo_collection.delete_one({"_id": ObjectId(knowledge_id)})
        
        # Delete from Qdrant
        if self.qdrant and QDRANT_AVAILABLE:
            try:
                point_id = self._generate_point_id(knowledge_id)
                await self.qdrant.delete(
                    collection_name=self.qdrant_collection,
                    points_selector=[point_id]
                )
            except Exception as e:
                print(f"Warning: Could not delete from Qdrant: {e}")
    
    async def _update_access_stats(self, knowledge_ids: List[str]):
        """Update access statistics for knowledge items."""
        await self.mongo_collection.update_many(
            {"_id": {"$in": [ObjectId(kid) for kid in knowledge_ids]}},
            {
                "$inc": {"access_count": 1},
                "$set": {"last_accessed": datetime.utcnow()}
            }
        )
    
    def _generate_point_id(self, mongo_id: str) -> int:
        """Generate numeric Qdrant point ID from MongoDB ObjectId."""
        # Use first 16 hex chars of MD5 hash as integer
        return int(hashlib.md5(mongo_id.encode()).hexdigest()[:16], 16)


