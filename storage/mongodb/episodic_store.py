"""MongoDB-based episodic memory implementation."""

from typing import List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

from models.memory.episodic import Episode, EPISODIC_MEMORY_INDEXES
from config.settings import get_settings


class EpisodicMemoryStore:
    """Episodic memory storage using MongoDB."""
    
    def __init__(self, mongo_client: AsyncIOMotorClient, db_name: Optional[str] = None):
        """
        Initialize episodic memory store.
        
        Args:
            mongo_client: Motor async MongoDB client
            db_name: Database name (uses settings if None)
        """
        settings = get_settings()
        self.db: AsyncIOMotorDatabase = mongo_client[db_name or settings.mongodb_database]
        self.collection = self.db.episodes
        self.settings = settings
    
    async def initialize(self):
        """Create indexes for the collection."""
        # Create standard indexes
        for index_spec in EPISODIC_MEMORY_INDEXES:
            if len(index_spec) == 1:
                await self.collection.create_index(index_spec[0])
            else:
                await self.collection.create_index(index_spec[0], **index_spec[1] if len(index_spec) > 1 else {})
        
        # Create TTL index
        ttl_seconds = self.settings.episodic_memory_ttl_days * 24 * 3600
        await self.collection.create_index(
            "created_at",
            expireAfterSeconds=ttl_seconds
        )
    
    async def save_episode(self, episode: Episode) -> str:
        """
        Save an episode to the database.
        
        Args:
            episode: Episode to save
            
        Returns:
            Episode ID
        """
        # Calculate importance if not set
        if episode.importance == 0.5:  # Default value
            episode.importance = self._calculate_importance(episode)
        
        episode_dict = episode.model_dump(by_alias=True, exclude_none=True)
        
        # Remove _id if None
        if episode_dict.get("_id") is None:
            episode_dict.pop("_id", None)
        
        result = await self.collection.insert_one(episode_dict)
        return str(result.inserted_id)
    
    async def get_episode(self, episode_id: str) -> Optional[Episode]:
        """
        Get an episode by ID.
        
        Args:
            episode_id: Episode identifier
            
        Returns:
            Episode or None if not found
        """
        doc = await self.collection.find_one({"_id": ObjectId(episode_id)})
        return Episode(**doc) if doc else None
    
    async def search_similar_episodes(
        self,
        agent_id: str,
        query_embedding: List[float],
        limit: int = 5,
        min_importance: float = 0.3,
        tags: Optional[List[str]] = None
    ) -> List[Episode]:
        """
        Search for similar episodes using vector search.
        
        Note: Requires MongoDB Atlas with Vector Search configured.
        
        Args:
            agent_id: Agent identifier
            query_embedding: Query vector
            limit: Maximum results
            min_importance: Minimum importance threshold
            tags: Optional tag filter
            
        Returns:
            List of similar episodes
        """
        # Build filter
        search_filter = {
            "agent_id": agent_id,
            "importance": {"$gte": min_importance}
        }
        
        if tags:
            search_filter["tags"] = {"$in": tags}
        
        try:
            # MongoDB Atlas Vector Search pipeline
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "episode_vector_index",
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": 100,
                        "limit": limit,
                        "filter": search_filter
                    }
                },
                {
                    "$project": {
                        "score": {"$meta": "vectorSearchScore"},
                        "agent_id": 1,
                        "session_id": 1,
                        "summary": 1,
                        "messages": 1,
                        "importance": 1,
                        "created_at": 1,
                        "tags": 1
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            episodes = await cursor.to_list(length=limit)
            
            return [Episode(**ep) for ep in episodes]
        
        except Exception as e:
            # Fallback to simple query if vector search not available
            print(f"Vector search failed: {e}. Using fallback query.")
            return await self.get_recent_episodes(agent_id, limit=limit, tags=tags)
    
    async def get_recent_episodes(
        self,
        agent_id: str,
        limit: int = 10,
        tags: Optional[List[str]] = None,
        min_importance: Optional[float] = None
    ) -> List[Episode]:
        """
        Get recent episodes for an agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum results
            tags: Optional tag filter
            min_importance: Optional importance filter
            
        Returns:
            List of recent episodes
        """
        query = {"agent_id": agent_id}
        
        if tags:
            query["tags"] = {"$in": tags}
        
        if min_importance is not None:
            query["importance"] = {"$gte": min_importance}
        
        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        episodes = await cursor.to_list(length=limit)
        
        return [Episode(**ep) for ep in episodes]
    
    async def get_session_episodes(self, session_id: str) -> List[Episode]:
        """Get all episodes for a specific session."""
        cursor = self.collection.find({"session_id": session_id}).sort("created_at", 1)
        episodes = await cursor.to_list(length=None)
        return [Episode(**ep) for ep in episodes]
    
    async def update_episode_feedback(
        self,
        episode_id: str,
        feedback: dict,
        success: Optional[bool] = None
    ):
        """
        Update episode with user feedback.
        
        Args:
            episode_id: Episode identifier
            feedback: Feedback dictionary
            success: Whether episode was successful
        """
        update_doc = {
            "user_feedback": feedback,
            "updated_at": datetime.utcnow()
        }
        
        if success is not None:
            update_doc["success"] = success
            
            # Recalculate importance with feedback
            episode = await self.get_episode(episode_id)
            if episode:
                episode.user_feedback = feedback
                episode.success = success
                new_importance = self._calculate_importance(episode)
                update_doc["importance"] = new_importance
        
        await self.collection.update_one(
            {"_id": ObjectId(episode_id)},
            {"$set": update_doc}
        )
    
    async def apply_relevance_decay(self, decay_rate: float = 0.95):
        """
        Apply temporal decay to episode relevance.
        
        This should be run periodically (e.g., daily).
        
        Args:
            decay_rate: Decay factor (default 5% per day)
        """
        await self.collection.update_many(
            {"relevance_decay": {"$gt": 0.1}},
            [{
                "$set": {
                    "relevance_decay": {
                        "$multiply": ["$relevance_decay", decay_rate]
                    },
                    "updated_at": datetime.utcnow()
                }
            }]
        )
    
    async def cleanup_old_episodes(self, days: int = 90):
        """
        Manually cleanup episodes older than specified days.
        
        Note: TTL index should handle this automatically, but this
        can be used for manual cleanup or different policies.
        
        Args:
            days: Age threshold in days
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.collection.delete_many({
            "created_at": {"$lt": cutoff_date}
        })
        return result.deleted_count
    
    async def get_agent_statistics(self, agent_id: str) -> dict:
        """
        Get statistics for an agent's episodes.
        
        Returns:
            Dictionary with episode counts, average importance, etc.
        """
        pipeline = [
            {"$match": {"agent_id": agent_id}},
            {
                "$group": {
                    "_id": None,
                    "total_episodes": {"$sum": 1},
                    "avg_importance": {"$avg": "$importance"},
                    "with_feedback": {
                        "$sum": {
                            "$cond": [{"$ne": ["$user_feedback", None]}, 1, 0]
                        }
                    },
                    "successful": {
                        "$sum": {
                            "$cond": [{"$eq": ["$success", True]}, 1, 0]
                        }
                    }
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            stats = result[0]
            stats.pop("_id", None)
            return stats
        
        return {
            "total_episodes": 0,
            "avg_importance": 0,
            "with_feedback": 0,
            "successful": 0
        }
    
    def _calculate_importance(self, episode: Episode) -> float:
        """
        Calculate episode importance based on heuristics.
        
        Factors:
        - Length of conversation
        - User feedback
        - Success indicator
        
        Args:
            episode: Episode to evaluate
            
        Returns:
            Importance score (0-1)
        """
        # Length score (normalized by 20 messages)
        length_score = min(len(episode.messages) / 20, 1.0)
        
        # Feedback score
        feedback_score = 1.0 if episode.user_feedback else 0.5
        
        # Success score
        if episode.success is True:
            success_score = 1.0
        elif episode.success is False:
            success_score = 0.3
        else:
            success_score = 0.5
        
        # Weighted sum
        importance = (
            0.3 * length_score +
            0.3 * feedback_score +
            0.4 * success_score
        )
        
        return importance





