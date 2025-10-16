"""
Qdrant client for high-performance vector search.

This module provides an async Qdrant client with connection management,
health checks, and specialized methods for semantic search operations.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple

from qdrant_client import QdrantClient as SyncQdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition,
    MatchValue, Range, SearchRequest, ScrollRequest, CountRequest
)

from ...config.settings import get_settings

logger = logging.getLogger(__name__)


class QdrantClient:
    """Async Qdrant client with connection management and health checks."""
    
    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        prefer_grpc: bool = False
    ):
        self.url = url
        self.api_key = api_key
        self.timeout = timeout
        self.prefer_grpc = prefer_grpc
        
        self._client: Optional[SyncQdrantClient] = None
        self._health_status = "unknown"
        self._last_health_check = None
        
    async def connect(self) -> None:
        """Initialize Qdrant connection."""
        try:
            self._client = SyncQdrantClient(
                url=self.url,
                api_key=self.api_key,
                timeout=self.timeout,
                prefer_grpc=self.prefer_grpc
            )
            
            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None, self._client.get_collections
            )
            
            self._health_status = "healthy"
            self._last_health_check = datetime.utcnow()
            
            # Initialize collections
            await self._initialize_collections()
            
            logger.info("Qdrant client connected successfully")
            
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Qdrant connection."""
        if self._client:
            self._client.close()
        logger.info("Qdrant client disconnected")
    
    async def _initialize_collections(self) -> None:
        """Initialize collections for semantic search."""
        try:
            # Semantic memory collection
            await self._create_collection_if_not_exists(
                collection_name="semantic_memory",
                vector_size=1536,  # OpenAI embedding size
                distance=Distance.COSINE
            )
            
            # Episodes collection (optional)
            await self._create_collection_if_not_exists(
                collection_name="episodes",
                vector_size=1536,
                distance=Distance.COSINE
            )
            
            logger.info("Qdrant collections initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collections: {e}")
            raise
    
    async def _create_collection_if_not_exists(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE
    ) -> None:
        """Create collection if it doesn't exist."""
        try:
            collections = await asyncio.get_event_loop().run_in_executor(
                None, self._client.get_collections
            )
            
            existing_collections = [col.name for col in collections.collections]
            
            if collection_name not in existing_collections:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._client.create_collection,
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=distance
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Qdrant connection."""
        try:
            if not self._client:
                return {
                    "status": "unhealthy",
                    "error": "Client not connected",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Test basic operations
            start_time = datetime.utcnow()
            collections = await asyncio.get_event_loop().run_in_executor(
                None, self._client.get_collections
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self._health_status = "healthy"
            self._last_health_check = datetime.utcnow()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "collections_count": len(collections.collections),
                "collections": [col.name for col in collections.collections],
                "timestamp": self._last_health_check.isoformat()
            }
            
        except Exception as e:
            self._health_status = "unhealthy"
            logger.error(f"Qdrant health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    @property
    def is_healthy(self) -> bool:
        """Check if Qdrant client is healthy."""
        return self._health_status == "healthy"
    
    # Collection operations
    
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE
    ) -> None:
        """Create a new collection."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        await asyncio.get_event_loop().run_in_executor(
            None,
            self._client.create_collection,
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance
            )
        )
    
    async def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        await asyncio.get_event_loop().run_in_executor(
            None, self._client.delete_collection, collection_name
        )
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        info = await asyncio.get_event_loop().run_in_executor(
            None, self._client.get_collection, collection_name
        )
        
        return {
            "name": info.config.name,
            "vector_size": info.config.params.vectors.size,
            "distance": info.config.params.vectors.distance,
            "points_count": info.points_count,
            "segments_count": info.segments_count,
            "status": info.status
        }
    
    # Point operations
    
    async def upsert_points(
        self,
        collection_name: str,
        points: List[PointStruct]
    ) -> None:
        """Upsert points to collection."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        await asyncio.get_event_loop().run_in_executor(
            None, self._client.upsert, collection_name, points
        )
    
    async def delete_points(
        self,
        collection_name: str,
        points_selector: Union[List[str], Filter]
    ) -> None:
        """Delete points from collection."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        await asyncio.get_event_loop().run_in_executor(
            None, self._client.delete, collection_name, points_selector
        )
    
    async def retrieve_points(
        self,
        collection_name: str,
        ids: List[str],
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[Dict[str, Any]]:
        """Retrieve points by IDs."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        points = await asyncio.get_event_loop().run_in_executor(
            None,
            self._client.retrieve,
            collection_name,
            ids,
            with_payload=with_payload,
            with_vectors=with_vectors
        )
        
        return [
            {
                "id": point.id,
                "payload": point.payload,
                "vector": point.vector
            }
            for point in points
        ]
    
    # Search operations
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_filter: Optional[Filter] = None,
        limit: int = 10,
        offset: int = 0,
        with_payload: bool = True,
        with_vectors: bool = False,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        search_request = SearchRequest(
            vector=query_vector,
            filter=query_filter,
            limit=limit,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
            score_threshold=score_threshold
        )
        
        results = await asyncio.get_event_loop().run_in_executor(
            None, self._client.search, collection_name, search_request
        )
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
                "vector": result.vector
            }
            for result in results
        ]
    
    async def scroll(
        self,
        collection_name: str,
        scroll_filter: Optional[Filter] = None,
        limit: int = 10,
        offset: Optional[str] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Scroll through collection points."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        scroll_request = ScrollRequest(
            filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors
        )
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._client.scroll, collection_name, scroll_request
        )
        
        points = [
            {
                "id": point.id,
                "payload": point.payload,
                "vector": point.vector
            }
            for point in result[0]
        ]
        
        return points, result[1]
    
    async def count_points(
        self,
        collection_name: str,
        count_filter: Optional[Filter] = None
    ) -> int:
        """Count points in collection."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        count_request = CountRequest(filter=count_filter)
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._client.count, collection_name, count_request
        )
        
        return result.count
    
    # Semantic search operations
    
    async def semantic_search(
        self,
        collection_name: str,
        query_vector: List[float],
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search with access control filters."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        # Build access control filter
        filter_conditions = []
        
        if agent_id:
            filter_conditions.append(
                FieldCondition(
                    key="agent_id",
                    match=MatchValue(value=agent_id)
                )
            )
        
        if team_id:
            filter_conditions.append(
                FieldCondition(
                    key="team_id",
                    match=MatchValue(value=team_id)
                )
            )
        
        if user_id:
            filter_conditions.append(
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            )
        
        query_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        return await self.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        )
    
    async def hybrid_search(
        self,
        collection_name: str,
        dense_vector: List[float],
        sparse_vector: Optional[Dict[str, float]] = None,
        alpha: float = 0.7,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform hybrid dense/sparse search."""
        if not self._client:
            raise RuntimeError("Qdrant client not connected")
        
        # For now, we'll use dense search only
        # TODO: Implement proper hybrid search when Qdrant supports it
        return await self.semantic_search(
            collection_name=collection_name,
            query_vector=dense_vector,
            agent_id=agent_id,
            limit=limit
        )
    
    # Memory-specific operations
    
    async def store_knowledge_embedding(
        self,
        knowledge_id: str,
        embedding: List[float],
        payload: Dict[str, Any]
    ) -> None:
        """Store knowledge embedding."""
        point = PointStruct(
            id=knowledge_id,
            vector=embedding,
            payload=payload
        )
        
        await self.upsert_points("semantic_memory", [point])
    
    async def store_episode_embedding(
        self,
        episode_id: str,
        embedding: List[float],
        payload: Dict[str, Any]
    ) -> None:
        """Store episode embedding."""
        point = PointStruct(
            id=episode_id,
            vector=embedding,
            payload=payload
        )
        
        await self.upsert_points("episodes", [point])
    
    async def search_similar_knowledge(
        self,
        query_embedding: List[float],
        agent_id: str,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar knowledge."""
        return await self.semantic_search(
            collection_name="semantic_memory",
            query_vector=query_embedding,
            agent_id=agent_id,
            limit=limit,
            score_threshold=score_threshold
        )
    
    async def search_similar_episodes(
        self,
        query_embedding: List[float],
        agent_id: str,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar episodes."""
        return await self.semantic_search(
            collection_name="episodes",
            query_vector=query_embedding,
            agent_id=agent_id,
            limit=limit,
            score_threshold=score_threshold
        )


# Global Qdrant client instance
_qdrant_client: Optional[QdrantClient] = None


async def get_qdrant_client() -> QdrantClient:
    """Get or create global Qdrant client instance."""
    global _qdrant_client
    
    if _qdrant_client is None:
        settings = get_settings()
        _qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=settings.qdrant_timeout
        )
        await _qdrant_client.connect()
    
    return _qdrant_client


async def close_qdrant_client():
    """Close global Qdrant client."""
    global _qdrant_client
    
    if _qdrant_client:
        await _qdrant_client.disconnect()
        _qdrant_client = None
