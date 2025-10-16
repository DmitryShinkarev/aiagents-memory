"""
Business Logic Layer

This module contains business logic, adapters, validation, and idempotency
mechanisms that sit between the API layer and domain layer.
"""

from .idempotency import IdempotencyGuard, idempotent_operation
from .validation import RequestValidator, ValidationError
from .adapters import EntityContractAdapter, EpisodeContractAdapter

__all__ = [
    "IdempotencyGuard",
    "idempotent_operation",
    "RequestValidator",
    "ValidationError",
    "EntityContractAdapter",
    "EpisodeContractAdapter",
]
