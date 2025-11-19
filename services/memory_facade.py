"""
Memory Facade - Unified interface for all memory operations.

This module provides a unified facade that orchestrates operations across
all memory types (working, episodic, semantic, procedural, facts).
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from domain.memory.working import WorkingMemoryService
from domain.memory.episodic import EpisodicMemoryService
from domain.memory.semantic import SemanticMemoryService
from domain.memory.procedural import ProceduralMemoryService
from domain.memory.facts import FactsService

logger = logging.getLogger(__name__)


class MemoryFacade:
    """Unified facade for all memory operations."""
    
    def __init__(self):
        self.working = WorkingMemoryService()
        self.episodic = EpisodicMemoryService()
        self.semantic = SemanticMemoryService()
        self.procedural = ProceduralMemoryService()
        self.facts = FactsService()
    
    # Working Memory Operations
    
    async def get_context(
        self,
        agent_id: str,
        session_id: Optional[str] = None,
        include_history: bool = True,
        max_messages: int = 50
    ) -> Dict[str, Any]:
        """Get comprehensive context for an agent."""
        return await self.working.get_context(
            agent_id=agent_id,
            session_id=session_id,
            include_history=include_history,
            max_messages=max_messages
        )
    
    async def update_context(
        self,
        agent_id: str,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update context for an agent session."""
        return await self.working.update_context(
            agent_id=agent_id,
            session_id=session_id,
            updates=updates
        )
    
    async def cache_retrieval(
        self,
        query_hash: str,
        result: Any,
        ttl: int = 300
    ) -> bool:
        """Cache RAG retrieval result."""
        return await self.working.cache_retrieval(
            query_hash=query_hash,
            result=result,
            ttl=ttl
        )
    
    async def get_cached_retrieval(self, query_hash: str) -> Optional[Any]:
        """Get cached RAG retrieval result."""
        return await self.working.get_cached_retrieval(query_hash)
    
    # Episodic Memory Operations
    
    async def create_episode(
        self,
        episode_id: str,
        context: Dict[str, Any],
        scope: str,
        episode_type: str,
        title: str,
        trajectory: List[Dict[str, Any]],
        outcome: Optional[str] = None,
        status: str = "completed",
        success: bool = True,
        importance: float = 0.5,
        user_satisfaction: Optional[float] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> str:
        """Create a new episode."""
        from api.contracts.episode import EpisodeContext, EpisodeTrajectory, EpisodeScope, EpisodeType, EpisodeStatus
        
        # Convert context
        episode_context = EpisodeContext(
            user_id=context.get("user_id"),
            agent_id=context["agent_id"],
            team_id=context.get("team_id"),
            session_id=context.get("session_id"),
            parent_episode_id=context.get("parent_episode_id"),
            participating_agents=context.get("participating_agents", [])
        )
        
        # Convert trajectory
        episode_trajectory = [
            EpisodeTrajectory(
                step_id=step["step_id"],
                timestamp=step["timestamp"],
                role=step["role"],
                action=step["action"],
                content=step["content"],
                metadata=step.get("metadata")
            )
            for step in trajectory
        ]
        
        return await self.episodic.create_episode(
            episode_id=episode_id,
            context=episode_context,
            scope=EpisodeScope(scope),
            episode_type=EpisodeType(episode_type),
            title=title,
            trajectory=episode_trajectory,
            outcome=outcome,
            status=EpisodeStatus(status),
            success=success,
            importance=importance,
            user_satisfaction=user_satisfaction,
            tags=tags,
            metadata=metadata,
            embedding=embedding
        )
    
    async def get_episode(
        self,
        episode_id: str,
        include_trajectory: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get episode by ID."""
        return await self.episodic.get_episode(
            episode_id=episode_id,
            include_trajectory=include_trajectory
        )
    
    async def query_episodes(
        self,
        filter_by_user_id: Optional[str] = None,
        filter_by_agent_id: Optional[str] = None,
        filter_by_team_id: Optional[str] = None,
        filter_by_session_id: Optional[str] = None,
        filter_by_scope: Optional[List[str]] = None,
        filter_by_type: Optional[List[str]] = None,
        filter_by_status: Optional[List[str]] = None,
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
        """Query episodes with various filters."""
        from api.contracts.episode import EpisodeScope, EpisodeType, EpisodeStatus
        
        # Convert string enums to enum objects
        scope_enums = [EpisodeScope(s) for s in filter_by_scope] if filter_by_scope else None
        type_enums = [EpisodeType(t) for t in filter_by_type] if filter_by_type else None
        status_enums = [EpisodeStatus(s) for s in filter_by_status] if filter_by_status else None
        
        return await self.episodic.query_episodes(
            filter_by_user_id=filter_by_user_id,
            filter_by_agent_id=filter_by_agent_id,
            filter_by_team_id=filter_by_team_id,
            filter_by_session_id=filter_by_session_id,
            filter_by_scope=scope_enums,
            filter_by_type=type_enums,
            filter_by_status=status_enums,
            filter_by_tags=filter_by_tags,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            min_importance=min_importance,
            only_successful=only_successful,
            semantic_query=semantic_query,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
    
    # Semantic Memory Operations
    
    async def create_knowledge(
        self,
        knowledge_id: str,
        knowledge: str,
        source: str,
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
        """Create new knowledge item."""
        from api.contracts.knowledge import SourceType
        
        return await self.semantic.create_knowledge(
            knowledge_id=knowledge_id,
            knowledge=knowledge,
            source=SourceType(source),
            confidence=confidence,
            agent_id=agent_id,
            tags=tags,
            supporting_evidence=supporting_evidence,
            temporal_scope=temporal_scope,
            half_life_days=half_life_days,
            embedding=embedding,
            access_scope=access_scope,
            allowed_teams=allowed_teams,
            allowed_agents=allowed_agents
        )
    
    async def get_knowledge(
        self,
        knowledge_id: str,
        update_access: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get knowledge by ID."""
        return await self.semantic.get_knowledge(
            knowledge_id=knowledge_id,
            update_access=update_access
        )
    
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
        """Perform semantic search with temporal decay."""
        return await self.semantic.semantic_search(
            query_embedding=query_embedding,
            agent_id=agent_id,
            team_id=team_id,
            user_id=user_id,
            limit=limit,
            score_threshold=score_threshold,
            include_temporal_decay=include_temporal_decay,
            alpha=alpha
        )
    
    # Procedural Memory Operations
    
    async def store_procedure(
        self,
        procedure_id: str,
        name: str,
        description: str,
        code: str,
        language: str = "python",
        parameters_schema: Optional[Dict[str, Any]] = None,
        return_schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        created_by: str = "system"
    ) -> str:
        """Store a new procedure."""
        return await self.procedural.store_procedure(
            procedure_id=procedure_id,
            name=name,
            description=description,
            code=code,
            language=language,
            parameters_schema=parameters_schema,
            return_schema=return_schema,
            tags=tags,
            created_by=created_by
        )
    
    async def get_procedure(
        self,
        name: str,
        include_code: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get procedure by name."""
        return await self.procedural.get_procedure(
            name=name,
            include_code=include_code
        )
    
    async def execute_procedure(
        self,
        name: str,
        parameters: Optional[Dict[str, Any]] = None,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute procedure and update metrics."""
        return await self.procedural.execute_procedure(
            name=name,
            parameters=parameters,
            execution_context=execution_context
        )
    
    # Facts Operations
    
    async def store_fact(
        self,
        fact_id: str,
        user_id: str,
        fact_type: str,
        key: str,
        value: str,
        confidence: float,
        source: str,
        evidence: Optional[List[str]] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        force_update: bool = False
    ) -> str:
        """Store or update a user fact."""
        from api.contracts.facts import SourceType
        
        return await self.facts.store_fact(
            fact_id=fact_id,
            user_id=user_id,
            fact_type=fact_type,
            key=key,
            value=value,
            confidence=confidence,
            source=SourceType(source),
            evidence=evidence,
            valid_from=valid_from,
            valid_until=valid_until,
            force_update=force_update
        )
    
    async def get_fact(
        self,
        user_id: str,
        key: str,
        valid_at: Optional[datetime] = None,
        update_access: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get user fact by key."""
        return await self.facts.get_fact(
            user_id=user_id,
            key=key,
            valid_at=valid_at,
            update_access=update_access
        )
    
    async def get_user_profile(
        self,
        user_id: str,
        include_history: bool = False,
        valid_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive user profile."""
        return await self.facts.get_user_profile(
            user_id=user_id,
            include_history=include_history,
            valid_at=valid_at
        )
    
    # Comprehensive Memory Operations
    
    async def retrieve_comprehensive_context(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        query: Optional[str] = None,
        include_episodes: bool = True,
        include_knowledge: bool = True,
        include_facts: bool = True,
        max_episodes: int = 10,
        max_knowledge: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieve comprehensive context combining all memory types.
        
        Args:
            agent_id: Agent identifier
            user_id: Optional user identifier
            session_id: Optional session identifier
            query: Optional query for semantic search
            include_episodes: Whether to include relevant episodes
            include_knowledge: Whether to include relevant knowledge
            include_facts: Whether to include user facts
            max_episodes: Maximum number of episodes to include
            max_knowledge: Maximum number of knowledge items to include
            
        Returns:
            Comprehensive context dictionary
        """
        try:
            context = {
                "agent_id": agent_id,
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "working_memory": {},
                "episodes": [],
                "knowledge": [],
                "facts": {},
                "procedures": []
            }
            
            # Get working memory context
            context["working_memory"] = await self.get_context(
                agent_id=agent_id,
                session_id=session_id
            )
            
            # Get relevant episodes
            if include_episodes:
                episodes = await self.query_episodes(
                    filter_by_agent_id=agent_id,
                    filter_by_user_id=user_id,
                    filter_by_session_id=session_id,
                    limit=max_episodes
                )
                context["episodes"] = episodes
            
            # Get relevant knowledge (if query provided)
            if include_knowledge and query:
                # TODO: Generate embedding from query
                # For now, we'll do a simple text search
                knowledge_items = await self.semantic.query_knowledge(
                    filter_by_agent_id=agent_id,
                    limit=max_knowledge
                )
                context["knowledge"] = knowledge_items
            
            # Get user facts
            if include_facts and user_id:
                user_profile = await self.get_user_profile(user_id=user_id)
                context["facts"] = user_profile.get("facts", {})
            
            logger.debug(f"Retrieved comprehensive context for agent {agent_id}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to retrieve comprehensive context: {e}")
            return {
                "agent_id": agent_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Health and Monitoring
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all memory services."""
        try:
            # Check all services in parallel
            health_checks = await asyncio.gather(
                self.working.health_check(),
                self.episodic.health_check(),
                self.semantic.health_check(),
                self.procedural.health_check(),
                self.facts.health_check(),
                return_exceptions=True
            )
            
            working_health, episodic_health, semantic_health, procedural_health, facts_health = health_checks
            
            # Determine overall status
            all_healthy = all(
                health.get("status") == "healthy" if isinstance(health, dict) else False
                for health in health_checks
            )
            
            return {
                "service": "memory_facade",
                "status": "healthy" if all_healthy else "unhealthy",
                "services": {
                    "working_memory": working_health,
                    "episodic_memory": episodic_health,
                    "semantic_memory": semantic_health,
                    "procedural_memory": procedural_health,
                    "facts": facts_health
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Memory facade health check failed: {e}")
            return {
                "service": "memory_facade",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from all memory services."""
        try:
            # Get metrics from all services in parallel
            metrics = await asyncio.gather(
                self.working.get_metrics(),
                self.episodic.get_metrics(),
                self.semantic.get_metrics(),
                self.procedural.get_metrics(),
                self.facts.get_metrics(),
                return_exceptions=True
            )
            
            working_metrics, episodic_metrics, semantic_metrics, procedural_metrics, facts_metrics = metrics
            
            return {
                "working_memory": working_metrics,
                "episodic_memory": episodic_metrics,
                "semantic_memory": semantic_metrics,
                "procedural_memory": procedural_metrics,
                "facts": facts_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory facade metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global memory facade instance
_memory_facade: Optional[MemoryFacade] = None


def get_memory_facade() -> MemoryFacade:
    """Get or create global memory facade instance."""
    global _memory_facade
    
    if _memory_facade is None:
        _memory_facade = MemoryFacade()
    
    return _memory_facade
