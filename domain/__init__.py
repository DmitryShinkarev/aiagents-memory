"""
Domain Layer - Core Business Logic

This module contains the core domain logic for memory operations,
including working memory, episodic memory, semantic memory, and procedural memory.
"""

from domain.memory.working import WorkingMemoryService
from domain.memory.episodic import EpisodicMemoryService
from domain.memory.semantic import SemanticMemoryService
from domain.memory.procedural import ProceduralMemoryService
from domain.memory.facts import FactsService

# Alias for consistency with naming pattern
FactsMemoryService = FactsService

__all__ = [
    "WorkingMemoryService",
    "EpisodicMemoryService",
    "SemanticMemoryService",
    "ProceduralMemoryService",
    "FactsService",
    "FactsMemoryService",
]
