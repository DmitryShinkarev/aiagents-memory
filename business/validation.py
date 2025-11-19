"""
Request validation for API contracts.

This module provides validation logic for API requests, ensuring data integrity
and business rule compliance before processing.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ValidationError as PydanticValidationError

from api.contracts.common import (
    APIVersion,
    MemoryScope,
    EpisodeScope,
    EpisodeType,
    EpisodeStatus,
    SourceType,
    FieldType,
    UpdateOperation,
    ValidationRule
)
from api.contracts.entity import UniversalEntityWriteRequest, UniversalEntityUpdateRequest
from api.contracts.episode import UniversalEpisodeWriteRequest
from api.contracts.knowledge import UniversalKnowledgeWriteRequest
from api.contracts.facts import UniversalFactWriteRequest

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.code = code


class RequestValidator:
    """Validator for API requests."""
    
    def __init__(self):
        self._validation_rules: Dict[str, Dict[str, ValidationRule]] = {}
        self._initialize_validation_rules()
    
    def _initialize_validation_rules(self):
        """Initialize validation rules for different entity types."""
        # Common validation rules
        self._validation_rules["common"] = {
            "idempotency_key": ValidationRule(
                min_length=1,
                max_length=255,
                pattern=r"^[a-zA-Z0-9_-]+$"
            ),
            "agent_id": ValidationRule(
                min_length=1,
                max_length=255,
                pattern=r"^[a-zA-Z0-9_-]+$"
            ),
            "team_id": ValidationRule(
                min_length=1,
                max_length=255,
                pattern=r"^[a-zA-Z0-9_-]+$"
            ),
            "user_id": ValidationRule(
                min_length=1,
                max_length=255,
                pattern=r"^[a-zA-Z0-9_-]+$"
            ),
            "entity_namespace": ValidationRule(
                min_length=1,
                max_length=100,
                pattern=r"^[a-zA-Z0-9_-]+$"
            ),
            "entity_type": ValidationRule(
                min_length=1,
                max_length=100,
                pattern=r"^[a-zA-Z0-9_-]+$"
            ),
            "entity_id": ValidationRule(
                min_length=1,
                max_length=255,
                pattern=r"^[a-zA-Z0-9_-]+$"
            )
        }
        
        # HR entity validation rules
        self._validation_rules["employee"] = {
            "employee_id": ValidationRule(
                min_length=1,
                max_length=50,
                pattern=r"^[A-Z0-9]+$"
            ),
            "first_name": ValidationRule(
                min_length=1,
                max_length=100,
                pattern=r"^[a-zA-Zа-яА-Я\s-]+$"
            ),
            "last_name": ValidationRule(
                min_length=1,
                max_length=100,
                pattern=r"^[a-zA-Zа-яА-Я\s-]+$"
            ),
            "email": ValidationRule(
                pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            ),
            "position": ValidationRule(
                min_length=1,
                max_length=200
            ),
            "salary": ValidationRule(
                min_value=0,
                max_value=10000000
            )
        }
        
        self._validation_rules["department"] = {
            "name": ValidationRule(
                min_length=1,
                max_length=200
            ),
            "code": ValidationRule(
                min_length=1,
                max_length=20,
                pattern=r"^[A-Z0-9_-]+$"
            ),
            "budget": ValidationRule(
                min_value=0,
                max_value=1000000000
            ),
            "employee_count": ValidationRule(
                min_value=0,
                max_value=10000
            )
        }
    
    def validate_entity_write_request(self, request: UniversalEntityWriteRequest) -> None:
        """Validate entity write request."""
        try:
            # Validate common fields
            self._validate_common_fields(request.dict())
            
            # Validate entity-specific fields
            entity_type = request.entity_type
            if entity_type in self._validation_rules:
                self._validate_entity_data(
                    request.entity_data,
                    self._validation_rules[entity_type]
                )
            
            # Validate access control
            self._validate_access_control(request)
            
            # Validate business rules
            self._validate_entity_business_rules(request)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Entity write validation failed: {e}")
            raise ValidationError(f"Validation failed: {str(e)}")
    
    def validate_entity_update_request(self, request: UniversalEntityUpdateRequest) -> None:
        """Validate entity update request."""
        try:
            # Validate common fields
            self._validate_common_fields(request.dict())
            
            # Validate update operation
            if request.update_operation == UpdateOperation.PATCH:
                self._validate_patch_operation(request.update_data)
            
            # Validate preconditions
            if request.preconditions:
                self._validate_preconditions(request.preconditions)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Entity update validation failed: {e}")
            raise ValidationError(f"Validation failed: {str(e)}")
    
    def validate_episode_write_request(self, request: UniversalEpisodeWriteRequest) -> None:
        """Validate episode write request."""
        try:
            # Validate common fields
            self._validate_common_fields(request.dict())
            
            # Validate episode-specific fields
            self._validate_episode_fields(request)
            
            # Validate trajectory
            self._validate_trajectory(request.trajectory)
            
            # Validate business rules
            self._validate_episode_business_rules(request)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Episode write validation failed: {e}")
            raise ValidationError(f"Validation failed: {str(e)}")
    
    def validate_knowledge_write_request(self, request: UniversalKnowledgeWriteRequest) -> None:
        """Validate knowledge write request."""
        try:
            # Validate common fields
            self._validate_common_fields(request.dict())
            
            # Validate knowledge-specific fields
            self._validate_knowledge_fields(request)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Knowledge write validation failed: {e}")
            raise ValidationError(f"Validation failed: {str(e)}")
    
    def validate_fact_write_request(self, request: UniversalFactWriteRequest) -> None:
        """Validate fact write request."""
        try:
            # Validate common fields
            self._validate_common_fields(request.dict())
            
            # Validate fact-specific fields
            self._validate_fact_fields(request)
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Fact write validation failed: {e}")
            raise ValidationError(f"Validation failed: {str(e)}")
    
    def _validate_common_fields(self, data: Dict[str, Any]) -> None:
        """Validate common fields across all requests."""
        common_rules = self._validation_rules["common"]
        
        for field, rule in common_rules.items():
            if field in data and data[field] is not None:
                self._validate_field(field, data[field], rule)
    
    def _validate_entity_data(
        self,
        entity_data: Dict[str, Any],
        rules: Dict[str, ValidationRule]
    ) -> None:
        """Validate entity data against rules."""
        for field, rule in rules.items():
            if field in entity_data and entity_data[field] is not None:
                self._validate_field(field, entity_data[field], rule)
    
    def _validate_field(self, field_name: str, value: Any, rule: ValidationRule) -> None:
        """Validate a single field against its rule."""
        # Type validation
        if isinstance(value, str):
            if rule.min_length is not None and len(value) < rule.min_length:
                raise ValidationError(
                    f"Field '{field_name}' must be at least {rule.min_length} characters long",
                    field=field_name,
                    code="min_length"
                )
            
            if rule.max_length is not None and len(value) > rule.max_length:
                raise ValidationError(
                    f"Field '{field_name}' must be at most {rule.max_length} characters long",
                    field=field_name,
                    code="max_length"
                )
            
            if rule.pattern and not re.match(rule.pattern, value):
                raise ValidationError(
                    f"Field '{field_name}' does not match required pattern",
                    field=field_name,
                    code="pattern"
                )
        
        elif isinstance(value, (int, float)):
            if rule.min_value is not None and value < rule.min_value:
                raise ValidationError(
                    f"Field '{field_name}' must be at least {rule.min_value}",
                    field=field_name,
                    code="min_value"
                )
            
            if rule.max_value is not None and value > rule.max_value:
                raise ValidationError(
                    f"Field '{field_name}' must be at most {rule.max_value}",
                    field=field_name,
                    code="max_value"
                )
        
        # Enum validation
        if rule.enum_values and value not in rule.enum_values:
            raise ValidationError(
                f"Field '{field_name}' must be one of {rule.enum_values}",
                field=field_name,
                code="enum"
            )
    
    def _validate_access_control(self, request: UniversalEntityWriteRequest) -> None:
        """Validate access control settings."""
        # Validate scope
        if request.access_scope not in [scope.value for scope in MemoryScope]:
            raise ValidationError(
                f"Invalid access scope: {request.access_scope}",
                field="access_scope",
                code="invalid_scope"
            )
        
        # Validate team/agent lists
        if request.allowed_teams:
            for team_id in request.allowed_teams:
                if not re.match(r"^[a-zA-Z0-9_-]+$", team_id):
                    raise ValidationError(
                        f"Invalid team ID format: {team_id}",
                        field="allowed_teams",
                        code="invalid_format"
                    )
        
        if request.allowed_agents:
            for agent_id in request.allowed_agents:
                if not re.match(r"^[a-zA-Z0-9_-]+$", agent_id):
                    raise ValidationError(
                        f"Invalid agent ID format: {agent_id}",
                        field="allowed_agents",
                        code="invalid_format"
                    )
    
    def _validate_entity_business_rules(self, request: UniversalEntityWriteRequest) -> None:
        """Validate entity-specific business rules."""
        entity_type = request.entity_type
        entity_data = request.entity_data
        
        if entity_type == "employee":
            self._validate_employee_business_rules(entity_data)
        elif entity_type == "department":
            self._validate_department_business_rules(entity_data)
    
    def _validate_employee_business_rules(self, employee_data: Dict[str, Any]) -> None:
        """Validate employee-specific business rules."""
        # Validate email format
        if "email" in employee_data:
            email = employee_data["email"]
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                raise ValidationError(
                    "Invalid email format",
                    field="email",
                    code="invalid_email"
                )
        
        # Validate hire date
        if "hire_date" in employee_data:
            hire_date = employee_data["hire_date"]
            if isinstance(hire_date, str):
                try:
                    hire_date = datetime.fromisoformat(hire_date.replace('Z', '+00:00'))
                except ValueError:
                    raise ValidationError(
                        "Invalid hire date format",
                        field="hire_date",
                        code="invalid_date"
                    )
            
            if hire_date > datetime.utcnow():
                raise ValidationError(
                    "Hire date cannot be in the future",
                    field="hire_date",
                    code="future_date"
                )
        
        # Validate salary
        if "salary" in employee_data:
            salary = employee_data["salary"]
            if salary < 0:
                raise ValidationError(
                    "Salary cannot be negative",
                    field="salary",
                    code="negative_salary"
                )
    
    def _validate_department_business_rules(self, department_data: Dict[str, Any]) -> None:
        """Validate department-specific business rules."""
        # Validate budget
        if "budget" in department_data:
            budget = department_data["budget"]
            if budget < 0:
                raise ValidationError(
                    "Budget cannot be negative",
                    field="budget",
                    code="negative_budget"
                )
        
        # Validate employee count
        if "employee_count" in department_data:
            employee_count = department_data["employee_count"]
            if employee_count < 0:
                raise ValidationError(
                    "Employee count cannot be negative",
                    field="employee_count",
                    code="negative_count"
                )
    
    def _validate_episode_fields(self, request: UniversalEpisodeWriteRequest) -> None:
        """Validate episode-specific fields."""
        # Validate scope
        if request.scope not in [scope.value for scope in EpisodeScope]:
            raise ValidationError(
                f"Invalid episode scope: {request.scope}",
                field="scope",
                code="invalid_scope"
            )
        
        # Validate episode type
        if request.episode_type not in [ep_type.value for ep_type in EpisodeType]:
            raise ValidationError(
                f"Invalid episode type: {request.episode_type}",
                field="episode_type",
                code="invalid_type"
            )
        
        # Validate status
        if request.status not in [status.value for status in EpisodeStatus]:
            raise ValidationError(
                f"Invalid episode status: {request.status}",
                field="status",
                code="invalid_status"
            )
        
        # Validate importance
        if not (0.0 <= request.importance <= 1.0):
            raise ValidationError(
                "Importance must be between 0.0 and 1.0",
                field="importance",
                code="invalid_range"
            )
        
        # Validate user satisfaction
        if request.user_satisfaction is not None:
            if not (0.0 <= request.user_satisfaction <= 1.0):
                raise ValidationError(
                    "User satisfaction must be between 0.0 and 1.0",
                    field="user_satisfaction",
                    code="invalid_range"
                )
    
    def _validate_trajectory(self, trajectory: List[Any]) -> None:
        """Validate episode trajectory."""
        if not trajectory:
            raise ValidationError(
                "Trajectory cannot be empty",
                field="trajectory",
                code="empty_trajectory"
            )
        
        if len(trajectory) > 1000:
            raise ValidationError(
                "Trajectory cannot have more than 1000 steps",
                field="trajectory",
                code="trajectory_too_long"
            )
        
        for i, step in enumerate(trajectory):
            if not isinstance(step, dict):
                raise ValidationError(
                    f"Trajectory step {i} must be a dictionary",
                    field=f"trajectory[{i}]",
                    code="invalid_step"
                )
            
            required_fields = ["step_id", "timestamp", "role", "action", "content"]
            for field in required_fields:
                if field not in step:
                    raise ValidationError(
                        f"Trajectory step {i} missing required field: {field}",
                        field=f"trajectory[{i}].{field}",
                        code="missing_field"
                    )
    
    def _validate_episode_business_rules(self, request: UniversalEpisodeWriteRequest) -> None:
        """Validate episode-specific business rules."""
        # Validate context
        context = request.context
        
        if not context.agent_id:
            raise ValidationError(
                "Agent ID is required in episode context",
                field="context.agent_id",
                code="missing_agent_id"
            )
        
        # Validate temporal consistency
        if request.trajectory:
            timestamps = [step.get("timestamp") for step in request.trajectory]
            if timestamps:
                try:
                    parsed_timestamps = [
                        datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        if isinstance(ts, str) else ts
                        for ts in timestamps
                    ]
                    
                    if parsed_timestamps != sorted(parsed_timestamps):
                        raise ValidationError(
                            "Trajectory timestamps must be in chronological order",
                            field="trajectory",
                            code="invalid_timestamps"
                        )
                except (ValueError, TypeError):
                    raise ValidationError(
                        "Invalid timestamp format in trajectory",
                        field="trajectory",
                        code="invalid_timestamp"
                    )
    
    def _validate_knowledge_fields(self, request: UniversalKnowledgeWriteRequest) -> None:
        """Validate knowledge-specific fields."""
        # Validate source
        if request.source not in [source.value for source in SourceType]:
            raise ValidationError(
                f"Invalid knowledge source: {request.source}",
                field="source",
                code="invalid_source"
            )
        
        # Validate confidence
        if not (0.0 <= request.confidence <= 1.0):
            raise ValidationError(
                "Confidence must be between 0.0 and 1.0",
                field="confidence",
                code="invalid_range"
            )
        
        # Validate temporal scope
        valid_scopes = ["always", "recent", "deprecated"]
        if request.temporal_scope not in valid_scopes:
            raise ValidationError(
                f"Invalid temporal scope: {request.temporal_scope}",
                field="temporal_scope",
                code="invalid_scope"
            )
    
    def _validate_fact_fields(self, request: UniversalFactWriteRequest) -> None:
        """Validate fact-specific fields."""
        # Validate fact type
        valid_types = ["personal", "location", "preference", "behavior", "relationship"]
        if request.fact_type not in valid_types:
            raise ValidationError(
                f"Invalid fact type: {request.fact_type}",
                field="fact_type",
                code="invalid_type"
            )
        
        # Validate source
        if request.source not in [source.value for source in SourceType]:
            raise ValidationError(
                f"Invalid fact source: {request.source}",
                field="source",
                code="invalid_source"
            )
        
        # Validate confidence
        if not (0.0 <= request.confidence <= 1.0):
            raise ValidationError(
                "Confidence must be between 0.0 and 1.0",
                field="confidence",
                code="invalid_range"
            )
    
    def _validate_patch_operation(self, update_data: Dict[str, Any]) -> None:
        """Validate JSON Patch operation."""
        # Basic JSON Patch validation
        if not isinstance(update_data, dict):
            raise ValidationError(
                "Patch data must be a dictionary",
                field="update_data",
                code="invalid_patch"
            )
    
    def _validate_preconditions(self, preconditions: Any) -> None:
        """Validate optimistic locking preconditions."""
        if not isinstance(preconditions, dict):
            raise ValidationError(
                "Preconditions must be a dictionary",
                field="preconditions",
                code="invalid_preconditions"
            )
        
        # Validate version
        if "version" in preconditions:
            version = preconditions["version"]
            if not isinstance(version, int) or version < 1:
                raise ValidationError(
                    "Precondition version must be a positive integer",
                    field="preconditions.version",
                    code="invalid_version"
                )
        
        # Validate content hash
        if "content_hash" in preconditions:
            content_hash = preconditions["content_hash"]
            if not isinstance(content_hash, str) or len(content_hash) != 64:
                raise ValidationError(
                    "Precondition content hash must be a 64-character string",
                    field="preconditions.content_hash",
                    code="invalid_hash"
                )


# Global validator instance
_validator: Optional[RequestValidator] = None


def get_validator() -> RequestValidator:
    """Get global validator instance."""
    global _validator
    
    if _validator is None:
        _validator = RequestValidator()
    
    return _validator


# Convenience functions

def validate_entity_request(request: Union[UniversalEntityWriteRequest, UniversalEntityUpdateRequest]) -> None:
    """Validate entity request."""
    validator = get_validator()
    
    if isinstance(request, UniversalEntityWriteRequest):
        validator.validate_entity_write_request(request)
    elif isinstance(request, UniversalEntityUpdateRequest):
        validator.validate_entity_update_request(request)
    else:
        raise ValidationError("Invalid request type")


def validate_episode_request(request: UniversalEpisodeWriteRequest) -> None:
    """Validate episode request."""
    validator = get_validator()
    validator.validate_episode_write_request(request)


def validate_knowledge_request(request: UniversalKnowledgeWriteRequest) -> None:
    """Validate knowledge request."""
    validator = get_validator()
    validator.validate_knowledge_write_request(request)


def validate_fact_request(request: UniversalFactWriteRequest) -> None:
    """Validate fact request."""
    validator = get_validator()
    validator.validate_fact_write_request(request)
