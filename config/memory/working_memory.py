"""Working memory configuration."""

from dataclasses import dataclass
from ..settings import get_settings


@dataclass
class WorkingMemoryConfig:
    """Configuration for working memory (Redis)."""
    
    session_ttl: int = None
    max_messages: int = None
    context_window: int = None
    compression_threshold: int = None
    
    def __post_init__(self):
        """Load values from settings if not provided."""
        settings = get_settings()
        
        if self.session_ttl is None:
            self.session_ttl = settings.redis_session_ttl
        
        if self.max_messages is None:
            self.max_messages = settings.working_memory_max_messages
        
        if self.context_window is None:
            self.context_window = settings.working_memory_context_window
        
        if self.compression_threshold is None:
            self.compression_threshold = settings.working_memory_compression_threshold


