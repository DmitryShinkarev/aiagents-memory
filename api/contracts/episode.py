"""
Episode-related API contracts.

This module defines the stable contracts for episodic memory operations.
Episodes represent specific events and interactions with temporal context.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from api.contracts.common import (
    BaseRequest,
    BaseResponse,
    PaginationRequest,
    PaginationResponse,
    EpisodeScope,
    EpisodeType,
    EpisodeStatus,
    SortOrder,
)


class EpisodeContext(BaseModel):
    """Context information for an episode."""
    
    user_id: Optional[str] = Field(
        None,
        description="User involved in the episode",
        max_length=255
    )
    agent_id: str = Field(
        ...,
        description="Primary agent involved",
        min_length=1,
        max_length=255
    )
    team_id: Optional[str] = Field(
        None,
        description="Team involved in the episode",
        max_length=255
    )
    session_id: Optional[str] = Field(
        None,
        description="Session identifier",
        max_length=255
    )
    parent_episode_id: Optional[str] = Field(
        None,
        description="Parent episode for nested episodes",
        max_length=255
    )
    participating_agents: List[str] = Field(
        default_factory=list,
        description="All agents that participated"
    )


class EpisodeTrajectory(BaseModel):
    """Single step in episode trajectory."""
    
    step_id: str = Field(
        ...,
        description="Unique step identifier",
        max_length=255
    )
    timestamp: datetime = Field(
        ...,
        description="Step timestamp"
    )
    role: str = Field(
        ...,
        description="Role (user, agent, system, etc.)",
        max_length=50
    )
    action: str = Field(
        ...,
        description="Action taken",
        max_length=200
    )
    content: Any = Field(
        ...,
        description="Action content"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional step metadata"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UniversalEpisodeWriteRequest(BaseRequest):
    """Request to create a new episode."""
    
    # Episode context
    context: EpisodeContext = Field(
        ...,
        description="Episode context"
    )
    
    # Episode properties
    scope: EpisodeScope = Field(
        ...,
        description="Episode visibility scope"
    )
    episode_type: EpisodeType = Field(
        ...,
        description="Type of episode"
    )
    
    # Episode content
    title: str = Field(
        ...,
        description="Episode title",
        min_length=1,
        max_length=200
    )
    trajectory: List[EpisodeTrajectory] = Field(
        ...,
        description="Episode trajectory (sequence of actions)"
    )
    outcome: Optional[str] = Field(
        None,
        description="Episode outcome",
        max_length=1000
    )
    status: EpisodeStatus = Field(
        default=EpisodeStatus.COMPLETED,
        description="Episode status"
    )
    
    # Quality metrics
    success: bool = Field(
        ...,
        description="Whether episode was successful"
    )
    importance: float = Field(
        ...,
        description="Episode importance (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    user_satisfaction: Optional[float] = Field(
        None,
        description="User satisfaction rating (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Episode tags",
        max_items=20
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional episode metadata"
    )
    
    # Optional embedding for semantic search
    embedding: Optional[List[float]] = Field(
        None,
        description="Episode embedding vector"
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


class UniversalEpisodeQueryRequest(BaseRequest, PaginationRequest):
    """Request to query episodes."""
    
    # Context filters
    filter_by_user_id: Optional[str] = Field(
        None,
        description="Filter by user ID"
    )
    filter_by_agent_id: Optional[str] = Field(
        None,
        description="Filter by agent ID"
    )
    filter_by_team_id: Optional[str] = Field(
        None,
        description="Filter by team ID"
    )
    filter_by_session_id: Optional[str] = Field(
        None,
        description="Filter by session ID"
    )
    
    # Property filters
    filter_by_scope: Optional[List[EpisodeScope]] = Field(
        None,
        description="Filter by scope"
    )
    filter_by_type: Optional[List[EpisodeType]] = Field(
        None,
        description="Filter by episode type"
    )
    filter_by_status: Optional[List[EpisodeStatus]] = Field(
        None,
        description="Filter by status"
    )
    filter_by_tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags"
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
    
    # Quality filters
    min_importance: Optional[float] = Field(
        None,
        description="Minimum importance threshold",
        ge=0.0,
        le=1.0
    )
    only_successful: Optional[bool] = Field(
        None,
        description="Only successful episodes"
    )
    
    # Semantic search
    semantic_query: Optional[str] = Field(
        None,
        description="Semantic search query",
        max_length=500
    )
    
    # Sorting
    sort_by: str = Field(
        default="timestamp",
        description="Field to sort by"
    )
    sort_order: SortOrder = Field(
        default=SortOrder.DESC,
        description="Sort order"
    )
    
    # Options
    include_trajectory: bool = Field(
        default=True,
        description="Include episode trajectory"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include episode metadata"
    )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UniversalEpisodeResponse(BaseResponse):
    """Response for episode operations."""
    
    # Single episode
    episode_id: Optional[str] = Field(
        None,
        description="Episode identifier"
    )
    episode_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Episode metadata"
    )
    episode_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Episode data"
    )
    
    # Query results
    episodes: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of episodes (for queries)"
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


class EpisodeConsolidationRequest(BaseRequest):
    """Request to consolidate episodes into knowledge."""
    
    # Consolidation parameters
    time_range_start: Optional[datetime] = Field(
        None,
        description="Start of time range for consolidation"
    )
    time_range_end: Optional[datetime] = Field(
        None,
        description="End of time range for consolidation"
    )
    min_importance: float = Field(
        default=0.5,
        description="Minimum importance for consolidation",
        ge=0.0,
        le=1.0
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
    
    # Options
    force_consolidation: bool = Field(
        default=False,
        description="Force consolidation even if recently done"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EpisodeConsolidationResponse(BaseResponse):
    """Response for episode consolidation."""
    
    # Consolidation results
    episodes_processed: int = Field(
        ...,
        description="Number of episodes processed"
    )
    knowledge_items_created: int = Field(
        ...,
        description="Number of knowledge items created"
    )
    clusters_found: int = Field(
        ...,
        description="Number of episode clusters found"
    )
    
    # Details
    consolidation_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed consolidation information"
    )
