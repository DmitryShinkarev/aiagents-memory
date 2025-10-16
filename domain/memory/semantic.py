"""
Semantic Memory Service - Long-term knowledge memory.

This service manages semantic memory using MongoDB for storage and Qdrant
for high-performance vector search, including temporal decay and hybrid search.
"""

import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId

from ...storage.clients.mongo_client import get_mongo_client
from ...storage.clients.qdrant_client import get_qdrant_client
from ...config.settings import get_settings
from ...api.contracts.knowledge import SourceType

logger = logging.getLogger(__name__)


class SemanticMemoryService:
    """Service for managing semantic memory with hybrid search."""
    
    def __init__(self):
        self._mongo_client = None
        self._qdrant_client = None
        self._settings = get_settings()
    
    async def _get_mongo_client(self):
        """Get MongoDB client instance."""
        if self._mongo_client is None:
            self._mongo_client = await get_mongo_client()
        return self._mongo_client
    
    async def _get_qdrant_client(self):
        """Get Qdrant client instance."""
        if self._qdrant_client is None:
            self._qdrant_client = await get_qdrant_client()
        return self._qdrant_client
    
    # Knowledge creation and management
    
    async def create_knowledge(
        self,
        knowledge_id: str,
        knowledge: str,
        source: SourceType,
        confidence: float,
        agent_id: str,
        tags: Optional[List[str]] = None,
        supporting_evidence: Optional[List[str]] = None,
        temporal_scope: str = "always",
        half_life_days: Optional[int] = None,
        embedding: Optional[List[float]] = None,
        access_scope: str = "agent_private",
        allowed_teams: Optional[List[str]] = None,
        allowed_agents: Optional[List[str]] = None
    ) -> str:
        """
        Create new knowledge item.
        
        Args:
            knowledge_id: Unique knowledge identifier
            knowledge: Knowledge text
            source: Source of the knowledge
            confidence: Confidence level (0.0-1.0)
            agent_id: Agent that owns this knowledge
            tags: Knowledge tags
            supporting_evidence: Episode IDs that support this knowledge
            temporal_scope: Temporal scope (always, recent, deprecated)
            half_life_days: Half-life in days for temporal decay
            embedding: Knowledge embedding vector
            access_scope: Access scope
            allowed_teams: Teams with access
            allowed_agents: Agents with access
            
        Returns:
            Created knowledge ID
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Calculate expiration date based on temporal scope
            expires_at = self._calculate_expiration_date(temporal_scope, half_life_days)
            
            # Create knowledge document
            knowledge_doc = {
                "knowledge_id": knowledge_id,
                "knowledge": knowledge,
                "source": source.value,
                "confidence": confidence,
                "agent_id": agent_id,
                "tags": tags or [],
                "supporting_evidence": supporting_evidence or [],
                "temporal_scope": temporal_scope,
                "half_life_days": half_life_days,
                "access_scope": access_scope,
                "allowed_teams": allowed_teams or [],
                "allowed_agents": allowed_agents or [],
                "created_at": datetime.utcnow(),
                "last_accessed": datetime.utcnow(),
                "access_count": 0,
                "expires_at": expires_at
            }
            
            # Insert into MongoDB
            inserted_id = await mongo_client.insert_one("semantic_knowledge", knowledge_doc)
            
            # Store embedding in Qdrant if provided
            if embedding:
                await self._store_knowledge_embedding(knowledge_id, embedding, knowledge_doc)
            
            logger.info(f"Created knowledge {knowledge_id} with source {source.value}")
            return str(inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create knowledge {knowledge_id}: {e}")
            raise
    
    async def get_knowledge(
        self,
        knowledge_id: str,
        update_access: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get knowledge by ID.
        
        Args:
            knowledge_id: Knowledge identifier
            update_access: Whether to update access count and timestamp
            
        Returns:
            Knowledge data or None if not found
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            knowledge = await mongo_client.find_one(
                "semantic_knowledge",
                {"knowledge_id": knowledge_id}
            )
            
            if knowledge:
                # Convert ObjectId to string
                knowledge["_id"] = str(knowledge["_id"])
                
                # Update access information
                if update_access:
                    await mongo_client.update_one(
                        "semantic_knowledge",
                        {"knowledge_id": knowledge_id},
                        {
                            "$inc": {"access_count": 1},
                            "$set": {"last_accessed": datetime.utcnow()}
                        }
                    )
                
                logger.debug(f"Retrieved knowledge {knowledge_id}")
            
            return knowledge
            
        except Exception as e:
            logger.error(f"Failed to get knowledge {knowledge_id}: {e}")
            return None
    
    async def update_knowledge(
        self,
        knowledge_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update knowledge.
        
        Args:
            knowledge_id: Knowledge identifier
            updates: Updates to apply
            
        Returns:
            True if successful
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Add update timestamp
            updates["updated_at"] = datetime.utcnow()
            
            result = await mongo_client.update_one(
                "semantic_knowledge",
                {"knowledge_id": knowledge_id},
                {"$set": updates}
            )
            
            success = result["modified_count"] > 0
            
            if success:
                logger.debug(f"Updated knowledge {knowledge_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update knowledge {knowledge_id}: {e}")
            return False
    
    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        Delete knowledge.
        
        Args:
            knowledge_id: Knowledge identifier
            
        Returns:
            True if successful
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Delete from MongoDB
            deleted_count = await mongo_client.delete_one(
                "semantic_knowledge",
                {"knowledge_id": knowledge_id}
            )
            
            # Delete embedding from Qdrant
            await self._delete_knowledge_embedding(knowledge_id)
            
            success = deleted_count > 0
            
            if success:
                logger.info(f"Deleted knowledge {knowledge_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge {knowledge_id}: {e}")
            return False
    
    # Knowledge querying and search
    
    async def query_knowledge(
        self,
        filter_by_agent_id: Optional[str] = None,
        filter_by_team_id: Optional[str] = None,
        filter_by_source: Optional[List[SourceType]] = None,
        filter_by_tags: Optional[List[str]] = None,
        filter_by_temporal_scope: Optional[List[str]] = None,
        min_confidence: Optional[float] = None,
        min_access_count: Optional[int] = None,
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query knowledge with various filters.
        
        Args:
            filter_by_agent_id: Filter by agent ID
            filter_by_team_id: Filter by team ID
            filter_by_source: Filter by source types
            filter_by_tags: Filter by tags
            filter_by_temporal_scope: Filter by temporal scope
            min_confidence: Minimum confidence threshold
            min_access_count: Minimum access count
            time_range_start: Start of time range
            time_range_end: End of time range
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of knowledge items
        """
        try:
            # Build MongoDB filter
            mongo_filter = {}
            
            if filter_by_agent_id:
                mongo_filter["agent_id"] = filter_by_agent_id
            
            if filter_by_team_id:
                mongo_filter["$or"] = [
                    {"allowed_teams": filter_by_team_id},
                    {"access_scope": "public"},
                    {"access_scope": "organization"}
                ]
            
            if filter_by_source:
                mongo_filter["source"] = {"$in": [source.value for source in filter_by_source]}
            
            if filter_by_tags:
                mongo_filter["tags"] = {"$in": filter_by_tags}
            
            if filter_by_temporal_scope:
                mongo_filter["temporal_scope"] = {"$in": filter_by_temporal_scope}
            
            if min_confidence is not None:
                mongo_filter["confidence"] = {"$gte": min_confidence}
            
            if min_access_count is not None:
                mongo_filter["access_count"] = {"$gte": min_access_count}
            
            if time_range_start:
                mongo_filter["created_at"] = {"$gte": time_range_start}
            
            if time_range_end:
                if "created_at" in mongo_filter:
                    mongo_filter["created_at"]["$lte"] = time_range_end
                else:
                    mongo_filter["created_at"] = {"$lte": time_range_end}
            
            # Build sort criteria
            from pymongo import ASCENDING, DESCENDING
            sort_criteria = []
            if sort_by == "created_at":
                sort_criteria.append(("created_at", DESCENDING if sort_order == "desc" else ASCENDING))
            elif sort_by == "confidence":
                sort_criteria.append(("confidence", DESCENDING if sort_order == "desc" else ASCENDING))
            elif sort_by == "access_count":
                sort_criteria.append(("access_count", DESCENDING if sort_order == "desc" else ASCENDING))
            else:
                sort_criteria.append((sort_by, DESCENDING if sort_order == "desc" else ASCENDING))
            
            mongo_client = await self._get_mongo_client()
            knowledge_items = await mongo_client.find_many(
                "semantic_knowledge",
                mongo_filter,
                sort=sort_criteria,
                skip=offset,
                limit=limit
            )
            
            # Convert ObjectIds to strings
            for item in knowledge_items:
                item["_id"] = str(item["_id"])
            
            logger.debug(f"Retrieved {len(knowledge_items)} knowledge items")
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Failed to query knowledge: {e}")
            return []
    
    async def semantic_search(
        self,
        query_embedding: List[float],
        agent_id: str,
        team_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        include_temporal_decay: bool = True,
        alpha: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search with temporal decay.
        
        Args:
            query_embedding: Query embedding vector
            agent_id: Agent ID for access control
            team_id: Team ID for access control
            user_id: User ID for access control
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            include_temporal_decay: Whether to include temporal decay
            alpha: Balance between dense and sparse search
            
        Returns:
            List of knowledge items with scores
        """
        try:
            qdrant_client = await self._get_qdrant_client()
            
            # Search in Qdrant
            results = await qdrant_client.semantic_search(
                collection_name="semantic_memory",
                query_vector=query_embedding,
                agent_id=agent_id,
                team_id=team_id,
                user_id=user_id,
                limit=limit * 2,  # Get more results for temporal decay filtering
                score_threshold=score_threshold
            )
            
            # Get full knowledge data from MongoDB
            knowledge_items = []
            for result in results:
                knowledge_id = result["id"]
                knowledge = await self.get_knowledge(knowledge_id, update_access=False)
                
                if knowledge:
                    # Calculate combined score with temporal decay
                    semantic_score = result["score"]
                    
                    if include_temporal_decay:
                        temporal_score = self._calculate_temporal_score(knowledge)
                        combined_score = semantic_score * 0.6 + temporal_score * 0.4
                    else:
                        combined_score = semantic_score
                    
                    knowledge["similarity_score"] = semantic_score
                    knowledge["temporal_score"] = temporal_score if include_temporal_decay else 1.0
                    knowledge["combined_score"] = combined_score
                    
                    knowledge_items.append(knowledge)
            
            # Sort by combined score and limit results
            knowledge_items.sort(key=lambda x: x["combined_score"], reverse=True)
            knowledge_items = knowledge_items[:limit]
            
            logger.debug(f"Found {len(knowledge_items)} knowledge items via semantic search")
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return []
    
    async def hybrid_search(
        self,
        dense_vector: List[float],
        sparse_vector: Optional[Dict[str, float]] = None,
        agent_id: str,
        alpha: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid dense/sparse search.
        
        Args:
            dense_vector: Dense embedding vector
            sparse_vector: Sparse vector (BM25-like)
            agent_id: Agent ID for access control
            alpha: Balance between dense and sparse search
            limit: Maximum number of results
            
        Returns:
            List of knowledge items
        """
        try:
            qdrant_client = await self._get_qdrant_client()
            
            # Perform hybrid search in Qdrant
            results = await qdrant_client.hybrid_search(
                collection_name="semantic_memory",
                dense_vector=dense_vector,
                sparse_vector=sparse_vector,
                alpha=alpha,
                agent_id=agent_id,
                limit=limit
            )
            
            # Get full knowledge data from MongoDB
            knowledge_items = []
            for result in results:
                knowledge_id = result["id"]
                knowledge = await self.get_knowledge(knowledge_id, update_access=False)
                
                if knowledge:
                    knowledge["similarity_score"] = result["score"]
                    knowledge_items.append(knowledge)
            
            logger.debug(f"Found {len(knowledge_items)} knowledge items via hybrid search")
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {e}")
            return []
    
    # Knowledge consolidation
    
    async def consolidate_knowledge_from_episodes(
        self,
        episode_ids: List[str],
        min_confidence: float = 0.7
    ) -> List[str]:
        """
        Consolidate knowledge from episodes.
        
        Args:
            episode_ids: List of episode IDs to consolidate
            min_confidence: Minimum confidence for created knowledge
            
        Returns:
            List of created knowledge IDs
        """
        try:
            # TODO: Implement LLM-based knowledge extraction
            # For now, return empty list
            logger.info(f"Consolidating knowledge from {len(episode_ids)} episodes")
            return []
            
        except Exception as e:
            logger.error(f"Failed to consolidate knowledge from episodes: {e}")
            return []
    
    # Helper methods
    
    def _calculate_expiration_date(
        self,
        temporal_scope: str,
        half_life_days: Optional[int]
    ) -> Optional[datetime]:
        """Calculate expiration date based on temporal scope."""
        if temporal_scope == "always":
            return None  # Never expires
        elif temporal_scope == "recent":
            return datetime.utcnow() + timedelta(days=30)
        elif temporal_scope == "deprecated":
            return datetime.utcnow() + timedelta(days=7)
        else:
            # Use half_life_days if provided
            if half_life_days:
                return datetime.utcnow() + timedelta(days=half_life_days * 2)
            return datetime.utcnow() + timedelta(days=365)  # Default 1 year
    
    def _calculate_temporal_score(self, knowledge: Dict[str, Any]) -> float:
        """Calculate temporal decay score for knowledge."""
        try:
            created_at = knowledge.get("created_at")
            if not created_at:
                return 1.0
            
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            half_life_days = knowledge.get("half_life_days", 365)  # Default 1 year
            age_days = (datetime.utcnow() - created_at).days
            
            # Calculate temporal score using exponential decay
            temporal_score = math.pow(2, -age_days / half_life_days)
            
            return min(1.0, max(0.0, temporal_score))
            
        except Exception as e:
            logger.warning(f"Failed to calculate temporal score: {e}")
            return 1.0
    
    async def _store_knowledge_embedding(
        self,
        knowledge_id: str,
        embedding: List[float],
        knowledge_doc: Dict[str, Any]
    ) -> None:
        """Store knowledge embedding in Qdrant."""
        try:
            qdrant_client = await self._get_qdrant_client()
            
            # Create payload for Qdrant
            payload = {
                "knowledge_id": knowledge_id,
                "agent_id": knowledge_doc["agent_id"],
                "team_id": knowledge_doc.get("team_id"),
                "user_id": knowledge_doc.get("user_id"),
                "source": knowledge_doc["source"],
                "confidence": knowledge_doc["confidence"],
                "temporal_scope": knowledge_doc["temporal_scope"],
                "half_life_days": knowledge_doc.get("half_life_days"),
                "created_at": knowledge_doc["created_at"].isoformat()
            }
            
            await qdrant_client.store_knowledge_embedding(
                knowledge_id=knowledge_id,
                embedding=embedding,
                payload=payload
            )
            
            logger.debug(f"Stored embedding for knowledge {knowledge_id}")
            
        except Exception as e:
            logger.warning(f"Failed to store knowledge embedding: {e}")
    
    async def _delete_knowledge_embedding(self, knowledge_id: str) -> None:
        """Delete knowledge embedding from Qdrant."""
        try:
            qdrant_client = await self._get_qdrant_client()
            await qdrant_client.delete_points("semantic_memory", [knowledge_id])
            logger.debug(f"Deleted embedding for knowledge {knowledge_id}")
        except Exception as e:
            logger.warning(f"Failed to delete knowledge embedding: {e}")
    
    # Health and monitoring
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on semantic memory service."""
        try:
            mongo_client = await self._get_mongo_client()
            mongo_health = await mongo_client.health_check()
            
            qdrant_client = await self._get_qdrant_client()
            qdrant_health = await qdrant_client.health_check()
            
            return {
                "service": "semantic_memory",
                "status": "healthy" if mongo_health["status"] == "healthy" and qdrant_health["status"] == "healthy" else "unhealthy",
                "mongodb": mongo_health,
                "qdrant": qdrant_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Semantic memory health check failed: {e}")
            return {
                "service": "semantic_memory",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get semantic memory metrics."""
        try:
            mongo_client = await self._get_mongo_client()
            
            # Get knowledge counts by source
            source_counts = {}
            for source in SourceType:
                count = await mongo_client.count_documents(
                    "semantic_knowledge",
                    {"source": source.value}
                )
                source_counts[source.value] = count
            
            # Get total knowledge count
            total_count = await mongo_client.count_documents("semantic_knowledge", {})
            
            # Get high-confidence knowledge count
            high_confidence_count = await mongo_client.count_documents(
                "semantic_knowledge",
                {"confidence": {"$gte": 0.8}}
            )
            
            # Get temporal scope counts
            temporal_counts = {}
            for scope in ["always", "recent", "deprecated"]:
                count = await mongo_client.count_documents(
                    "semantic_knowledge",
                    {"temporal_scope": scope}
                )
                temporal_counts[scope] = count
            
            return {
                "total_knowledge": total_count,
                "high_confidence_knowledge": high_confidence_count,
                "knowledge_by_source": source_counts,
                "knowledge_by_temporal_scope": temporal_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get semantic memory metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
