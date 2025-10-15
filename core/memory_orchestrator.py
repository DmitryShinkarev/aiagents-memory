"""Memory Orchestrator - central coordination of all memory types."""

import asyncio
from typing import List, Dict, Optional, Union, Any
from enum import Enum
from datetime import datetime

from storage.redis.working_store import RedisWorkingMemory
from storage.mongodb.episodic_store import EpisodicMemoryStore
from storage.mongodb.semantic_store import SemanticMemoryStore
from storage.mongodb.procedural_store import ProceduralMemoryStore
from storage.postgresql.event_logger import EventLogger
from models.memory.episodic import Episode, EpisodeMessage
from models.memory.semantic import SemanticKnowledge
from models.logging.event_log import EventLog, EventType


class MemoryPriority(str, Enum):
    """Priority modes for memory retrieval."""
    
    WORKING_FIRST = "working_first"
    EPISODIC_FIRST = "episodic_first"
    SEMANTIC_FIRST = "semantic_first"
    PROCEDURAL_FIRST = "procedural_first"
    BALANCED = "balanced"


class MemoryOrchestrator:
    """
    Central coordinator for all memory types.
    
    Handles:
    - Context retrieval across memory types
    - Session consolidation
    - Priority-based memory access
    - Periodic maintenance
    """
    
    def __init__(
        self,
        working_memory: RedisWorkingMemory,
        episodic_store: EpisodicMemoryStore,
        semantic_store: SemanticMemoryStore,
        procedural_store: ProceduralMemoryStore,
        event_logger: Optional[EventLogger] = None,
        embedding_service = None
    ):
        """
        Initialize memory orchestrator.
        
        Args:
            working_memory: Redis working memory
            episodic_store: MongoDB episodic memory
            semantic_store: MongoDB+Qdrant semantic memory
            procedural_store: MongoDB procedural memory
            event_logger: Optional PostgreSQL event logger
            embedding_service: Service for creating embeddings
        """
        self.working = working_memory
        self.episodic = episodic_store
        self.semantic = semantic_store
        self.procedural = procedural_store
        self.logger = event_logger
        self.embedder = embedding_service
    
    async def retrieve_context(
        self,
        agent_id: str,
        session_id: str,
        query: str,
        priority: MemoryPriority = MemoryPriority.BALANCED,
        max_tokens: int = 4096,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Retrieve comprehensive context from all memory types.
        
        Args:
            agent_id: Agent identifier
            session_id: Session identifier
            query: Current query/task
            priority: Memory priority mode
            max_tokens: Maximum context tokens
            namespace: Namespace for semantic/procedural memory
            
        Returns:
            Dictionary with context from each memory type
        """
        start_time = datetime.utcnow()
        
        try:
            # 1. Get working memory context
            working_context = await self.working.get_context(session_id)
            
            # 2. Create query embedding if embedder available
            query_embedding = None
            if self.embedder:
                query_embedding = await self.embedder.embed(query)
            
            # 3. Parallel search in long-term memory types
            tasks = []
            
            # Episodic memory
            if query_embedding:
                tasks.append(
                    self.episodic.search_similar_episodes(
                        agent_id, query_embedding, limit=3
                    )
                )
            else:
                tasks.append(
                    self.episodic.get_recent_episodes(agent_id, limit=3)
                )
            
            # Semantic memory
            if query_embedding:
                tasks.append(
                    self.semantic.semantic_search(
                        query_embedding, namespace=namespace, limit=5
                    )
                )
            else:
                tasks.append(
                    self.semantic.text_search(query, namespace=namespace, limit=5)
                )
            
            # Procedural memory
            tasks.append(
                self.procedural.search_procedures(
                    tags=self._extract_tags(query),
                    namespace=namespace,
                    limit=3
                )
            )
            
            # Execute parallel searches
            episodic_results, semantic_results, procedural_results = \
                await asyncio.gather(*tasks)
            
            # 4. Apply prioritization and token limit
            context = self._prioritize_and_limit(
                working=working_context,
                episodic=episodic_results,
                semantic=semantic_results,
                procedural=procedural_results,
                priority=priority,
                max_tokens=max_tokens
            )
            
            # 5. Log the retrieval
            if self.logger:
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                await self.logger.log_event(EventLog(
                    event_type=EventType.MEMORY_READ,
                    agent_id=agent_id,
                    session_id=session_id,
                    action="retrieve_context",
                    resource="orchestrator",
                    details={
                        "priority": priority.value,
                        "max_tokens": max_tokens,
                        "working_count": len(working_context),
                        "episodic_count": len(episodic_results),
                        "semantic_count": len(semantic_results),
                        "procedural_count": len(procedural_results)
                    },
                    latency_ms=latency_ms,
                    status="success"
                ))
            
            return context
        
        except Exception as e:
            if self.logger:
                await self.logger.log_event(EventLog(
                    event_type=EventType.ERROR,
                    agent_id=agent_id,
                    session_id=session_id,
                    action="retrieve_context",
                    resource="orchestrator",
                    details={"error": str(e)},
                    status="error",
                    error_message=str(e)
                ))
            raise
    
    async def consolidate_session(
        self,
        agent_id: str,
        session_id: str
    ):
        """
        Consolidate session from working memory to long-term memory.
        
        Implements Pattern 4.9 Self-reflection:
        - Summarizes session via LLM
        - Extracts key facts
        - Saves to episodic memory
        - Clears working memory
        
        Args:
            agent_id: Agent identifier
            session_id: Session identifier
        """
        start_time = datetime.utcnow()
        
        try:
            # 1. Get all messages from working memory
            messages = await self.working.get_context(session_id)
            
            if not messages:
                return
            
            # 2. Create summary (placeholder - would use LLM)
            summary = await self._create_summary(messages)
            
            # 3. Assess importance and extract tags
            importance = await self._assess_importance(messages, summary)
            tags = await self._extract_semantic_tags(summary)
            
            # 4. Create episode
            episode = Episode(
                agent_id=agent_id,
                session_id=session_id,
                messages=[EpisodeMessage(**msg) for msg in messages],
                summary=summary,
                importance=importance,
                tags=tags
            )
            
            # 5. Create embedding and save episode
            if self.embedder:
                episode_embedding = await self.embedder.embed(summary)
                episode.embedding = episode_embedding
            
            episode_id = await self.episodic.save_episode(episode)
            
            # 6. Extract and save facts to semantic memory
            facts = await self._extract_facts(messages)
            
            for fact in facts:
                if self.embedder:
                    fact_embedding = await self.embedder.embed(fact.content)
                    await self.semantic.add_knowledge(fact, fact_embedding)
            
            # 7. Clear working memory
            await self.working.clear_session(session_id)
            
            # 8. Log consolidation
            if self.logger:
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                await self.logger.log_event(EventLog(
                    event_type=EventType.MEMORY_WRITE,
                    agent_id=agent_id,
                    session_id=session_id,
                    action="consolidate_session",
                    resource="orchestrator",
                    details={
                        "episode_id": episode_id,
                        "message_count": len(messages),
                        "facts_extracted": len(facts),
                        "importance": importance
                    },
                    latency_ms=latency_ms,
                    status="success"
                ))
        
        except Exception as e:
            if self.logger:
                await self.logger.log_event(EventLog(
                    event_type=EventType.ERROR,
                    agent_id=agent_id,
                    session_id=session_id,
                    action="consolidate_session",
                    resource="orchestrator",
                    details={"error": str(e)},
                    status="error",
                    error_message=str(e)
                ))
            raise
    
    async def periodic_maintenance(self):
        """
        Perform periodic maintenance tasks.
        
        Should be run on a schedule (e.g., daily):
        - Apply relevance decay to episodes
        - Cleanup unused procedures
        - Archive old logs
        """
        try:
            tasks = [
                # Apply temporal decay to episodic memory
                self.episodic.apply_relevance_decay(),
                
                # Cleanup unused procedures
                self.procedural.cleanup_unused_procedures(days_unused=90),
            ]
            
            if self.logger:
                # Cleanup old events
                tasks.append(
                    self.logger.cleanup_old_events(days=90)
                )
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log maintenance results
            if self.logger:
                await self.logger.log_event(EventLog(
                    event_type=EventType.AGENT_ACTION,
                    agent_id="system",
                    action="periodic_maintenance",
                    resource="orchestrator",
                    details={
                        "results": [str(r) for r in results]
                    },
                    status="success"
                ))
        
        except Exception as e:
            if self.logger:
                await self.logger.log_event(EventLog(
                    event_type=EventType.ERROR,
                    agent_id="system",
                    action="periodic_maintenance",
                    resource="orchestrator",
                    details={"error": str(e)},
                    status="error",
                    error_message=str(e)
                ))
            raise
    
    def _prioritize_and_limit(
        self,
        working: List[Dict],
        episodic: List[Episode],
        semantic: List[SemanticKnowledge],
        procedural: List,
        priority: MemoryPriority,
        max_tokens: int
    ) -> Dict:
        """
        Prioritize and limit context based on token budget.
        
        Uses scoring formula:
        score = importance * decay * type_weight
        
        Args:
            working: Working memory messages
            episodic: Episodic memory results
            semantic: Semantic memory results
            procedural: Procedural memory results
            priority: Priority mode
            max_tokens: Token limit
            
        Returns:
            Prioritized and limited context
        """
        # Type weights based on priority
        weights = {
            MemoryPriority.WORKING_FIRST: {"working": 1.0, "episodic": 0.5, "semantic": 0.6, "procedural": 0.4},
            MemoryPriority.EPISODIC_FIRST: {"working": 1.0, "episodic": 0.9, "semantic": 0.6, "procedural": 0.5},
            MemoryPriority.SEMANTIC_FIRST: {"working": 1.0, "episodic": 0.6, "semantic": 0.9, "procedural": 0.7},
            MemoryPriority.PROCEDURAL_FIRST: {"working": 1.0, "episodic": 0.5, "semantic": 0.6, "procedural": 0.9},
            MemoryPriority.BALANCED: {"working": 1.0, "episodic": 0.7, "semantic": 0.7, "procedural": 0.6},
        }
        
        type_weights = weights[priority]
        
        # Score all items
        all_items = []
        
        # Working memory - always highest priority
        for item in working:
            all_items.append({
                "type": "working",
                "content": item,
                "score": 1.0,
                "tokens": self._estimate_tokens(item)
            })
        
        # Episodic memory
        for ep in episodic:
            score = ep.importance * ep.relevance_decay * type_weights["episodic"]
            all_items.append({
                "type": "episodic",
                "content": ep,
                "score": score,
                "tokens": self._estimate_tokens(ep.summary)
            })
        
        # Semantic memory
        for knowledge in semantic:
            score = knowledge.confidence * type_weights["semantic"]
            all_items.append({
                "type": "semantic",
                "content": knowledge,
                "score": score,
                "tokens": self._estimate_tokens(knowledge.content)
            })
        
        # Procedural memory
        for proc in procedural:
            score = proc.success_rate * type_weights["procedural"]
            all_items.append({
                "type": "procedural",
                "content": proc,
                "score": score,
                "tokens": self._estimate_tokens(proc.content)
            })
        
        # Sort by score
        all_items.sort(key=lambda x: x["score"], reverse=True)
        
        # Select items within token budget
        selected = {"working": [], "episodic": [], "semantic": [], "procedural": []}
        total_tokens = 0
        
        for item in all_items:
            if total_tokens + item["tokens"] > max_tokens:
                break
            
            selected[item["type"]].append(item["content"])
            total_tokens += item["tokens"]
        
        selected["total_tokens"] = total_tokens
        
        return selected
    
    def _estimate_tokens(self, content: Union[str, Dict]) -> int:
        """
        Estimate token count.
        
        Simple heuristic: ~4 characters per token.
        """
        if isinstance(content, str):
            return len(content) // 4
        elif isinstance(content, dict):
            return len(str(content)) // 4
        return 0
    
    async def _create_summary(self, messages: List[Dict]) -> str:
        """
        Create summary of messages.
        
        Placeholder - would use LLM in production.
        """
        # Simple summary for now
        if not messages:
            return "Empty session"
        
        return f"Session with {len(messages)} messages"
    
    async def _assess_importance(self, messages: List[Dict], summary: str) -> float:
        """
        Assess importance of a session.
        
        Could use LLM or heuristics.
        """
        # Simple heuristic based on length
        return min(len(messages) / 20, 1.0)
    
    async def _extract_semantic_tags(self, text: str) -> List[str]:
        """
        Extract semantic tags from text.
        
        Would use NER/keyword extraction in production.
        """
        # Placeholder
        return []
    
    async def _extract_facts(self, messages: List[Dict]) -> List[SemanticKnowledge]:
        """
        Extract facts from conversation.
        
        Would use information extraction in production.
        """
        # Placeholder
        return []
    
    def _extract_tags(self, query: str) -> List[str]:
        """
        Extract tags from query.
        
        Simple keyword extraction.
        """
        # Very basic - would use proper NLP
        words = query.lower().split()
        return [w for w in words if len(w) > 4][:5]


