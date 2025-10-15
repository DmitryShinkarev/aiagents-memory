"""
Memory-Agents: Comprehensive Memory System for Multi-Agent Systems

A production-ready memory management system implementing four cognitive memory types:
- Working Memory (Redis)
- Episodic Memory (MongoDB)
- Semantic Memory (MongoDB + Qdrant)
- Procedural Memory (MongoDB)

Usage:
    from memory_agents import initialize_memory_system
    
    orchestrator = await initialize_memory_system(agent_id="my_agent")
    
    # Add messages to working memory
    await orchestrator.working.add_message(
        session_id="session_1",
        role="user",
        content="Hello!"
    )
    
    # Retrieve comprehensive context
    context = await orchestrator.retrieve_context(
        agent_id="my_agent",
        session_id="session_1",
        query="What did we discuss?"
    )
"""

__version__ = "0.1.0"
__author__ = "Memory-Agents Team"

from .core.memory_orchestrator import MemoryOrchestrator, MemoryPriority
from .utils.initialization import initialize_memory_system
from .config.settings import Settings, get_settings

# Models
from .models.memory.episodic import Episode, EpisodeMessage
from .models.memory.semantic import SemanticKnowledge, KnowledgeType
from .models.memory.procedural import Procedure, ProcedureType
from .models.logging.event_log import EventLog, EventType

# Storage
from .storage.redis.working_store import RedisWorkingMemory
from .storage.mongodb.episodic_store import EpisodicMemoryStore
from .storage.mongodb.semantic_store import SemanticMemoryStore
from .storage.mongodb.procedural_store import ProceduralMemoryStore
from .storage.postgresql.event_logger import EventLogger

__all__ = [
    # Core
    "MemoryOrchestrator",
    "MemoryPriority",
    "initialize_memory_system",
    
    # Config
    "Settings",
    "get_settings",
    
    # Models
    "Episode",
    "EpisodeMessage",
    "SemanticKnowledge",
    "KnowledgeType",
    "Procedure",
    "ProcedureType",
    "EventLog",
    "EventType",
    
    # Storage
    "RedisWorkingMemory",
    "EpisodicMemoryStore",
    "SemanticMemoryStore",
    "ProceduralMemoryStore",
    "EventLogger",
]


