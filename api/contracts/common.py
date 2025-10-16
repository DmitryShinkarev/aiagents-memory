"""
Common types and base classes for API contracts.

This module defines the fundamental types and enums used across all API contracts.
These types must remain stable to ensure backward compatibility.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class APIVersion(str, Enum):
    """API version enumeration."""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


class OperationStatus(str, Enum):
    """Operation execution status."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"


class MemoryScope(str, Enum):
    """Memory access scope levels."""
    USER_PRIVATE = "user_private"
    AGENT_PRIVATE = "agent_private"
    TEAM_SHARED = "team_shared"
    CROSS_TEAM = "cross_team"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class EpisodeScope(str, Enum):
    """Episode visibility scope."""
    USER_PRIVATE = "user_private"
    AGENT_PRIVATE = "agent_private"
    TEAM_SHARED = "team_shared"
    CROSS_TEAM = "cross_team"
    ORGANIZATION = "organization"


class EpisodeType(str, Enum):
    """Type of episode."""
    INTERACTION = "interaction"
    TASK_EXECUTION = "task_execution"
    COLLABORATION = "collaboration"
    LEARNING = "learning"
    ERROR = "error"
    DECISION = "decision"


class EpisodeStatus(str, Enum):
    """Episode execution status."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceType(str, Enum):
    """Source of knowledge or fact."""
    USER_STATED = "user_stated"
    INFERRED = "inferred"
    OBSERVED = "observed"
    CONSOLIDATED = "consolidated"
    SYSTEM = "system"


class FieldType(str, Enum):
    """Dynamic entity field types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    REFERENCE = "reference"
    ARRAY = "array"


class UpdateOperation(str, Enum):
    """Entity update operation types."""
    SET = "set"      # Full replacement
    MERGE = "merge"  # Merge with existing
    PATCH = "patch"  # JSON Patch RFC 6902


class SortOrder(str, Enum):
    """Sort order for queries."""
    ASC = "asc"
    DESC = "desc"


class BaseRequest(BaseModel):
    """Base request model with common fields."""
    
    # Idempotency
    idempotency_key: str = Field(
        ...,
        description="Unique key for idempotent operations",
        min_length=1,
        max_length=255
    )
    
    # Metadata
    api_version: APIVersion = Field(
        default=APIVersion.V1,
        description="API version"
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique request identifier"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Request timestamp"
    )
    
    # Context
    requesting_agent_id: str = Field(
        ...,
        description="ID of the agent making the request",
        min_length=1,
        max_length=255
    )
    requesting_team_id: Optional[str] = Field(
        None,
        description="ID of the team making the request",
        max_length=255
    )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    
    request_id: str = Field(
        ...,
        description="Echo of the request ID"
    )
    status: OperationStatus = Field(
        ...,
        description="Operation execution status"
    )
    execution_time_ms: float = Field(
        ...,
        description="Operation execution time in milliseconds"
    )
    
    # Idempotency
    idempotent: bool = Field(
        default=False,
        description="Whether this was an idempotent operation"
    )
    idempotency_key: Optional[str] = Field(
        None,
        description="Idempotency key used"
    )
    
    # Error handling
    error_code: Optional[str] = Field(
        None,
        description="Error code if operation failed"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if operation failed"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warning messages"
    )
    
    class Config:
        use_enum_values = True


class PaginationRequest(BaseModel):
    """Pagination parameters for queries."""
    
    cursor: Optional[str] = Field(
        None,
        description="Cursor for pagination (base64 encoded)"
    )
    limit: int = Field(
        default=50,
        description="Number of items to return",
        ge=1,
        le=1000
    )
    
    @validator('limit')
    def validate_limit(cls, v):
        if v > 1000:
            raise ValueError("Limit cannot exceed 1000")
        return v


class PaginationResponse(BaseModel):
    """Pagination metadata for responses."""
    
    has_more: bool = Field(
        ...,
        description="Whether there are more items available"
    )
    next_cursor: Optional[str] = Field(
        None,
        description="Cursor for next page (base64 encoded)"
    )
    total_count: Optional[int] = Field(
        None,
        description="Total number of items (if available)"
    )


class IdempotencyGuard(BaseModel):
    """Idempotency guard for operations."""
    
    operation_type: str = Field(
        ...,
        description="Type of operation (e.g., 'entity_create', 'episode_create')"
    )
    idempotency_key: str = Field(
        ...,
        description="Unique key for idempotent operations"
    )
    request_hash: str = Field(
        ...,
        description="SHA256 hash of critical request fields"
    )
    ttl_days: int = Field(
        default=7,
        description="Time to live for idempotency cache in days"
    )
    
    class Config:
        frozen = True  # Immutable for caching


class ValidationRule(BaseModel):
    """Validation rule for dynamic entity fields."""
    
    min_length: Optional[int] = Field(None, ge=0)
    max_length: Optional[int] = Field(None, ge=0)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = Field(None, description="Regex pattern")
    enum_values: Optional[List[str]] = Field(None, description="Allowed enum values")
    
    @validator('max_length')
    def validate_max_length(cls, v, values):
        if v is not None and 'min_length' in values and values['min_length'] is not None:
            if v < values['min_length']:
                raise ValueError("max_length must be >= min_length")
        return v
    
    @validator('max_value')
    def validate_max_value(cls, v, values):
        if v is not None and 'min_value' in values and values['min_value'] is not None:
            if v < values['min_value']:
                raise ValueError("max_value must be >= min_value")
        return v


class Precondition(BaseModel):
    """Optimistic locking preconditions."""
    
    version: Optional[int] = Field(None, description="Expected version number")
    content_hash: Optional[str] = Field(None, description="Expected content hash")
    field_conditions: Optional[Dict[str, Any]] = Field(
        None,
        description="Field-specific conditions"
    )
    
    class Config:
        extra = "allow"  # Allow additional field conditions
