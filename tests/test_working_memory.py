"""Tests for working memory (Redis)."""

import pytest
from storage.redis.working_store import RedisWorkingMemory


@pytest.mark.asyncio
async def test_add_and_get_message(redis_client, test_agent_id, test_session_id):
    """Test adding and retrieving messages."""
    working_memory = RedisWorkingMemory(redis_client, test_agent_id)
    
    # Add message
    msg_id = await working_memory.add_message(
        session_id=test_session_id,
        role="user",
        content="Hello, world!"
    )
    
    assert msg_id is not None
    
    # Get context
    context = await working_memory.get_context(test_session_id)
    
    assert len(context) == 1
    assert context[0]["role"] == "user"
    assert context[0]["content"] == "Hello, world!"


@pytest.mark.asyncio
async def test_temp_variables(redis_client, test_agent_id, test_session_id):
    """Test temporary variables."""
    working_memory = RedisWorkingMemory(redis_client, test_agent_id)
    
    # Set variable
    await working_memory.set_temp_variable(
        test_session_id, "test_var", {"key": "value"}
    )
    
    # Get variable
    value = await working_memory.get_temp_variable(test_session_id, "test_var")
    
    assert value == {"key": "value"}
    
    # Delete variable
    await working_memory.delete_temp_variable(test_session_id, "test_var")
    
    # Verify deletion
    value = await working_memory.get_temp_variable(test_session_id, "test_var")
    assert value is None


@pytest.mark.asyncio
async def test_clear_session(redis_client, test_agent_id, test_session_id):
    """Test clearing session."""
    working_memory = RedisWorkingMemory(redis_client, test_agent_id)
    
    # Add some data
    await working_memory.add_message(
        test_session_id, "user", "Test message"
    )
    await working_memory.set_temp_variable(
        test_session_id, "test_var", "test_value"
    )
    
    # Clear session
    await working_memory.clear_session(test_session_id)
    
    # Verify cleared
    context = await working_memory.get_context(test_session_id)
    assert len(context) == 0
    
    value = await working_memory.get_temp_variable(test_session_id, "test_var")
    assert value is None


