"""
Entity-related API contracts.

This module defines the stable contracts for dynamic entity operations.
Entities are business objects with dynamic schemas (e.g., employees, departments).
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
    MemoryScope,
    UpdateOperation,
    SortOrder,
    Precondition,
)


class EntityMetadata(BaseModel):
    """Metadata for an entity."""
    
    entity_id: str = Field(..., description="Unique entity identifier")
    entity_namespace: str = Field(..., description="Entity namespace (e.g., 'hr', 'finance')")
    entity_type: str = Field(..., description="Entity type (e.g., 'employee', 'department')")
    schema_version: str = Field(..., description="Schema version used")
    
    # Ownership
    created_by: str = Field(..., description="Agent/team that created the entity")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_by: str = Field(..., description="Agent/team that last updated the entity")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Versioning
    current_version: int = Field(..., description="Current version number", ge=1)
    access_scope: MemoryScope = Field(..., description="Access scope")
    content_hash: str = Field(..., description="SHA256 hash of entity data")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EntityVersion(BaseModel):
    """Version history for an entity."""
    
    version_id: str = Field(..., description="Unique version identifier")
    version_number: int = Field(..., description="Version number", ge=1)
    data: Dict[str, Any] = Field(..., description="Entity data snapshot")
    changed_fields: List[str] = Field(..., description="Fields that changed")
    changed_by: str = Field(..., description="Agent/team that made changes")
    changed_at: datetime = Field(..., description="Change timestamp")
    change_reason: Optional[str] = Field(None, description="Reason for change")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UniversalEntityWriteRequest(BaseRequest):
    """Request to create a new entity."""
    
    # Target entity
    entity_namespace: str = Field(
        ...,
        description="Entity namespace (e.g., 'hr', 'finance')",
        min_length=1,
        max_length=100
    )
    entity_type: str = Field(
        ...,
        description="Entity type (e.g., 'employee', 'department')",
        min_length=1,
        max_length=100
    )
    
    # Entity data (free-form structure)
    entity_data: Dict[str, Any] = Field(
        ...,
        description="Entity data (validated against schema)"
    )
    
    # Access control
    access_scope: MemoryScope = Field(
        default=MemoryScope.TEAM_SHARED,
        description="Access scope for the entity"
    )
    allowed_teams: List[str] = Field(
        default_factory=list,
        description="Teams with access to this entity"
    )
    allowed_agents: List[str] = Field(
        default_factory=list,
        description="Agents with access to this entity"
    )
    allowed_users: List[str] = Field(
        default_factory=list,
        description="Users with access to this entity"
    )
    
    # Business context
    business_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional business context"
    )
    
    class Config:
        use_enum_values = True


class UniversalEntityUpdateRequest(BaseRequest):
    """Request to update an existing entity."""
    
    # Target entity
    entity_namespace: str = Field(
        ...,
        description="Entity namespace",
        min_length=1,
        max_length=100
    )
    entity_type: str = Field(
        ...,
        description="Entity type",
        min_length=1,
        max_length=100
    )
    entity_id: str = Field(
        ...,
        description="Entity identifier",
        min_length=1,
        max_length=255
    )
    
    # Update operation
    update_operation: UpdateOperation = Field(
        default=UpdateOperation.MERGE,
        description="Type of update operation"
    )
    update_data: Dict[str, Any] = Field(
        ...,
        description="Data to update"
    )
    
    # Optimistic locking
    preconditions: Optional[Precondition] = Field(
        None,
        description="Preconditions for update"
    )
    
    # Change tracking
    change_reason: Optional[str] = Field(
        None,
        description="Reason for the change",
        max_length=500
    )
    
    class Config:
        use_enum_values = True


class UniversalEntityReadRequest(BaseRequest):
    """Request to read an entity."""
    
    # Target entity
    entity_namespace: str = Field(
        ...,
        description="Entity namespace",
        min_length=1,
        max_length=100
    )
    entity_type: str = Field(
        ...,
        description="Entity type",
        min_length=1,
        max_length=100
    )
    entity_id: str = Field(
        ...,
        description="Entity identifier",
        min_length=1,
        max_length=255
    )
    
    # Options
    include_metadata: bool = Field(
        default=True,
        description="Include entity metadata"
    )
    include_history: bool = Field(
        default=False,
        description="Include version history"
    )
    version: Optional[int] = Field(
        None,
        description="Specific version to retrieve (time-travel)",
        ge=1
    )
    fields: Optional[List[str]] = Field(
        None,
        description="Specific fields to return (projection)"
    )


class UniversalEntityQueryRequest(BaseRequest, PaginationRequest):
    """Request to query entities."""
    
    # Target entity type
    entity_namespace: str = Field(
        ...,
        description="Entity namespace",
        min_length=1,
        max_length=100
    )
    entity_type: str = Field(
        ...,
        description="Entity type",
        min_length=1,
        max_length=100
    )
    
    # Filters (stable structure)
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Query filters (field: value or field: {operator: value})"
    )
    
    # Sorting
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by"
    )
    sort_order: SortOrder = Field(
        default=SortOrder.ASC,
        description="Sort order"
    )
    
    # Options
    include_metadata: bool = Field(
        default=True,
        description="Include entity metadata"
    )
    fields: Optional[List[str]] = Field(
        None,
        description="Specific fields to return (projection)"
    )
    
    class Config:
        use_enum_values = True


class UniversalEntityResponse(BaseResponse):
    """Response for entity operations."""
    
    # Entity data
    entity_id: Optional[str] = Field(
        None,
        description="Entity identifier"
    )
    entity_metadata: Optional[EntityMetadata] = Field(
        None,
        description="Entity metadata"
    )
    entity_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Entity data"
    )
    version_history: Optional[List[EntityVersion]] = Field(
        None,
        description="Version history"
    )
    
    # Query results
    entities: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of entities (for queries)"
    )
    pagination: Optional[PaginationResponse] = Field(
        None,
        description="Pagination metadata (for queries)"
    )


class EntitySchemaInfo(BaseModel):
    """Information about an entity schema."""
    
    entity_type: str = Field(..., description="Entity type")
    version: str = Field(..., description="Schema version")
    description: str = Field(..., description="Schema description")
    created_by: str = Field(..., description="Team that created the schema")
    created_at: datetime = Field(..., description="Creation timestamp")
    active: bool = Field(..., description="Whether schema is active")
    
    # Schema structure
    fields_count: int = Field(..., description="Number of fields")
    indexed_fields: List[str] = Field(..., description="Indexed fields")
    unique_fields: List[str] = Field(..., description="Unique fields")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EntitySchemaRequest(BaseRequest):
    """Request to get entity schema information."""
    
    entity_namespace: str = Field(
        ...,
        description="Entity namespace",
        min_length=1,
        max_length=100
    )
    entity_type: str = Field(
        ...,
        description="Entity type",
        min_length=1,
        max_length=100
    )
    version: Optional[str] = Field(
        None,
        description="Specific schema version"
    )


class EntitySchemaResponse(BaseResponse):
    """Response with entity schema information."""
    
    schema_info: Optional[EntitySchemaInfo] = Field(
        None,
        description="Schema information"
    )
    schema_definition: Optional[Dict[str, Any]] = Field(
        None,
        description="Full schema definition"
    )
