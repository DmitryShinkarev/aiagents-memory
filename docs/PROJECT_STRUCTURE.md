# Project Structure

This document describes the structure of the Memory-Agents project and explains the purpose of each component.

## Directory Structure

```
memory-agents/
├── api/                           # API Layer - Stable Contracts
│   ├── __init__.py
│   ├── contracts/                 # Pydantic DTOs for API contracts
│   │   ├── __init__.py
│   │   ├── common.py             # Common types and enums
│   │   ├── entity.py             # Entity operation contracts
│   │   ├── episode.py            # Episode operation contracts
│   │   ├── facts.py              # Facts operation contracts
│   │   └── knowledge.py          # Knowledge operation contracts
│   └── versioning.py             # API version management
├── business/                      # Business Logic Layer
│   ├── __init__.py
│   ├── idempotency.py            # Idempotency mechanisms
│   └── validation.py             # Request validation
├── domain/                        # Domain Layer - Core Services
│   ├── __init__.py
│   └── memory/                   # Memory type services
│       ├── __init__.py
│       ├── episodic.py           # Episodic memory service
│       ├── facts.py              # User facts service
│       ├── procedural.py         # Procedural memory service
│       ├── semantic.py           # Semantic memory service
│       └── working.py            # Working memory service
├── services/                      # Services Layer - High-level Services
│   ├── __init__.py
│   └── memory_facade.py          # Unified memory interface
├── storage/                       # Storage Layer - Database Clients
│   ├── __init__.py
│   └── clients/                  # Database client implementations
│       ├── __init__.py
│       ├── mongo_client.py       # MongoDB client
│       ├── postgres_client.py    # PostgreSQL client
│       ├── qdrant_client.py      # Qdrant client
│       └── redis_client.py       # Redis client
├── config/                        # Configuration
│   ├── __init__.py
│   ├── prometheus.yml            # Prometheus configuration
│   └── settings.py               # Application settings
├── examples/                      # Usage Examples
│   ├── __init__.py
│   └── memory_usage_example.py   # Basic usage example
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md           # System architecture
│   ├── API_REFERENCE.md          # API documentation
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── EXAMPLES.md               # Usage examples
│   ├── GETTING_STARTED.md        # Getting started guide
│   ├── PROJECT_STRUCTURE.md      # This file
│   └── QUICKSTART.md             # Quick start guide
├── scripts/                       # Database Initialization
│   ├── mongo-init.js             # MongoDB initialization
│   └── postgres-init.sql         # PostgreSQL initialization
├── __init__.py                    # Main package entry point
├── docker-compose.yml             # Docker Compose configuration
├── LICENSE                        # MIT License
├── Makefile                       # Build and development commands
├── README.md                      # Main README
├── README_EN.md                   # English README
├── requirements.txt               # Python dependencies
└── setup.py                       # Package setup
```

## Layer Descriptions

### API Layer (`api/`)

The API layer provides stable, versioned contracts for all memory operations.

#### `api/contracts/`
- **`common.py`**: Common types, enums, and base classes used across all contracts
- **`entity.py`**: Contracts for dynamic entity operations (create, read, update, delete)
- **`episode.py`**: Contracts for episodic memory operations
- **`facts.py`**: Contracts for user facts operations
- **`knowledge.py`**: Contracts for semantic knowledge operations

#### `api/versioning.py`
- API version management and backward compatibility

### Business Logic Layer (`business/`)

The business logic layer implements core business rules and cross-cutting concerns.

#### `business/idempotency.py`
- **`IdempotencyGuard`**: Ensures operations are executed only once
- **`@idempotent_operation`**: Decorator for idempotent operations
- Collision detection and response caching

#### `business/validation.py`
- **`RequestValidator`**: Validates incoming requests against business rules
- Schema validation and access control validation

### Domain Layer (`domain/`)

The domain layer contains the core memory services that implement business logic.

#### `domain/memory/`
- **`working.py`**: Working memory service (Redis-based)
- **`episodic.py`**: Episodic memory service (MongoDB + Qdrant)
- **`semantic.py`**: Semantic memory service (MongoDB + Qdrant)
- **`procedural.py`**: Procedural memory service (MongoDB)
- **`facts.py`**: User facts service (MongoDB)

### Services Layer (`services/`)

The services layer provides high-level services that orchestrate domain services.

#### `services/memory_facade.py`
- **`MemoryFacade`**: Unified interface for all memory operations
- **`get_memory_facade()`**: Factory function for memory facade

### Storage Layer (`storage/`)

The storage layer provides database clients and connection management.

#### `storage/clients/`
- **`redis_client.py`**: Redis client with connection pooling
- **`mongo_client.py`**: MongoDB client with connection pooling
- **`qdrant_client.py`**: Qdrant client for vector operations
- **`postgres_client.py`**: PostgreSQL client for audit logging

### Configuration (`config/`)

Configuration management and application settings.

#### `config/settings.py`
- **`Settings`**: Pydantic settings for environment variables
- **`get_settings()`**: Factory function for settings

### Examples (`examples/`)

Usage examples and demonstrations.

#### `examples/memory_usage_example.py`
- Basic usage example showing all memory types
- Multi-agent coordination example
- Health monitoring example

### Documentation (`docs/`)

Comprehensive documentation for the system.

- **`ARCHITECTURE.md`**: System architecture and design
- **`API_REFERENCE.md`**: Detailed API documentation
- **`DEPLOYMENT.md`**: Production deployment guide
- **`EXAMPLES.md`**: Comprehensive usage examples
- **`GETTING_STARTED.md`**: Getting started guide
- **`PROJECT_STRUCTURE.md`**: This file
- **`QUICKSTART.md`**: Quick start guide

### Scripts (`scripts/`)

Database initialization and setup scripts.

- **`mongo-init.js`**: MongoDB database and collection setup
- **`postgres-init.sql`**: PostgreSQL database and table setup

## Key Files

### `__init__.py` (Root)
Main package entry point that exposes the public API:

```python
# Core services
from .services.memory_facade import MemoryFacade, get_memory_facade
from .config.settings import Settings, get_settings

# API contracts
from .api.contracts.common import *
from .api.contracts.entity import *
from .api.contracts.episode import *
from .api.contracts.knowledge import *
from .api.contracts.facts import *

# Business logic
from .business.idempotency import IdempotencyGuard, idempotent_operation
from .business.validation import RequestValidator, ValidationError

# Domain services
from .domain.memory.working import WorkingMemoryService
from .domain.memory.episodic import EpisodicMemoryService
from .domain.memory.semantic import SemanticMemoryService
from .domain.memory.procedural import ProceduralMemoryService
from .domain.memory.facts import FactsService

# Storage clients
from .storage.clients.redis_client import RedisClient
from .storage.clients.mongo_client import MongoClient
from .storage.clients.qdrant_client import QdrantClient
from .storage.clients.postgres_client import PostgresClient
```

### `requirements.txt`
Python dependencies for the project:

```
# Core dependencies
redis>=5.0.0
motor>=3.3.0
pymongo>=4.6.0
qdrant-client>=1.7.0
asyncpg>=0.29.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
aiofiles>=23.2.0
asyncio-mqtt>=0.16.0
prometheus-client>=0.19.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
python-dotenv>=1.0.0
pyyaml>=6.0.1
click>=8.1.0
numpy>=1.24.0
sentence-transformers>=2.2.0

# Development dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.7.0
```

### `docker-compose.yml`
Docker Compose configuration for local development:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
  
  postgresql:
    image: postgres:16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: memory_logs
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
```

### `Makefile`
Build and development commands:

```makefile
.PHONY: install test lint format type-check clean

install:
	pip install -r requirements.txt

test:
	pytest

lint:
	ruff check .

format:
	black .

type-check:
	mypy .

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
```

## Design Patterns

### Layered Architecture
The project follows a layered architecture pattern:

1. **API Layer**: Stable contracts and versioning
2. **Business Logic Layer**: Cross-cutting concerns and business rules
3. **Domain Layer**: Core business logic and services
4. **Services Layer**: High-level orchestration
5. **Storage Layer**: Database clients and connection management

### Dependency Injection
Services are injected through factory functions:

```python
# Factory function for memory facade
def get_memory_facade() -> MemoryFacade:
    return MemoryFacade()

# Factory function for settings
def get_settings() -> Settings:
    return Settings()
```

### Repository Pattern
Storage clients implement the repository pattern:

```python
class MongoClient:
    async def insert_one(self, collection: str, document: dict) -> str:
        # Implementation
    
    async def find_one(self, collection: str, filter: dict) -> Optional[dict]:
        # Implementation
```

### Facade Pattern
The `MemoryFacade` provides a unified interface to all memory services:

```python
class MemoryFacade:
    def __init__(self):
        self.working = WorkingMemoryService()
        self.episodic = EpisodicMemoryService()
        self.semantic = SemanticMemoryService()
        self.procedural = ProceduralMemoryService()
        self.facts = FactsService()
```

## Development Workflow

### 1. Local Development
```bash
# Clone repository
git clone https://github.com/your-org/memory-agents.git
cd memory-agents

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start dependencies
docker-compose up -d

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy .
```

### 2. Adding New Features
1. Create feature branch
2. Implement changes following the layered architecture
3. Add tests
4. Update documentation
5. Submit pull request

### 3. Code Organization
- Follow the layered architecture
- Use dependency injection
- Implement proper error handling
- Add comprehensive logging
- Write tests for all new code

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Test error conditions

### Integration Tests
- Test component interactions
- Test database operations
- Test API endpoints

### End-to-End Tests
- Test complete workflows
- Test multi-agent scenarios
- Test performance characteristics

## Documentation Strategy

### Code Documentation
- Docstrings for all public methods
- Type hints for all parameters and return values
- Inline comments for complex logic

### API Documentation
- Comprehensive API reference
- Usage examples
- Error handling documentation

### Architecture Documentation
- System design documents
- Deployment guides
- Performance characteristics

## Security Considerations

### Data Protection
- Encryption in transit and at rest
- Access control and authentication
- Audit logging for all operations

### Privacy
- User data isolation
- TTL for automatic cleanup
- Consent management

### Compliance
- GDPR compliance
- Data retention policies
- Right to be forgotten

## Performance Considerations

### Latency
- Target latencies for each memory type
- Connection pooling
- Query optimization

### Throughput
- Concurrent operation support
- Batch operations
- Caching strategies

### Scalability
- Horizontal scaling support
- Database sharding
- Load balancing

## Monitoring and Observability

### Health Checks
- Service availability monitoring
- Database connectivity checks
- Performance metrics

### Logging
- Structured logging
- Request tracing
- Error tracking

### Metrics
- Prometheus metrics
- Custom business metrics
- Performance indicators


