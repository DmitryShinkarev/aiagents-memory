"""Application settings and configuration."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_session_ttl: int = 3600
    redis_max_connections: int = 50
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "agent_memory"
    mongodb_max_pool_size: int = 100
    
    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_timeout: int = 30
    
    # PostgreSQL Configuration
    postgres_url: str = "postgresql://postgres:password@localhost:5432/memory_logs"
    postgres_max_pool_size: int = 20
    
    # Memory Limits
    working_memory_max_messages: int = 50
    working_memory_context_window: int = 8192
    working_memory_compression_threshold: int = 40
    
    episodic_memory_ttl_days: int = 90
    episodic_memory_max_per_agent: int = 10000
    
    semantic_memory_ttl_days: int = 365
    semantic_memory_vector_size: int = 1536
    
    # Embedding Service
    embedding_provider: str = "openai"
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 100
    embedding_model_path: Optional[str] = None
    
    # Monitoring
    prometheus_port: int = 8000
    enable_metrics: bool = True
    log_level: str = "INFO"
    
    # Performance
    query_cache_ttl: int = 300
    enable_query_cache: bool = True
    max_context_tokens: int = 4096
    
    # Features
    enable_cross_agent_memory: bool = True
    enable_self_reflection: bool = True
    enable_human_feedback: bool = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()





