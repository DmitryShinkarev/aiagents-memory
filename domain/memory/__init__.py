"""
Memory services for different types of memory.

This module provides services for working memory, episodic memory,
semantic memory, procedural memory, and user facts.
"""

from domain.memory.facts import FactsService

# Alias for backward compatibility
FactsMemoryService = FactsService

__all__ = ['FactsMemoryService', 'FactsService']
