"""
User facts API contracts.

This module defines the stable contracts for user profile and facts operations.
Facts represent personal information about users with full version history.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from api.contracts.common import (
    BaseRequest,
    BaseResponse,
    PaginationRequest,
    PaginationResponse,
    SourceType,
    SortOrder,
)


class FactType(str, Enum):
    """Type of user fact."""
    PERSONAL = "personal"        # Name, age, etc.
    LOCATION = "location"        # City, country, etc.
    PREFERENCE = "preference"    # Preferences, likes, etc.
    BEHAVIOR = "behavior"        # Behavioral patterns
    RELATIONSHIP = "relationship" # Relationships with others


class FactVersion(BaseModel):
    """Version of a user fact."""
    
    version_id: str = Field(..., description="Unique version identifier")
    value: str = Field(..., description="Fact value")
    confidence: float = Field(..., description="Confidence level (0.0-1.0)", ge=0.0, le=1.0)
    
    # Temporal validity
    valid_from: datetime = Field(..., description="When this version became valid")
    valid_until: Optional[datetime] = Field(None, description="When this version expires")
    
    # Source information
    source: SourceType = Field(..., description="Source of this fact version")
    evidence: List[str] = Field(
        default_factory=list,
        description="Episode IDs that support this version"
    )
    
    # Status
    deprecated: bool = Field(default=False, description="Whether this version is deprecated")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UniversalFactWriteRequest(BaseRequest):
    """Request to create or update a user fact."""
    
    # Target user
    user_id: str = Field(
        ...,
        description="User identifier",
        min_length=1,
        max_length=255
    )
    
    # Fact information
    fact_type: str = Field(
        ...,
        description="Type of fact",
        min_length=1,
        max_length=50
    )
    key: str = Field(
        ...,
        description="Fact key (e.g., 'name', 'city', 'favorite_color')",
        min_length=1,
        max_length=100
    )
    value: str = Field(
        ...,
        description="Fact value",
        min_length=1,
        max_length=1000
    )
    
    # Quality metrics
    confidence: float = Field(
        ...,
        description="Confidence level (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    # Source information
    source: SourceType = Field(
        ...,
        description="Source of the fact"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Episode IDs that support this fact"
    )
    
    # Temporal validity
    valid_from: Optional[datetime] = Field(
        None,
        description="When this fact becomes valid (defaults to now)"
    )
    valid_until: Optional[datetime] = Field(
        None,
        description="When this fact expires"
    )
    
    # Conflict resolution
    force_update: bool = Field(
        default=False,
        description="Force update even if confidence is lower"
    )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('fact_type')
    def validate_fact_type(cls, v):
        allowed_types = ["personal", "location", "preference", "behavior", "relationship"]
        if v not in allowed_types:
            raise ValueError(f"fact_type must be one of {allowed_types}")
        return v


class UniversalFactQueryRequest(BaseRequest, PaginationRequest):
    """Request to query user facts."""
    
    # Target user
    user_id: str = Field(
        ...,
        description="User identifier",
        min_length=1,
        max_length=255
    )
    
    # Filters
    filter_by_fact_type: Optional[List[str]] = Field(
        None,
        description="Filter by fact types"
    )
    filter_by_key: Optional[List[str]] = Field(
        None,
        description="Filter by fact keys"
    )
    filter_by_source: Optional[List[SourceType]] = Field(
        None,
        description="Filter by source types"
    )
    
    # Quality filters
    min_confidence: Optional[float] = Field(
        None,
        description="Minimum confidence threshold",
        ge=0.0,
        le=1.0
    )
    only_current: bool = Field(
        default=True,
        description="Only return current (non-deprecated) facts"
    )
    
    # Temporal filters
    valid_at: Optional[datetime] = Field(
        None,
        description="Point in time for fact validity"
    )
    time_range_start: Optional[datetime] = Field(
        None,
        description="Start of time range"
    )
    time_range_end: Optional[datetime] = Field(
        None,
        description="End of time range"
    )
    
    # Sorting
    sort_by: str = Field(
        default="key",
        description="Field to sort by (key, fact_type, confidence, last_updated)"
    )
    sort_order: SortOrder = Field(
        default=SortOrder.ASC,
        description="Sort order"
    )
    
    # Options
    include_history: bool = Field(
        default=False,
        description="Include version history"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include fact metadata"
    )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UniversalFactResponse(BaseResponse):
    """Response for fact operations."""
    
    # Single fact
    fact_id: Optional[str] = Field(
        None,
        description="Fact identifier"
    )
    fact_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Fact metadata"
    )
    fact_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Fact data"
    )
    
    # Query results
    facts: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of facts (for queries)"
    )
    pagination: Optional[PaginationResponse] = Field(
        None,
        description="Pagination metadata (for queries)"
    )
    
    # Conflict resolution info
    conflict_resolution: Optional[Dict[str, Any]] = Field(
        None,
        description="Information about conflict resolution"
    )


class UserProfileRequest(BaseRequest):
    """Request to get user profile summary."""
    
    user_id: str = Field(
        ...,
        description="User identifier",
        min_length=1,
        max_length=255
    )
    
    # Options
    include_facts: bool = Field(
        default=True,
        description="Include user facts"
    )
    include_episodes: bool = Field(
        default=False,
        description="Include recent episodes"
    )
    include_knowledge: bool = Field(
        default=False,
        description="Include relevant knowledge"
    )
    
    # Limits
    max_facts: int = Field(
        default=100,
        description="Maximum number of facts to return",
        ge=1,
        le=1000
    )
    max_episodes: int = Field(
        default=10,
        description="Maximum number of episodes to return",
        ge=1,
        le=100
    )
    max_knowledge: int = Field(
        default=10,
        description="Maximum number of knowledge items to return",
        ge=1,
        le=100
    )


class UserProfileResponse(BaseResponse):
    """Response with user profile information."""
    
    user_id: str = Field(..., description="User identifier")
    
    # Profile data
    profile_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Profile summary"
    )
    facts: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="User facts"
    )
    recent_episodes: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Recent episodes"
    )
    relevant_knowledge: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Relevant knowledge"
    )
    
    # Metadata
    profile_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Profile metadata"
    )


class FactExtractionRequest(BaseRequest):
    """Request to extract facts from text."""
    
    # Source text
    text: str = Field(
        ...,
        description="Text to extract facts from",
        min_length=1,
        max_length=10000
    )
    
    # Target user
    user_id: str = Field(
        ...,
        description="User to associate facts with",
        min_length=1,
        max_length=255
    )
    
    # Extraction options
    fact_types: Optional[List[str]] = Field(
        None,
        description="Specific fact types to extract"
    )
    min_confidence: float = Field(
        default=0.5,
        description="Minimum confidence for extracted facts",
        ge=0.0,
        le=1.0
    )
    auto_save: bool = Field(
        default=False,
        description="Automatically save extracted facts"
    )
    
    # Context
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for extraction"
    )


class FactExtractionResponse(BaseResponse):
    """Response with extracted facts."""
    
    # Extraction results
    extracted_facts: List[Dict[str, Any]] = Field(
        ...,
        description="List of extracted facts"
    )
    facts_saved: int = Field(
        ...,
        description="Number of facts saved (if auto_save=True)"
    )
    
    # Quality metrics
    avg_confidence: float = Field(
        ...,
        description="Average confidence of extracted facts"
    )
    extraction_quality: str = Field(
        ...,
        description="Overall extraction quality assessment"
    )
    
    # Details
    extraction_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed extraction information"
    )
