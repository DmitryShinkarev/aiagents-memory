# Getting Started with Memory-Agents

## Installation

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for infrastructure)
- Git

### Quick Install

```bash
# Clone repository
git clone https://github.com/yourusername/memory-agents.git
cd memory-agents

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Infrastructure Setup

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f
```

This starts:
- Redis (port 6379)
- MongoDB (port 27017)
- Qdrant (ports 6333, 6334)
- PostgreSQL (port 5432)

### Manual Setup

If you prefer manual setup, install and configure:

1. **Redis 7.x**
   ```bash
   redis-server --port 6379
   ```

2. **MongoDB 7.x**
   ```bash
   mongod --port 27017
   ```

3. **Qdrant**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

4. **PostgreSQL 16.x**
   ```bash
   psql -U postgres -c "CREATE DATABASE memory_logs;"
   ```

## Configuration

### Environment Variables

Copy the example configuration:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Redis
REDIS_URL=redis://localhost:6379

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=agent_memory

# Qdrant
QDRANT_URL=http://localhost:6333

# PostgreSQL
POSTGRES_URL=postgresql://postgres:password@localhost:5432/memory_logs

# Embedding Service (if using OpenAI)
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
```

## Basic Usage

### Initialize the System

```python
from memory_agents import initialize_memory_system

# Initialize with default configuration
orchestrator = await initialize_memory_system(agent_id="my_agent")
```

### Working Memory Example

```python
# Add messages to active session
session_id = "session_001"

await orchestrator.working.add_message(
    session_id=session_id,
    role="user",
    content="What is multi-agent systems?"
)

await orchestrator.working.add_message(
    session_id=session_id,
    role="assistant",
    content="Multi-agent systems are..."
)

# Retrieve conversation context
context = await orchestrator.working.get_context(session_id)
print(f"Messages: {len(context)}")

# Set temporary variables
await orchestrator.working.set_temp_variable(
    session_id, "current_topic", "multi-agent-systems"
)
```

### Context Retrieval

```python
# Get comprehensive context from all memory types
context = await orchestrator.retrieve_context(
    agent_id="my_agent",
    session_id="session_001",
    query="What did we discuss about agents?",
    max_tokens=4096
)

print(f"Working memory: {len(context['working'])} items")
print(f"Episodic memory: {len(context['episodic'])} items")
print(f"Semantic memory: {len(context['semantic'])} items")
print(f"Total tokens: {context['total_tokens']}")
```

### Session Consolidation

```python
# Move session from working memory to long-term memory
await orchestrator.consolidate_session(
    agent_id="my_agent",
    session_id="session_001"
)

print("Session consolidated to long-term memory!")
```

### Adding Knowledge

```python
from memory_agents import SemanticKnowledge, KnowledgeType

# Create knowledge item
knowledge = SemanticKnowledge(
    content="Redis is an in-memory data store",
    knowledge_type=KnowledgeType.FACT,
    source="documentation",
    namespace="technical",
    tags=["redis", "database"],
    confidence=1.0
)

# Add to semantic memory (requires embedding service)
# embedding = await embedding_service.embed(knowledge.content)
# await orchestrator.semantic.add_knowledge(knowledge, embedding)
```

### Adding Procedures

```python
from memory_agents import Procedure, ProcedureType, ProcedureParameter

# Create procedure template
procedure = Procedure(
    name="greeting_template",
    procedure_type=ProcedureType.PROMPT_TEMPLATE,
    description="Friendly greeting template",
    content="Hello {name}! Welcome to {service}.",
    parameters=[
        ProcedureParameter(name="name", type="string", required=True),
        ProcedureParameter(name="service", type="string", required=True)
    ],
    tags=["greeting", "template"]
)

# Save procedure
proc_id = await orchestrator.procedural.save_procedure(procedure)
print(f"Saved procedure: {proc_id}")
```

## Running Examples

```bash
# Run basic usage example
python examples/basic_usage.py

# Or using Make
make run-example
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=memory_agents --cov-report=html

# Or using Make
make test
```

## Monitoring

### Prometheus Metrics

Start metrics server in your application:

```python
from metrics import start_metrics_server

# Start on port 8000
start_metrics_server(8000)
```

Access metrics at: `http://localhost:8000/metrics`

### Grafana Dashboard

If you started monitoring services:

```bash
docker-compose --profile monitoring up -d
```

Access Grafana at: `http://localhost:3000` (admin/admin)

## Next Steps

- Read [Architecture Documentation](./ARCHITECTURE.md)
- Explore [API Reference](./API.md)
- Check out [Advanced Examples](../examples/)
- Review [Performance Tuning](./PERFORMANCE.md)

## Troubleshooting

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

### MongoDB Connection Issues

```bash
# Check MongoDB is running
mongosh --eval "db.adminCommand('ping')"
```

### Qdrant Connection Issues

```bash
# Check Qdrant health
curl http://localhost:6333/health
```

### PostgreSQL Connection Issues

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"
```

## Getting Help

- GitHub Issues: Report bugs or request features
- Documentation: Check docs/ directory
- Examples: See examples/ directory

## License

MIT License - see LICENSE file for details





