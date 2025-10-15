"""Pytest configuration and fixtures."""

import pytest
import asyncio
from redis.asyncio import Redis
from motor.motor_asyncio import AsyncIOMotorClient


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def redis_client():
    """Redis client fixture for tests."""
    client = Redis.from_url("redis://localhost:6379", decode_responses=False)
    yield client
    await client.flushdb()  # Clean up after tests
    await client.close()


@pytest.fixture
async def mongo_client():
    """MongoDB client fixture for tests."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    # Clean up test database
    await client.drop_database("test_agent_memory")
    client.close()


@pytest.fixture
def test_agent_id():
    """Test agent ID."""
    return "test_agent_001"


@pytest.fixture
def test_session_id():
    """Test session ID."""
    return "test_session_001"


