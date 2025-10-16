"""
API Layer - Stable Contracts for Memory System

This module provides stable, versioned API contracts that remain consistent
regardless of internal implementation changes.
"""

from .contracts.common import (
    APIVersion,
    OperationStatus,
    MemoryScope,
    EpisodeScope,
    EpisodeType,
    EpisodeStatus,
    SourceType,
    FieldType,
    UpdateOperation,
    SortOrder,
    IdempotencyGuard,
    BaseRequest,
    BaseResponse,
    PaginationRequest,
    PaginationResponse,
)

from .contracts.entity import (
    UniversalEntityWriteRequest,
    UniversalEntityUpdateRequest,
    UniversalEntityReadRequest,
    UniversalEntityQueryRequest,
    UniversalEntityResponse,
    EntityMetadata,
    EntityVersion,
)

from .contracts.episode import (
    UniversalEpisodeWriteRequest,
    UniversalEpisodeQueryRequest,
    UniversalEpisodeResponse,
    EpisodeContext,
    EpisodeTrajectory,
)

from .contracts.knowledge import (
    UniversalKnowledgeWriteRequest,
    UniversalKnowledgeQueryRequest,
    UniversalKnowledgeResponse,
    KnowledgeMetadata,
)

from .contracts.facts import (
    UniversalFactWriteRequest,
    UniversalFactQueryRequest,
    UniversalFactResponse,
    FactVersion,
)

from .versioning import APIVersionManager

__all__ = [
    # Common
    "APIVersion",
    "OperationStatus", 
    "MemoryScope",
    "EpisodeScope",
    "EpisodeType",
    "EpisodeStatus",
    "SourceType",
    "FieldType",
    "UpdateOperation",
    "SortOrder",
    "IdempotencyGuard",
    "BaseRequest",
    "BaseResponse",
    "PaginationRequest",
    "PaginationResponse",
    
    # Entity contracts
    "UniversalEntityWriteRequest",
    "UniversalEntityUpdateRequest", 
    "UniversalEntityReadRequest",
    "UniversalEntityQueryRequest",
    "UniversalEntityResponse",
    "EntityMetadata",
    "EntityVersion",
    
    # Episode contracts
    "UniversalEpisodeWriteRequest",
    "UniversalEpisodeQueryRequest",
    "UniversalEpisodeResponse",
    "EpisodeContext",
    "EpisodeTrajectory",
    
    # Knowledge contracts
    "UniversalKnowledgeWriteRequest",
    "UniversalKnowledgeQueryRequest",
    "UniversalKnowledgeResponse",
    "KnowledgeMetadata",
    
    # Facts contracts
    "UniversalFactWriteRequest",
    "UniversalFactQueryRequest",
    "UniversalFactResponse",
    "FactVersion",
    
    # Versioning
    "APIVersionManager",
]
