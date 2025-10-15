"""Prometheus metrics for memory operations."""

from prometheus_client import Counter, Histogram, Gauge, start_http_server
from functools import wraps
from typing import Callable
import time


# Define metrics
memory_operations = Counter(
    'memory_operations_total',
    'Total memory operations',
    ['type', 'operation', 'status']
)

memory_latency = Histogram(
    'memory_operation_latency_seconds',
    'Memory operation latency in seconds',
    ['type', 'operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

memory_size = Gauge(
    'memory_size_bytes',
    'Memory size in bytes',
    ['type', 'agent_id']
)

memory_item_count = Gauge(
    'memory_item_count',
    'Number of items in memory',
    ['type', 'agent_id']
)

embedding_operations = Counter(
    'embedding_operations_total',
    'Total embedding operations',
    ['status']
)

cache_hits = Counter(
    'cache_hits_total',
    'Cache hit/miss count',
    ['result']  # hit or miss
)


def monitor_async(memory_type: str, operation: str):
    """
    Decorator to monitor async memory operations.
    
    Args:
        memory_type: Type of memory (working, episodic, etc.)
        operation: Operation name
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                # Record metrics
                latency = time.time() - start_time
                memory_operations.labels(
                    type=memory_type,
                    operation=operation,
                    status=status
                ).inc()
                
                memory_latency.labels(
                    type=memory_type,
                    operation=operation
                ).observe(latency)
        
        return wrapper
    return decorator


def start_metrics_server(port: int = 8000):
    """
    Start Prometheus metrics HTTP server.
    
    Args:
        port: Port to listen on
    """
    start_http_server(port)
    print(f"Metrics server started on port {port}")


