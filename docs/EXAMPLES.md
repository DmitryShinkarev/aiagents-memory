# Examples

This document provides comprehensive examples of using the Memory-Agents system for various use cases.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Multi-Agent Scenarios](#multi-agent-scenarios)
- [Memory Types](#memory-types)
- [Advanced Features](#advanced-features)
- [Integration Examples](#integration-examples)

## Basic Usage

### Simple Agent with Memory

```python
import asyncio
from memory_agents import get_memory_facade

async def simple_agent_example():
    """Basic example of an agent using memory."""
    memory = get_memory_facade()
    
    # Create an episode for this interaction
    await memory.create_episode(
        episode_id="ep_001",
        context={
            "agent_id": "support_agent_001",
            "user_id": "user_123",
            "session_id": "session_001"
        },
        scope="user_private",
        episode_type="interaction",
        title="Customer support interaction",
        trajectory=[{
            "step_id": "1",
            "timestamp": "2024-01-01T10:00:00Z",
            "role": "user",
            "action": "message",
            "content": "I need help with my billing"
        }],
        success=True,
        importance=0.8
    )
    
    # Store knowledge about the user
    await memory.create_knowledge(
        knowledge_id="kb_001",
        knowledge="User prefers email communication for billing issues",
        source="inferred",
        confidence=0.9,
        agent_id="support_agent_001"
    )
    
    # Get comprehensive context
    context = await memory.retrieve_comprehensive_context(
        agent_id="support_agent_001",
        user_id="user_123"
    )
    
    print(f"Retrieved context with {len(context.get('episodes', []))} episodes")
    return context

# Run the example
if __name__ == "__main__":
    asyncio.run(simple_agent_example())
```

### Working with User Facts

```python
async def user_facts_example():
    """Example of managing user facts."""
    memory = get_memory_facade()
    
    # Store user facts
    await memory.facts.store_fact(
        fact_id="fact_001",
        user_id="user_123",
        fact_type="personal",
        key="name",
        value="John Doe",
        confidence=1.0,
        source="user_stated"
    )
    
    await memory.facts.store_fact(
        fact_id="fact_002",
        user_id="user_123",
        fact_type="preference",
        key="communication_method",
        value="email",
        confidence=0.9,
        source="inferred"
    )
    
    # Get user profile
    profile = await memory.facts.get_user_profile("user_123")
    print(f"User profile: {profile}")
    
    # Query specific facts
    facts = await memory.facts.query_facts(
        user_id="user_123",
        filter_by_fact_type=["personal", "preference"]
    )
    print(f"Found {len(facts)} facts")

asyncio.run(user_facts_example())
```

## Multi-Agent Scenarios

### Agent Team Collaboration

```python
async def team_collaboration_example():
    """Example of multiple agents working together."""
    memory = get_memory_facade()
    
    # Agent 1: Analyzes the problem
    await memory.create_episode(
        episode_id="ep_analysis_001",
        context={
            "agent_id": "analyst_001",
            "user_id": "user_123",
            "team_id": "support_team_001"
        },
        scope="team_shared",
        episode_type="task_execution",
        title="Problem analysis",
        trajectory=[{
            "step_id": "1",
            "timestamp": "2024-01-01T10:00:00Z",
            "role": "analyst",
            "action": "analyze",
            "content": "Analyzed billing issue: duplicate charge on credit card"
        }],
        success=True,
        importance=0.9
    )
    
    # Agent 2: Resolves the issue
    await memory.create_episode(
        episode_id="ep_resolution_001",
        context={
            "agent_id": "resolver_001",
            "user_id": "user_123",
            "team_id": "support_team_001"
        },
        scope="team_shared",
        episode_type="task_execution",
        title="Issue resolution",
        trajectory=[{
            "step_id": "1",
            "timestamp": "2024-01-01T10:05:00Z",
            "role": "resolver",
            "action": "resolve",
            "content": "Processed refund for duplicate charge"
        }],
        success=True,
        importance=0.8
    )
    
    # Agent 3: Follows up with user
    await memory.create_episode(
        episode_id="ep_followup_001",
        context={
            "agent_id": "followup_001",
            "user_id": "user_123",
            "team_id": "support_team_001"
        },
        scope="user_private",
        episode_type="interaction",
        title="Follow-up communication",
        trajectory=[{
            "step_id": "1",
            "timestamp": "2024-01-01T10:10:00Z",
            "role": "followup",
            "action": "notify",
            "content": "Notified user about refund processing"
        }],
        success=True,
        importance=0.7
    )
    
    # Get team context
    team_context = await memory.retrieve_comprehensive_context(
        agent_id="followup_001",
        user_id="user_123"
    )
    
    print(f"Team context includes {len(team_context.get('episodes', []))} episodes")

asyncio.run(team_collaboration_example())
```

### Cross-Agent Knowledge Sharing

```python
async def knowledge_sharing_example():
    """Example of agents sharing knowledge."""
    memory = get_memory_facade()
    
    # Agent 1 discovers new knowledge
    await memory.create_knowledge(
        knowledge_id="kb_shared_001",
        knowledge="Premium users prefer phone support for urgent issues",
        source="consolidated",
        confidence=0.95,
        agent_id="analyst_001",
        access_scope="team_shared",
        allowed_teams=["support_team_001", "sales_team_001"]
    )
    
    # Agent 2 can access this knowledge
    knowledge_items = await memory.semantic_search(
        query_embedding=[0.1, 0.2, 0.3],  # Your embedding vector
        agent_id="resolver_001",
        limit=10
    )
    
    print(f"Found {len(knowledge_items)} knowledge items")
    
    # Agent 3 updates the knowledge
    await memory.create_knowledge(
        knowledge_id="kb_shared_002",
        knowledge="Premium users prefer phone support for urgent issues, but email for non-urgent",
        source="consolidated",
        confidence=0.98,
        agent_id="followup_001",
        access_scope="team_shared",
        allowed_teams=["support_team_001", "sales_team_001"]
    )

asyncio.run(knowledge_sharing_example())
```

## Memory Types

### Working Memory for Active Sessions

```python
async def working_memory_example():
    """Example of using working memory for active sessions."""
    memory = get_memory_facade()
    
    # Store session data
    await memory.working.store_session("session_001", {
        "current_message": "User needs help with billing",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "agent", "content": "Hi! How can I help you?"},
            {"role": "user", "content": "I have a billing question"}
        ],
        "temporary_variables": {
            "user_tier": "premium",
            "issue_type": "billing"
        },
        "current_step": "analyzing_issue"
    })
    
    # Get context for decision making
    context = await memory.working.get_context(
        agent_id="support_agent_001",
        session_id="session_001"
    )
    
    print(f"Session context: {context}")
    
    # Cache RAG results
    await memory.working.cache_retrieval(
        "billing_help_query_hash",
        {
            "relevant_episodes": ["ep_001", "ep_002"],
            "knowledge_items": ["kb_001", "kb_002"],
            "user_facts": ["fact_001"]
        },
        ttl=300
    )

asyncio.run(working_memory_example())
```

### Episodic Memory for Event Tracking

```python
async def episodic_memory_example():
    """Example of using episodic memory for event tracking."""
    memory = get_memory_facade()
    
    # Create a detailed episode
    await memory.create_episode(
        episode_id="ep_detailed_001",
        context={
            "agent_id": "support_agent_001",
            "user_id": "user_123",
            "session_id": "session_001"
        },
        scope="user_private",
        episode_type="interaction",
        title="Complex billing issue resolution",
        trajectory=[
            {
                "step_id": "1",
                "timestamp": "2024-01-01T10:00:00Z",
                "role": "user",
                "action": "message",
                "content": "I was charged twice for my subscription"
            },
            {
                "step_id": "2",
                "timestamp": "2024-01-01T10:01:00Z",
                "role": "agent",
                "action": "analyze",
                "content": "Analyzing billing records for user_123"
            },
            {
                "step_id": "3",
                "timestamp": "2024-01-01T10:02:00Z",
                "role": "agent",
                "action": "confirm",
                "content": "Confirmed duplicate charge on 2024-01-01"
            },
            {
                "step_id": "4",
                "timestamp": "2024-01-01T10:03:00Z",
                "role": "agent",
                "action": "resolve",
                "content": "Processed refund for duplicate charge"
            }
        ],
        outcome="Successfully processed refund for duplicate charge",
        success=True,
        importance=0.9,
        user_satisfaction=0.95,
        tags=["billing", "refund", "duplicate_charge"]
    )
    
    # Query episodes with filters
    episodes = await memory.query_episodes(
        filter_by_user_id="user_123",
        filter_by_tags=["billing"],
        min_importance=0.8,
        limit=10
    )
    
    print(f"Found {len(episodes)} relevant episodes")

asyncio.run(episodic_memory_example())
```

### Semantic Memory for Knowledge Management

```python
async def semantic_memory_example():
    """Example of using semantic memory for knowledge management."""
    memory = get_memory_facade()
    
    # Store various types of knowledge
    await memory.create_knowledge(
        knowledge_id="kb_policy_001",
        knowledge="Premium users get priority support and faster response times",
        source="system",
        confidence=1.0,
        agent_id="system",
        tags=["policy", "premium", "support"],
        temporal_scope="always"
    )
    
    await memory.create_knowledge(
        knowledge_id="kb_procedure_001",
        knowledge="To process a refund, verify the charge first, then use the billing system",
        source="consolidated",
        confidence=0.95,
        agent_id="support_agent_001",
        tags=["procedure", "refund", "billing"],
        supporting_evidence=["ep_001", "ep_002"]
    )
    
    await memory.create_knowledge(
        knowledge_id="kb_pattern_001",
        knowledge="Users often confuse subscription charges with one-time purchases",
        source="inferred",
        confidence=0.8,
        agent_id="analyst_001",
        tags=["pattern", "user_behavior", "billing"],
        temporal_scope="recent",
        half_life_days=90
    )
    
    # Perform semantic search
    knowledge_items = await memory.semantic_search(
        query_embedding=[0.1, 0.2, 0.3],  # Your embedding vector
        agent_id="support_agent_001",
        limit=5,
        include_temporal_decay=True
    )
    
    print(f"Found {len(knowledge_items)} knowledge items")

asyncio.run(semantic_memory_example())
```

### Procedural Memory for Skills and Code

```python
async def procedural_memory_example():
    """Example of using procedural memory for skills and code."""
    memory = get_memory_facade()
    
    # Store a procedure
    await memory.procedural.store_procedure(
        procedure_id="proc_001",
        name="resolve_billing_issue",
        description="Resolve billing issues for customers",
        code="""
def resolve_billing_issue(account_number, issue_type, amount=None):
    \"\"\"
    Resolve billing issues for customers.
    
    Args:
        account_number (str): Customer account number
        issue_type (str): Type of issue (refund, adjustment, etc.)
        amount (float, optional): Amount to refund/adjust
    
    Returns:
        dict: Resolution result
    \"\"\"
    # Verify account exists
    account = verify_account(account_number)
    if not account:
        return {"status": "error", "message": "Account not found"}
    
    # Process based on issue type
    if issue_type == "refund":
        result = process_refund(account_number, amount)
    elif issue_type == "adjustment":
        result = process_adjustment(account_number, amount)
    else:
        return {"status": "error", "message": "Unknown issue type"}
    
    # Log the resolution
    log_resolution(account_number, issue_type, result)
    
    return {"status": "success", "result": result}
        """,
        language="python",
        parameters_schema={
            "type": "object",
            "properties": {
                "account_number": {"type": "string"},
                "issue_type": {"type": "string", "enum": ["refund", "adjustment"]},
                "amount": {"type": "number", "minimum": 0}
            },
            "required": ["account_number", "issue_type"]
        },
        return_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "result": {"type": "object"}
            }
        },
        tags=["billing", "resolution", "automation"]
    )
    
    # Execute the procedure
    result = await memory.procedural.execute_procedure(
        name="resolve_billing_issue",
        parameters={
            "account_number": "12345",
            "issue_type": "refund",
            "amount": 99.99
        }
    )
    
    print(f"Procedure result: {result}")

asyncio.run(procedural_memory_example())
```

## Advanced Features

### Idempotent Operations

```python
async def idempotent_operations_example():
    """Example of using idempotent operations."""
    memory = get_memory_facade()
    
    # Create episode with idempotency key
    idempotency_key = "create_episode_001"
    
    # First call - creates the episode
    result1 = await memory.create_episode(
        episode_id="ep_001",
        context={
            "agent_id": "support_agent_001",
            "user_id": "user_123"
        },
        scope="user_private",
        episode_type="interaction",
        title="Test episode",
        trajectory=[{
            "step_id": "1",
            "timestamp": "2024-01-01T10:00:00Z",
            "role": "user",
            "action": "message",
            "content": "Test message"
        }],
        success=True,
        importance=0.5,
        idempotency_key=idempotency_key
    )
    
    # Second call with same idempotency key - returns cached result
    result2 = await memory.create_episode(
        episode_id="ep_001",
        context={
            "agent_id": "support_agent_001",
            "user_id": "user_123"
        },
        scope="user_private",
        episode_type="interaction",
        title="Test episode",
        trajectory=[{
            "step_id": "1",
            "timestamp": "2024-01-01T10:00:00Z",
            "role": "user",
            "action": "message",
            "content": "Test message"
        }],
        success=True,
        importance=0.5,
        idempotency_key=idempotency_key
    )
    
    # Both calls return the same result
    print(f"Result 1: {result1}")
    print(f"Result 2: {result2}")
    print(f"Results are equal: {result1 == result2}")

asyncio.run(idempotent_operations_example())
```

### Temporal Decay in Semantic Memory

```python
async def temporal_decay_example():
    """Example of temporal decay in semantic memory."""
    memory = get_memory_facade()
    
    # Store knowledge with temporal decay
    await memory.create_knowledge(
        knowledge_id="kb_temporal_001",
        knowledge="Current promotion: 20% off for new users",
        source="system",
        confidence=1.0,
        agent_id="marketing_agent_001",
        tags=["promotion", "marketing"],
        temporal_scope="recent",
        half_life_days=30  # Knowledge becomes less relevant over time
    )
    
    # Store knowledge without temporal decay
    await memory.create_knowledge(
        knowledge_id="kb_permanent_001",
        knowledge="Premium users get priority support",
        source="system",
        confidence=1.0,
        agent_id="system",
        tags=["policy", "premium"],
        temporal_scope="always"  # Knowledge is always relevant
    )
    
    # Search with temporal decay
    knowledge_items = await memory.semantic_search(
        query_embedding=[0.1, 0.2, 0.3],  # Your embedding vector
        agent_id="support_agent_001",
        limit=10,
        include_temporal_decay=True
    )
    
    print(f"Found {len(knowledge_items)} knowledge items with temporal decay applied")

asyncio.run(temporal_decay_example())
```

### Multi-Agent Coordination

```python
async def multi_agent_coordination_example():
    """Example of multi-agent coordination."""
    memory = get_memory_facade()
    
    # Agent 1 publishes a task
    await memory.working.publish_event(
        channel="task:analysis",
        message={
            "task_id": "task_001",
            "type": "analyze_billing_issue",
            "data": {
                "user_id": "user_123",
                "issue_description": "Duplicate charge"
            },
            "assigned_agents": ["analyst_001", "resolver_001"]
        }
    )
    
    # Agent 2 subscribes to the task
    events = await memory.working.subscribe_events(
        channels=["task:analysis"],
        timeout=10
    )
    
    for event in events:
        if event["type"] == "analyze_billing_issue":
            # Process the task
            result = await process_billing_analysis(event["data"])
            
            # Publish result
            await memory.working.publish_event(
                channel="results:task_001",
                message={
                    "task_id": "task_001",
                    "result": result,
                    "agent_id": "analyst_001"
                }
            )
    
    # Agent 3 gets the results
    results = await memory.working.get_task_results("task_001", timeout=30)
    print(f"Task results: {results}")

async def process_billing_analysis(data):
    """Simulate billing analysis processing."""
    # Simulate processing time
    await asyncio.sleep(1)
    return {
        "status": "completed",
        "analysis": "Confirmed duplicate charge",
        "recommendation": "Process refund"
    }

asyncio.run(multi_agent_coordination_example())
```

## Integration Examples

### LangGraph Integration

```python
from langgraph.graph import StateGraph, END
from memory_agents import get_memory_facade

class AgentState:
    def __init__(self):
        self.messages = []
        self.user_id = None
        self.agent_id = None
        self.session_id = None
        self.memory = get_memory_facade()

async def memory_aware_agent(state: AgentState):
    """LangGraph node that uses memory."""
    # Get context from memory
    context = await state.memory.retrieve_comprehensive_context(
        agent_id=state.agent_id,
        user_id=state.user_id,
        session_id=state.session_id
    )
    
    # Use context to generate response
    response = generate_response(state.messages, context)
    
    # Store interaction in memory
    await state.memory.create_episode(
        episode_id=f"ep_{state.session_id}_{len(state.messages)}",
        context={
            "agent_id": state.agent_id,
            "user_id": state.user_id,
            "session_id": state.session_id
        },
        scope="user_private",
        episode_type="interaction",
        title="Agent interaction",
        trajectory=[{
            "step_id": str(len(state.messages)),
            "timestamp": "2024-01-01T10:00:00Z",
            "role": "agent",
            "action": "respond",
            "content": response
        }],
        success=True,
        importance=0.5
    )
    
    state.messages.append({"role": "agent", "content": response})
    return state

def generate_response(messages, context):
    """Generate response using context."""
    # Use context to generate more informed responses
    return "I understand your issue. Based on our previous interactions, I can help you with that."

# Create LangGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("memory_aware_agent", memory_aware_agent)
workflow.set_entry_point("memory_aware_agent")
workflow.add_edge("memory_aware_agent", END)
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from memory_agents import get_memory_facade
from pydantic import BaseModel

app = FastAPI()
memory = get_memory_facade()

class EpisodeRequest(BaseModel):
    episode_id: str
    agent_id: str
    user_id: str
    title: str
    content: str

@app.post("/episodes")
async def create_episode(request: EpisodeRequest):
    """Create a new episode."""
    try:
        episode_id = await memory.create_episode(
            episode_id=request.episode_id,
            context={
                "agent_id": request.agent_id,
                "user_id": request.user_id
            },
            scope="user_private",
            episode_type="interaction",
            title=request.title,
            trajectory=[{
                "step_id": "1",
                "timestamp": "2024-01-01T10:00:00Z",
                "role": "user",
                "action": "message",
                "content": request.content
            }],
            success=True,
            importance=0.5
        )
        return {"episode_id": episode_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/{agent_id}")
async def get_context(agent_id: str, user_id: str = None):
    """Get comprehensive context for an agent."""
    try:
        context = await memory.retrieve_comprehensive_context(
            agent_id=agent_id,
            user_id=user_id
        )
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        health = await memory.health_check()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Custom Agent Implementation

```python
class MemoryAwareAgent:
    """Custom agent that uses memory for context-aware responses."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memory = get_memory_facade()
    
    async def process_message(self, user_id: str, message: str, session_id: str = None):
        """Process a user message with memory context."""
        # Get comprehensive context
        context = await self.memory.retrieve_comprehensive_context(
            agent_id=self.agent_id,
            user_id=user_id,
            session_id=session_id
        )
        
        # Generate response using context
        response = await self.generate_response(message, context)
        
        # Store interaction in memory
        await self.memory.create_episode(
            episode_id=f"ep_{session_id}_{int(time.time())}",
            context={
                "agent_id": self.agent_id,
                "user_id": user_id,
                "session_id": session_id
            },
            scope="user_private",
            episode_type="interaction",
            title="User interaction",
            trajectory=[
                {
                    "step_id": "1",
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": "user",
                    "action": "message",
                    "content": message
                },
                {
                    "step_id": "2",
                    "timestamp": datetime.utcnow().isoformat(),
                    "role": "agent",
                    "action": "respond",
                    "content": response
                }
            ],
            success=True,
            importance=0.5
        )
        
        return response
    
    async def generate_response(self, message: str, context: dict) -> str:
        """Generate response using message and context."""
        # Use context to generate more informed responses
        episodes = context.get("episodes", [])
        knowledge = context.get("knowledge", [])
        facts = context.get("facts", [])
        
        # Simple response generation (replace with your LLM)
        if episodes:
            return f"I remember our previous conversation. {message}"
        elif knowledge:
            return f"Based on my knowledge, {message}"
        else:
            return f"I understand. {message}"

# Usage
agent = MemoryAwareAgent("support_agent_001")
response = await agent.process_message("user_123", "I need help with billing", "session_001")
print(response)
```

These examples demonstrate the full capabilities of the Memory-Agents system and how to integrate it into various applications and frameworks.


