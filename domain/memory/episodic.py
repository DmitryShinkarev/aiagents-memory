"""
Episodic Memory Service - Long-term event memory.

This service manages episodic memory in MongoDB, including episodes,
trajectories, and consolidation operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from ...storage.clients.mongo_client import get_mongo_client
from ...storage.clients.qdrant_client import get_qdrant_client
from ...config.settings import get_settings
from ...api.contracts.episode import (
    EpisodeContext,
    EpisodeTrajectory,
    EpisodeScope,
    EpisodeType,
    EpisodeStatus
)

logger = logging.getLogger(__name__)


class EpisodicMemoryService:
    """Service for managing episodic memory in MongoDB."""
    
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
    
    # Episode creation and management
    
    async def create_episode(
        self,
        episode_id: str,
        context: EpisodeContext,
        scope: EpisodeScope,
        episode_type: EpisodeType,
        title: str,
        trajectory: List[EpisodeTrajectory],
        outcome: Optional[str] = None,
        status: EpisodeStatus = EpisodeStatus.COMPLETED,
        success: bool = True,
        importance: float = 0.5,
        user_satisfaction: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        retention_days: Optional[int] = None
    ) -> str:
        """
        Create a new episode.
        
        Args:
            episode_id: Unique episode identifier
            context: Episode context
            scope: Episode scope
            episode_type: Type of episode
            title: Episode title
            trajectory: Episode trajectory
            outcome: Episode outcome
            status: Episode status
            success: Whether episode was successful
            importance: Episode importance (0.0-1.0)
            user_satisfaction: User satisfaction rating (0.0-1.0)
            tags: Episode tags
            metadata: Additional metadata
            embedding: Episode embedding vector
            retention_days: Retention period in days
            
        Returns:
            Created episode ID
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Calculate expiration date
            if retention_days is None:
                retention_days = self._get_retention_days(scope)
            
            expires_at = datetime.utcnow() + timedelta(days=retention_days)
            
            # Create episode document
            episode_doc = {
                "episode_id": episode_id,
                "context": {
                    "user_id": context.user_id,
                    "agent_id": context.agent_id,
                    "team_id": context.team_id,
                    "session_id": context.session_id,
                    "parent_episode_id": context.parent_episode_id,
                    "participating_agents": context.participating_agents
                },
                "scope": scope.value,
                "episode_type": episode_type.value,
                "title": title,
                "trajectory": [
                    {
                        "step_id": step.step_id,
                        "timestamp": step.timestamp.isoformat() if isinstance(step.timestamp, datetime) else step.timestamp,
                        "role": step.role,
                        "action": step.action,
                        "content": step.content,
                        "metadata": step.metadata
                    }
                    for step in trajectory
                ],
                "outcome": outcome,
                "status": status.value,
                "success": success,
                "importance": importance,
                "user_satisfaction": user_satisfaction,
                "tags": tags or [],
                "metadata": metadata or {},
                "embedding": embedding,
                "created_at": datetime.utcnow(),
                "started_at": datetime.utcnow(),
                "completed_at": datetime.utcnow() if status == EpisodeStatus.COMPLETED else None,
                "expires_at": expires_at,
                "consolidated": False,
                "consolidated_at": None,
                "consolidated_knowledge_ids": []
            }
            
            # Insert into MongoDB
            inserted_id = await mongo_client.insert_one("episodes", episode_doc)
            
            # Store embedding in Qdrant if provided
            if embedding:
                await self._store_episode_embedding(episode_id, embedding, episode_doc)
            
            logger.info(f"Created episode {episode_id} with scope {scope.value}")
            return str(inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create episode {episode_id}: {e}")
            raise
    
    async def get_episode(
        self,
        episode_id: str,
        include_trajectory: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get episode by ID.
        
        Args:
            episode_id: Episode identifier
            include_trajectory: Whether to include trajectory data
            
        Returns:
            Episode data or None if not found
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            projection = None
            if not include_trajectory:
                projection = {"trajectory": 0}
            
            episode = await mongo_client.find_one(
                "episodes",
                {"episode_id": episode_id},
                projection
            )
            
            if episode:
                # Convert ObjectId to string
                episode["_id"] = str(episode["_id"])
                logger.debug(f"Retrieved episode {episode_id}")
            
            return episode
            
        except Exception as e:
            logger.error(f"Failed to get episode {episode_id}: {e}")
            return None
    
    async def update_episode(
        self,
        episode_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update episode.
        
        Args:
            episode_id: Episode identifier
            updates: Updates to apply
            
        Returns:
            True if successful
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Add update timestamp
            updates["updated_at"] = datetime.utcnow()
            
            result = await mongo_client.update_one(
                "episodes",
                {"episode_id": episode_id},
                {"$set": updates}
            )
            
            success = result["modified_count"] > 0
            
            if success:
                logger.debug(f"Updated episode {episode_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update episode {episode_id}: {e}")
            return False
    
    async def delete_episode(self, episode_id: str) -> bool:
        """
        Delete episode.
        
        Args:
            episode_id: Episode identifier
            
        Returns:
            True if successful
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Delete from MongoDB
            deleted_count = await mongo_client.delete_one(
                "episodes",
                {"episode_id": episode_id}
            )
            
            # Delete embedding from Qdrant
            await self._delete_episode_embedding(episode_id)
            
            success = deleted_count > 0
            
            if success:
                logger.info(f"Deleted episode {episode_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete episode {episode_id}: {e}")
            return False
    
    # Episode querying
    
    async def query_episodes(
        self,
        filter_by_user_id: Optional[str] = None,
        filter_by_agent_id: Optional[str] = None,
        filter_by_team_id: Optional[str] = None,
        filter_by_session_id: Optional[str] = None,
        filter_by_scope: Optional[List[EpisodeScope]] = None,
        filter_by_type: Optional[List[EpisodeType]] = None,
        filter_by_status: Optional[List[EpisodeStatus]] = None,
        filter_by_tags: Optional[List[str]] = None,
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None,
        min_importance: Optional[float] = None,
        only_successful: Optional[bool] = None,
        semantic_query: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query episodes with various filters.
        
        Args:
            filter_by_user_id: Filter by user ID
            filter_by_agent_id: Filter by agent ID
            filter_by_team_id: Filter by team ID
            filter_by_session_id: Filter by session ID
            filter_by_scope: Filter by scope
            filter_by_type: Filter by episode type
            filter_by_status: Filter by status
            filter_by_tags: Filter by tags
            time_range_start: Start of time range
            time_range_end: End of time range
            min_importance: Minimum importance threshold
            only_successful: Only successful episodes
            semantic_query: Semantic search query
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of episodes
        """
        try:
            # Build MongoDB filter
            mongo_filter = {}
            
            if filter_by_user_id:
                mongo_filter["context.user_id"] = filter_by_user_id
            
            if filter_by_agent_id:
                mongo_filter["context.agent_id"] = filter_by_agent_id
            
            if filter_by_team_id:
                mongo_filter["context.team_id"] = filter_by_team_id
            
            if filter_by_session_id:
                mongo_filter["context.session_id"] = filter_by_session_id
            
            if filter_by_scope:
                mongo_filter["scope"] = {"$in": [scope.value for scope in filter_by_scope]}
            
            if filter_by_type:
                mongo_filter["episode_type"] = {"$in": [ep_type.value for ep_type in filter_by_type]}
            
            if filter_by_status:
                mongo_filter["status"] = {"$in": [status.value for status in filter_by_status]}
            
            if filter_by_tags:
                mongo_filter["tags"] = {"$in": filter_by_tags}
            
            if time_range_start:
                mongo_filter["created_at"] = {"$gte": time_range_start}
            
            if time_range_end:
                if "created_at" in mongo_filter:
                    mongo_filter["created_at"]["$lte"] = time_range_end
                else:
                    mongo_filter["created_at"] = {"$lte": time_range_end}
            
            if min_importance is not None:
                mongo_filter["importance"] = {"$gte": min_importance}
            
            if only_successful is not None:
                mongo_filter["success"] = only_successful
            
            # Handle semantic search
            if semantic_query:
                # For now, we'll do a simple text search
                # TODO: Implement proper semantic search with embeddings
                mongo_filter["$or"] = [
                    {"title": {"$regex": semantic_query, "$options": "i"}},
                    {"outcome": {"$regex": semantic_query, "$options": "i"}}
                ]
            
            # Build sort criteria
            sort_criteria = []
            if sort_by == "created_at":
                sort_criteria.append(("created_at", DESCENDING if sort_order == "desc" else ASCENDING))
            elif sort_by == "importance":
                sort_criteria.append(("importance", DESCENDING if sort_order == "desc" else ASCENDING))
            else:
                sort_criteria.append((sort_by, DESCENDING if sort_order == "desc" else ASCENDING))
            
            mongo_client = await self._get_mongo_client()
            episodes = await mongo_client.find_many(
                "episodes",
                mongo_filter,
                sort=sort_criteria,
                skip=offset,
                limit=limit
            )
            
            # Convert ObjectIds to strings
            for episode in episodes:
                episode["_id"] = str(episode["_id"])
            
            logger.debug(f"Retrieved {len(episodes)} episodes")
            return episodes
            
        except Exception as e:
            logger.error(f"Failed to query episodes: {e}")
            return []
    
    async def search_similar_episodes(
        self,
        query_embedding: List[float],
        agent_id: str,
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar episodes using semantic search.
        
        Args:
            query_embedding: Query embedding vector
            agent_id: Agent ID for access control
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of similar episodes
        """
        try:
            qdrant_client = await self._get_qdrant_client()
            
            # Search in Qdrant
            results = await qdrant_client.search_similar_episodes(
                query_embedding=query_embedding,
                agent_id=agent_id,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Get full episode data from MongoDB
            episodes = []
            for result in results:
                episode_id = result["id"]
                episode = await self.get_episode(episode_id, include_trajectory=False)
                if episode:
                    episode["similarity_score"] = result["score"]
                    episodes.append(episode)
            
            logger.debug(f"Found {len(episodes)} similar episodes")
            return episodes
            
        except Exception as e:
            logger.error(f"Failed to search similar episodes: {e}")
            return []
    
    # Consolidation operations
    
    async def consolidate_episodes(
        self,
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None,
        min_importance: float = 0.5,
        target_agent_id: Optional[str] = None,
        target_team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consolidate episodes into knowledge.
        
        Args:
            time_range_start: Start of time range
            time_range_end: End of time range
            min_importance: Minimum importance for consolidation
            target_agent_id: Target agent for consolidation
            target_team_id: Target team for consolidation
            
        Returns:
            Consolidation results
        """
        try:
            # Get episodes for consolidation
            episodes = await self.query_episodes(
                filter_by_agent_id=target_agent_id,
                filter_by_team_id=target_team_id,
                time_range_start=time_range_start,
                time_range_end=time_range_end,
                min_importance=min_importance,
                limit=1000  # Large limit for consolidation
            )
            
            if not episodes:
                return {
                    "episodes_processed": 0,
                    "clusters_found": 0,
                    "knowledge_items_created": 0,
                    "consolidation_details": {}
                }
            
            # Consolidate episodes into knowledge
            from ..memory.semantic import SemanticMemoryService
            semantic_service = SemanticMemoryService()
            
            # Get episode IDs for consolidation
            episode_ids = [episode["episode_id"] for episode in episodes]
            
            # Perform knowledge consolidation
            created_knowledge_ids = await semantic_service.consolidate_knowledge_from_episodes(
                episode_ids=episode_ids,
                min_confidence=0.7
            )
            
            # Mark episodes as consolidated and link to created knowledge
            consolidated_count = 0
            for episode in episodes:
                if not episode.get("consolidated", False):
                    await self.update_episode(episode["episode_id"], {
                        "consolidated": True,
                        "consolidated_at": datetime.utcnow(),
                        "consolidated_knowledge_ids": created_knowledge_ids
                    })
                    consolidated_count += 1
            
            logger.info(f"Consolidated {consolidated_count} episodes into {len(created_knowledge_ids)} knowledge items")
            
            return {
                "episodes_processed": len(episodes),
                "clusters_found": len(created_knowledge_ids),  # Number of knowledge clusters created
                "knowledge_items_created": len(created_knowledge_ids),
                "consolidation_details": {
                    "consolidated_count": consolidated_count,
                    "created_knowledge_ids": created_knowledge_ids
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to consolidate episodes: {e}")
            return {
                "episodes_processed": 0,
                "clusters_found": 0,
                "knowledge_items_created": 0,
                "error": str(e)
            }
    
    # Helper methods
    
    def _get_retention_days(self, scope: EpisodeScope) -> int:
        """Get retention days for episode scope."""
        retention_map = {
            EpisodeScope.USER_PRIVATE: 90,
            EpisodeScope.AGENT_PRIVATE: 180,
            EpisodeScope.TEAM_SHARED: 365,
            EpisodeScope.CROSS_TEAM: 730,
            EpisodeScope.ORGANIZATION: 1825
        }
        return retention_map.get(scope, 90)
    
    async def _store_episode_embedding(
        self,
        episode_id: str,
        embedding: List[float],
        episode_doc: Dict[str, Any]
    ) -> None:
        """Store episode embedding in Qdrant."""
        try:
            qdrant_client = await self._get_qdrant_client()
            
            # Create payload for Qdrant
            payload = {
                "episode_id": episode_id,
                "agent_id": episode_doc["context"]["agent_id"],
                "team_id": episode_doc["context"].get("team_id"),
                "user_id": episode_doc["context"].get("user_id"),
                "episode_type": episode_doc["episode_type"],
                "scope": episode_doc["scope"],
                "importance": episode_doc["importance"],
                "created_at": episode_doc["created_at"].isoformat()
            }
            
            await qdrant_client.store_episode_embedding(
                episode_id=episode_id,
                embedding=embedding,
                payload=payload
            )
            
            logger.debug(f"Stored embedding for episode {episode_id}")
            
        except Exception as e:
            logger.warning(f"Failed to store episode embedding: {e}")
    
    async def _delete_episode_embedding(self, episode_id: str) -> None:
        """Delete episode embedding from Qdrant."""
        try:
            qdrant_client = await self._get_qdrant_client()
            await qdrant_client.delete_points("episodes", [episode_id])
            logger.debug(f"Deleted embedding for episode {episode_id}")
        except Exception as e:
            logger.warning(f"Failed to delete episode embedding: {e}")
    
    # Health and monitoring
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on episodic memory service."""
        try:
            mongo_client = await self._get_mongo_client()
            mongo_health = await mongo_client.health_check()
            
            qdrant_client = await self._get_qdrant_client()
            qdrant_health = await qdrant_client.health_check()
            
            return {
                "service": "episodic_memory",
                "status": "healthy" if mongo_health["status"] == "healthy" and qdrant_health["status"] == "healthy" else "unhealthy",
                "mongodb": mongo_health,
                "qdrant": qdrant_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Episodic memory health check failed: {e}")
            return {
                "service": "episodic_memory",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get episodic memory metrics."""
        try:
            mongo_client = await self._get_mongo_client()
            
            # Get episode counts by scope
            scope_counts = {}
            for scope in EpisodeScope:
                count = await mongo_client.count_documents(
                    "episodes",
                    {"scope": scope.value}
                )
                scope_counts[scope.value] = count
            
            # Get total episode count
            total_count = await mongo_client.count_documents("episodes", {})
            
            # Get consolidated count
            consolidated_count = await mongo_client.count_documents(
                "episodes",
                {"consolidated": True}
            )
            
            return {
                "total_episodes": total_count,
                "consolidated_episodes": consolidated_count,
                "episodes_by_scope": scope_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get episodic memory metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
