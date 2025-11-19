# Deployment Guide

This guide covers deployment options for the Memory-Agents system in different environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Redis**: 7.0 or higher
- **MongoDB**: 7.0 or higher
- **Qdrant**: 1.7.0 or higher
- **PostgreSQL**: 16.0 or higher

### Hardware Requirements

#### Minimum (Development)
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **Network**: 100 Mbps

#### Recommended (Production)
- **CPU**: 8 cores
- **RAM**: 32 GB
- **Storage**: 500 GB SSD
- **Network**: 1 Gbps

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/your-org/memory-agents.git
cd memory-agents
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Dependencies

#### Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

This will start:
- Redis on port 6379
- MongoDB on port 27017
- Qdrant on port 6333
- PostgreSQL on port 5432

#### Manual Setup

**Redis:**
```bash
redis-server
```

**MongoDB:**
```bash
mongod --dbpath /path/to/data
```

**Qdrant:**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**PostgreSQL:**
```bash
sudo -u postgres createdb memory_logs
```

### 5. Initialize Databases

```bash
# MongoDB initialization
mongo < scripts/mongo-init.js

# PostgreSQL initialization
psql -d memory_logs -f scripts/postgres-init.sql
```

### 6. Configure Environment

Create `.env` file:

```bash
# Redis
REDIS_URL=redis://localhost:6379
REDIS_SESSION_TTL=3600

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=agent_memory

# Qdrant
QDRANT_URL=http://localhost:6333

# PostgreSQL
POSTGRES_URL=postgresql://postgres:password@localhost:5432/memory_logs

# Embeddings
OPENAI_API_KEY=your_openai_key
EMBEDDING_MODEL=text-embedding-3-small

# Monitoring
PROMETHEUS_PORT=8000
LOG_LEVEL=INFO
```

### 7. Run Tests

```bash
pytest
```

### 8. Run Example

```bash
python examples/memory_usage_example.py
```

## Docker Deployment

### 1. Build Docker Image

```bash
docker build -t memory-agents:latest .
```

### 2. Run with Docker Compose

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Health Check

```bash
curl http://localhost:8000/health
```

## Production Deployment

### Kubernetes Deployment

#### 1. Create Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: memory-agents
```

#### 2. Deploy Redis

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: memory-agents
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: memory-agents
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

#### 3. Deploy MongoDB

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: memory-agents
spec:
  serviceName: mongodb
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: "admin"
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mongodb-secret
              key: password
        volumeMounts:
        - name: mongodb-storage
          mountPath: /data/db
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: mongodb-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb-service
  namespace: memory-agents
spec:
  selector:
    app: mongodb
  ports:
  - port: 27017
    targetPort: 27017
```

#### 4. Deploy Qdrant

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  namespace: memory-agents
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:latest
        ports:
        - containerPort: 6333
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant-service
  namespace: memory-agents
spec:
  selector:
    app: qdrant
  ports:
  - port: 6333
    targetPort: 6333
```

#### 5. Deploy PostgreSQL

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: memory-agents
spec:
  serviceName: postgresql
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:16
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "memory_logs"
        - name: POSTGRES_USER
          value: "postgres"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgresql-secret
              key: password
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql-service
  namespace: memory-agents
spec:
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
```

#### 6. Deploy Memory-Agents Application

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: memory-agents
  namespace: memory-agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: memory-agents
  template:
    metadata:
      labels:
        app: memory-agents
    spec:
      containers:
      - name: memory-agents
        image: memory-agents:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: MONGODB_URL
          value: "mongodb://mongodb-service:27017"
        - name: QDRANT_URL
          value: "http://qdrant-service:6333"
        - name: POSTGRES_URL
          value: "postgresql://postgresql-service:5432/memory_logs"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: memory-agents-service
  namespace: memory-agents
spec:
  selector:
    app: memory-agents
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### Secrets

Create secrets for sensitive data:

```bash
# MongoDB secret
kubectl create secret generic mongodb-secret \
  --from-literal=password=your-mongodb-password \
  -n memory-agents

# PostgreSQL secret
kubectl create secret generic postgresql-secret \
  --from-literal=password=your-postgresql-password \
  -n memory-agents

# OpenAI secret
kubectl create secret generic openai-secret \
  --from-literal=api-key=your-openai-api-key \
  -n memory-agents
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` | Yes |
| `REDIS_SESSION_TTL` | Session TTL in seconds | `3600` | No |
| `MONGODB_URL` | MongoDB connection URL | `mongodb://localhost:27017` | Yes |
| `MONGODB_DATABASE` | MongoDB database name | `agent_memory` | No |
| `QDRANT_URL` | Qdrant server URL | `http://localhost:6333` | Yes |
| `QDRANT_API_KEY` | Qdrant API key | None | No |
| `POSTGRES_URL` | PostgreSQL connection URL | `postgresql://postgres:password@localhost:5432/memory_logs` | Yes |
| `OPENAI_API_KEY` | OpenAI API key | None | Yes |
| `EMBEDDING_MODEL` | Embedding model name | `text-embedding-3-small` | No |
| `PROMETHEUS_PORT` | Prometheus metrics port | `8000` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Production Configuration

For production deployment, consider:

1. **Connection Pooling**: Increase connection pool sizes
2. **Timeouts**: Set appropriate timeouts for external services
3. **Retries**: Configure retry policies
4. **Circuit Breakers**: Implement circuit breakers for resilience
5. **Rate Limiting**: Add rate limiting for API endpoints

## Monitoring

### Health Checks

The system provides health check endpoints:

- `/health` - Overall system health
- `/health/working` - Working memory health
- `/health/episodic` - Episodic memory health
- `/health/semantic` - Semantic memory health
- `/health/procedural` - Procedural memory health
- `/health/facts` - Facts service health

### Metrics

Prometheus metrics are available at `/metrics`:

- `memory_operations_total` - Total memory operations
- `memory_operation_duration_seconds` - Operation duration
- `active_sessions_count` - Active sessions
- `episodes_count` - Total episodes
- `knowledge_items_count` - Total knowledge items
- `cache_hit_rate` - Cache hit rate

### Logging

Structured logging with the following fields:

- `timestamp` - ISO timestamp
- `level` - Log level (DEBUG, INFO, WARNING, ERROR)
- `service` - Service name
- `operation` - Operation name
- `agent_id` - Agent identifier
- `user_id` - User identifier (if applicable)
- `request_id` - Request identifier
- `execution_time_ms` - Execution time
- `status` - Operation status

### Grafana Dashboard

Create a Grafana dashboard with the following panels:

1. **System Overview**
   - Overall health status
   - Active sessions
   - Memory usage

2. **Performance Metrics**
   - Operation duration
   - Throughput
   - Error rates

3. **Memory Statistics**
   - Episodes count by scope
   - Knowledge items by source
   - Facts count by type

4. **Database Metrics**
   - Connection pool usage
   - Query performance
   - Storage usage

## Troubleshooting

### Common Issues

#### 1. Connection Issues

**Problem**: Cannot connect to Redis/MongoDB/Qdrant/PostgreSQL

**Solution**:
- Check if services are running
- Verify connection URLs
- Check network connectivity
- Verify credentials

#### 2. Memory Issues

**Problem**: High memory usage

**Solution**:
- Check for memory leaks
- Increase connection pool sizes
- Optimize queries
- Add memory limits

#### 3. Performance Issues

**Problem**: Slow operations

**Solution**:
- Check database indexes
- Optimize queries
- Increase connection pools
- Add caching

#### 4. Idempotency Issues

**Problem**: Duplicate operations

**Solution**:
- Check idempotency key generation
- Verify Redis/PostgreSQL connectivity
- Check TTL settings

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

### Database Maintenance

#### MongoDB

```bash
# Check database status
mongo --eval "db.stats()"

# Check collections
mongo --eval "db.getCollectionNames()"

# Check indexes
mongo --eval "db.episodes.getIndexes()"
```

#### PostgreSQL

```bash
# Check database size
psql -c "SELECT pg_size_pretty(pg_database_size('memory_logs'));"

# Check table sizes
psql -c "SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size FROM pg_tables WHERE schemaname = 'public';"

# Check slow queries
psql -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

#### Redis

```bash
# Check memory usage
redis-cli info memory

# Check keys
redis-cli keys "*"

# Check TTL
redis-cli ttl "session:session_001"
```

### Backup and Recovery

#### MongoDB Backup

```bash
# Create backup
mongodump --db agent_memory --out /backup/mongodb

# Restore backup
mongorestore --db agent_memory /backup/mongodb/agent_memory
```

#### PostgreSQL Backup

```bash
# Create backup
pg_dump memory_logs > /backup/postgresql/memory_logs.sql

# Restore backup
psql memory_logs < /backup/postgresql/memory_logs.sql
```

#### Redis Backup

```bash
# Create backup
redis-cli BGSAVE

# Copy backup file
cp /var/lib/redis/dump.rdb /backup/redis/
```

### Scaling

#### Horizontal Scaling

1. **Application Layer**: Deploy multiple instances behind a load balancer
2. **Database Layer**: Use read replicas for MongoDB and PostgreSQL
3. **Cache Layer**: Use Redis Cluster for high availability

#### Vertical Scaling

1. **Increase Resources**: Add more CPU and memory
2. **Optimize Configuration**: Tune connection pools and timeouts
3. **Add Indexes**: Optimize database queries

### Security

#### Network Security

1. **Firewall**: Restrict access to database ports
2. **VPN**: Use VPN for remote access
3. **SSL/TLS**: Enable encryption for all connections

#### Authentication

1. **Database Users**: Create dedicated users with minimal privileges
2. **API Keys**: Use strong API keys for external services
3. **Secrets Management**: Use Kubernetes secrets or external secret management

#### Data Protection

1. **Encryption**: Enable encryption at rest and in transit
2. **Backup Encryption**: Encrypt backup files
3. **Access Control**: Implement proper access controls
4. **Audit Logging**: Enable audit logging for all operations




