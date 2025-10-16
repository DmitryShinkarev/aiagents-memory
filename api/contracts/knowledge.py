"""
Knowledge-related API contracts.

This module defines the stable contracts for semantic memory operations.
Knowledge represents generalized information extracted from episodes or provided directly.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .common import (
    BaseRequest,
    BaseResponse,
    PaginationRequest,
    PaginationResponse,
    SourceType,
    SortOrder,
)


class KnowledgeMetadata(BaseModel):
    """Metadata for knowledge items."""
    
    knowledge_id: str = Field(..., description="Unique knowledge identifier")
    agent_id: str = Field(..., description="Agent that owns this knowledge")
    source: SourceType = Field(..., description="Source of the knowledge")
    
    # Quality metrics
    confidence: float = Field(..., description="Confidence level (0.0-1.0)", ge=0.0, le=1.0)
    access_count: int = Field(..., description="Number of times accessed", ge=0)
    
    # Temporal information
    created_at: datetime = Field(..., description="Creation timestamp")
    last_accessed: datetime = Field(..., description="Last access timestamp")
    
    # Supporting evidence
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Episode IDs that support this knowledge"
    )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UniversalKnowledgeWriteRequest(BaseRequest):
    """Request to create or update knowledge."""
    
    # Knowledge content
    knowledge: str = Field(
        ...,
        description="Knowledge text",
        min_length=1,
        max_length=10000
    )
    
    # Source information
    source: SourceType = Field(
        ...,
        description="Source of the knowledge"
    )
    
    # Quality metrics
    confidence: float = Field(
        ...,
        description="Confidence level (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Knowledge tags",
        max_items=20
    )
    supporting_evidence: List[str] = Field(
        default_factory=list,
        description="Episode IDs that support this knowledge"
    )
    
    # Temporal scope
    temporal_scope: str = Field(
        default="always",
        description="Temporal scope (always, recent, deprecated)"
    )
    half_life_days: Optional[int] = Field(
        None,
        description="Half-life in days for temporal decay",
        ge=1
    )
    
    # Optional embedding
    embedding: Optional[List[float]] = Field(
        None,
        description="Knowledge embedding vector"
    )
    
    # Access control
    access_scope: str = Field(
        default="agent_private",
        description="Access scope for the knowledge"
    )
    allowed_teams: List[str] = Field(
        default_factory=list,
        description="Teams with access"
    )
    allowed_agents: List[str] = Field(
        default_factory=list,
        description="Agents with access"
    )
    
    class Config:
        use_enum_values = True
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError("Cannot have more than 20 tags")
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Tag length cannot exceed 50 characters")
        return v
    
    @validator('temporal_scope')
    def validate_temporal_scope(cls, v):
        allowed_scopes = ["always", "recent", "deprecated"]
        if v not in allowed_scopes:
            raise ValueError(f"temporal_scope must be one of {allowed_scopes}")
        return v


class UniversalKnowledgeQueryRequest(BaseRequest, PaginationRequest):
    """Request to query knowledge."""
    
    # Context filters
    filter_by_agent_id: Optional[str] = Field(
        None,
        description="Filter by agent ID"
    )
    filter_by_team_id: Optional[str] = Field(
        None,
        description="Filter by team ID"
    )
    
    # Property filters
    filter_by_source: Optional[List[SourceType]] = Field(
        None,
        description="Filter by source type"
    )
    filter_by_tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags"
    )
    filter_by_temporal_scope: Optional[List[str]] = Field(
        None,
        description="Filter by temporal scope"
    )
    
    # Quality filters
    min_confidence: Optional[float] = Field(
        None,
        description="Minimum confidence threshold",
        ge=0.0,
        le=1.0
    )
    min_access_count: Optional[int] = Field(
        None,
        description="Minimum access count",
        ge=0
    )
    
    # Temporal filters
    time_range_start: Optional[datetime] = Field(
        None,
        description="Start of time range"
    )
    time_range_end: Optional[datetime] = Field(
        None,
        description="End of time range"
    )
    
    # Semantic search
    semantic_query: Optional[str] = Field(
        None,
        description="Semantic search query",
        max_length=500
    )
    
    # Search options
    search_type: str = Field(
        default="hybrid",
        description="Search type (dense, sparse, hybrid)"
    )
    alpha: float = Field(
        default=0.7,
        description="Balance between dense and sparse search (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    include_temporal_decay: bool = Field(
        default=True,
        description="Include temporal decay in scoring"
    )
    
    # Sorting
    sort_by: str = Field(
        default="relevance",
        description="Field to sort by (relevance, confidence, created_at, last_accessed)"
    )
    sort_order: SortOrder = Field(
        default=SortOrder.DESC,
        description="Sort order"
    )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('search_type')
    def validate_search_type(cls, v):
        allowed_types = ["dense", "sparse", "hybrid"]
        if v not in allowed_types:
            raise ValueError(f"search_type must be one of {allowed_types}")
        return v


class UniversalKnowledgeResponse(BaseResponse):
    """Response for knowledge operations."""
    
    # Single knowledge item
    knowledge_id: Optional[str] = Field(
        None,
        description="Knowledge identifier"
    )
    knowledge_metadata: Optional[KnowledgeMetadata] = Field(
        None,
        description="Knowledge metadata"
    )
    knowledge_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Knowledge data"
    )
    
    # Query results
    knowledge_items: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of knowledge items (for queries)"
    )
    pagination: Optional[PaginationResponse] = Field(
        None,
        description="Pagination metadata (for queries)"
    )
    
    # Search metadata
    search_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Search-specific metadata"
    )
    temporal_scores: Optional[Dict[str, float]] = Field(
        None,
        description="Temporal decay scores for results"
    )


class KnowledgeConsolidationRequest(BaseRequest):
    """Request to consolidate knowledge from episodes."""
    
    # Consolidation parameters
    time_range_start: Optional[datetime] = Field(
        None,
        description="Start of time range for consolidation"
    )
    time_range_end: Optional[datetime] = Field(
        None,
        description="End of time range for consolidation"
    )
    min_episode_importance: float = Field(
        default=0.5,
        description="Minimum episode importance for consolidation",
        ge=0.0,
        le=1.0
    )
    min_cluster_size: int = Field(
        default=3,
        description="Minimum cluster size for consolidation",
        ge=2
    )
    
    # Target context
    target_agent_id: Optional[str] = Field(
        None,
        description="Target agent for consolidation"
    )
    target_team_id: Optional[str] = Field(
        None,
        description="Target team for consolidation"
    )
    
    # Consolidation options
    force_consolidation: bool = Field(
        default=False,
        description="Force consolidation even if recently done"
    )
    min_confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence for created knowledge",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class KnowledgeConsolidationResponse(BaseResponse):
    """Response for knowledge consolidation."""
    
    # Consolidation results
    episodes_processed: int = Field(
        ...,
        description="Number of episodes processed"
    )
    clusters_found: int = Field(
        ...,
        description="Number of episode clusters found"
    )
    knowledge_items_created: int = Field(
        ...,
        description="Number of knowledge items created"
    )
    knowledge_items_updated: int = Field(
        ...,
        description="Number of knowledge items updated"
    )
    
    # Quality metrics
    avg_confidence: float = Field(
        ...,
        description="Average confidence of created knowledge"
    )
    consolidation_quality: str = Field(
        ...,
        description="Overall consolidation quality assessment"
    )
    
    # Details
    consolidation_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed consolidation information"
    )
