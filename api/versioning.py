"""
API versioning management.

This module handles API versioning, backward compatibility, and contract evolution.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime

from pydantic import BaseModel, Field

from .contracts.common import APIVersion


class VersionCompatibility(str, Enum):
    """Version compatibility levels."""
    FULLY_COMPATIBLE = "fully_compatible"
    BACKWARD_COMPATIBLE = "backward_compatible"
    BREAKING_CHANGE = "breaking_change"


class ContractChange(BaseModel):
    """Represents a change to an API contract."""
    
    change_type: str = Field(..., description="Type of change")
    description: str = Field(..., description="Description of the change")
    impact: VersionCompatibility = Field(..., description="Compatibility impact")
    migration_guide: Optional[str] = Field(None, description="Migration guide")
    deprecated_in: Optional[APIVersion] = Field(None, description="Version when deprecated")
    removed_in: Optional[APIVersion] = Field(None, description="Version when removed")
    
    class Config:
        use_enum_values = True


class APIVersionManager:
    """Manages API versions and contract evolution."""
    
    def __init__(self):
        self._versions: Dict[APIVersion, Dict[str, Any]] = {}
        self._contract_changes: List[ContractChange] = []
        self._current_version = APIVersion.V1
        self._supported_versions = [APIVersion.V1]
        
        # Initialize with default version info
        self._initialize_default_versions()
    
    def _initialize_default_versions(self):
        """Initialize default version information."""
        self._versions[APIVersion.V1] = {
            "release_date": datetime(2024, 1, 1),
            "status": "stable",
            "deprecation_date": None,
            "end_of_life": None,
            "features": [
                "entity_operations",
                "episode_operations", 
                "knowledge_operations",
                "facts_operations",
                "idempotency",
                "pagination",
                "semantic_search"
            ]
        }
    
    def register_version(
        self,
        version: APIVersion,
        release_date: datetime,
        status: str = "stable",
        features: Optional[List[str]] = None,
        deprecation_date: Optional[datetime] = None,
        end_of_life: Optional[datetime] = None
    ):
        """Register a new API version."""
        self._versions[version] = {
            "release_date": release_date,
            "status": status,
            "deprecation_date": deprecation_date,
            "end_of_life": end_of_life,
            "features": features or []
        }
        
        if version not in self._supported_versions:
            self._supported_versions.append(version)
    
    def deprecate_version(
        self,
        version: APIVersion,
        deprecation_date: datetime,
        end_of_life: Optional[datetime] = None
    ):
        """Deprecate an API version."""
        if version in self._versions:
            self._versions[version]["status"] = "deprecated"
            self._versions[version]["deprecation_date"] = deprecation_date
            self._versions[version]["end_of_life"] = end_of_life
    
    def add_contract_change(
        self,
        change_type: str,
        description: str,
        impact: VersionCompatibility,
        migration_guide: Optional[str] = None,
        deprecated_in: Optional[APIVersion] = None,
        removed_in: Optional[APIVersion] = None
    ):
        """Add a contract change for tracking."""
        change = ContractChange(
            change_type=change_type,
            description=description,
            impact=impact,
            migration_guide=migration_guide,
            deprecated_in=deprecated_in,
            removed_in=removed_in
        )
        self._contract_changes.append(change)
    
    def is_version_supported(self, version: APIVersion) -> bool:
        """Check if a version is supported."""
        if version not in self._versions:
            return False
        
        version_info = self._versions[version]
        
        # Check if version is end-of-life
        if version_info.get("end_of_life"):
            return datetime.utcnow() < version_info["end_of_life"]
        
        return version in self._supported_versions
    
    def get_version_info(self, version: APIVersion) -> Optional[Dict[str, Any]]:
        """Get information about a specific version."""
        return self._versions.get(version)
    
    def get_supported_versions(self) -> List[APIVersion]:
        """Get list of supported versions."""
        return [
            v for v in self._supported_versions 
            if self.is_version_supported(v)
        ]
    
    def get_current_version(self) -> APIVersion:
        """Get the current API version."""
        return self._current_version
    
    def set_current_version(self, version: APIVersion):
        """Set the current API version."""
        if self.is_version_supported(version):
            self._current_version = version
        else:
            raise ValueError(f"Version {version} is not supported")
    
    def get_version_compatibility(self, from_version: APIVersion, to_version: APIVersion) -> VersionCompatibility:
        """Get compatibility level between two versions."""
        if from_version == to_version:
            return VersionCompatibility.FULLY_COMPATIBLE
        
        # Check for breaking changes between versions
        breaking_changes = [
            change for change in self._contract_changes
            if change.impact == VersionCompatibility.BREAKING_CHANGE
        ]
        
        if breaking_changes:
            return VersionCompatibility.BREAKING_CHANGE
        
        return VersionCompatibility.BACKWARD_COMPATIBLE
    
    def validate_request_version(self, request_version: APIVersion) -> bool:
        """Validate that a request version is supported."""
        return self.is_version_supported(request_version)
    
    def get_migration_guide(self, from_version: APIVersion, to_version: APIVersion) -> Optional[str]:
        """Get migration guide between versions."""
        if from_version == to_version:
            return None
        
        # Find relevant changes
        relevant_changes = [
            change for change in self._contract_changes
            if change.migration_guide and (
                change.deprecated_in == from_version or
                change.removed_in == to_version
            )
        ]
        
        if relevant_changes:
            return "\n".join([change.migration_guide for change in relevant_changes])
        
        return None
    
    def get_deprecation_warnings(self, version: APIVersion) -> List[str]:
        """Get deprecation warnings for a version."""
        warnings = []
        
        if version in self._versions:
            version_info = self._versions[version]
            
            if version_info.get("status") == "deprecated":
                deprecation_date = version_info.get("deprecation_date")
                end_of_life = version_info.get("end_of_life")
                
                if deprecation_date:
                    warnings.append(f"Version {version} was deprecated on {deprecation_date}")
                
                if end_of_life:
                    warnings.append(f"Version {version} will reach end-of-life on {end_of_life}")
        
        return warnings
    
    def get_version_features(self, version: APIVersion) -> List[str]:
        """Get features available in a version."""
        if version in self._versions:
            return self._versions[version].get("features", [])
        return []
    
    def is_feature_available(self, version: APIVersion, feature: str) -> bool:
        """Check if a feature is available in a version."""
        features = self.get_version_features(version)
        return feature in features


# Global version manager instance
version_manager = APIVersionManager()


def get_version_manager() -> APIVersionManager:
    """Get the global version manager instance."""
    return version_manager


def validate_api_version(version: APIVersion) -> bool:
    """Validate API version for requests."""
    return version_manager.validate_request_version(version)


def get_version_info(version: APIVersion) -> Optional[Dict[str, Any]]:
    """Get version information."""
    return version_manager.get_version_info(version)


def get_supported_versions() -> List[APIVersion]:
    """Get supported API versions."""
    return version_manager.get_supported_versions()
