"""
Example usage of the Memory-Agents system.

This example demonstrates how to use the memory system for a multi-agent
scenario with different types of memory operations.
"""

import asyncio
import logging
from datetime import datetime

from memory_agents import (
    get_memory_facade,
    EpisodeContext,
    EpisodeTrajectory,
    SourceType,
    MemoryScope
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    logger.info("Starting Memory-Agents example")
    
    # Get memory facade
    memory = get_memory_facade()
    
    # Example 1: Working Memory - Store session context
    logger.info("Example 1: Working Memory")
    
    session_data = {
        "agent_id": "support_agent_001",
        "current_message": "User needs help with billing",
        "conversation_history": [
            {"role": "user", "content": "I have a billing question"},
            {"role": "agent", "content": "I'd be happy to help with your billing question"}
        ],
        "temporary_variables": {
            "user_tier": "premium",
            "issue_type": "billing"
        }
    }
    
    await memory.working.store_session("session_001", session_data)
    logger.info("Stored session data")
    
    # Retrieve context
    context = await memory.get_context("support_agent_001", "session_001")
    logger.info(f"Retrieved context: {context['current_message']}")
    
    # Example 2: Episodic Memory - Create an episode
    logger.info("Example 2: Episodic Memory")
    
    episode_id = "episode_001"
    trajectory = [
        {
            "step_id": "step_1",
            "timestamp": datetime.utcnow().isoformat(),
            "role": "user",
            "action": "message",
            "content": "I need help with my billing",
            "metadata": {"message_type": "support_request"}
        },
        {
            "step_id": "step_2", 
            "timestamp": datetime.utcnow().isoformat(),
            "role": "agent",
            "action": "response",
            "content": "I'll help you with your billing question. Can you provide your account number?",
            "metadata": {"response_type": "information_request"}
        }
    ]
    
    await memory.create_episode(
        episode_id=episode_id,
        context={
            "agent_id": "support_agent_001",
            "user_id": "user_123",
            "session_id": "session_001"
        },
        scope="user_private",
        episode_type="interaction",
        title="Billing support interaction",
        trajectory=trajectory,
        outcome="User provided account number, issue resolved",
        success=True,
        importance=0.8,
        user_satisfaction=0.9,
        tags=["billing", "support", "resolved"]
    )
    logger.info(f"Created episode {episode_id}")
    
    # Example 3: Semantic Memory - Store knowledge
    logger.info("Example 3: Semantic Memory")
    
    knowledge_id = "knowledge_001"
    await memory.create_knowledge(
        knowledge_id=knowledge_id,
        knowledge="Premium users have priority support and can access billing history for the last 2 years",
        source="system",
        confidence=1.0,
        agent_id="support_agent_001",
        tags=["billing", "premium", "support"],
        supporting_evidence=["episode_001"],
        temporal_scope="always"
    )
    logger.info(f"Created knowledge {knowledge_id}")
    
    # Example 4: Procedural Memory - Store a procedure
    logger.info("Example 4: Procedural Memory")
    
    procedure_code = """
def resolve_billing_issue(account_number, issue_type):
    \"\"\"
    Resolve billing issues for customers.
    
    Args:
        account_number: Customer account number
        issue_type: Type of billing issue
        
    Returns:
        Resolution status and details
    \"\"\"
    # Check account status
    account_status = check_account_status(account_number)
    
    if issue_type == "overcharge":
        # Process refund
        refund_amount = calculate_refund(account_number)
        process_refund(account_number, refund_amount)
        return {"status": "resolved", "action": "refund", "amount": refund_amount}
    elif issue_type == "missing_payment":
        # Send payment reminder
        send_payment_reminder(account_number)
        return {"status": "pending", "action": "reminder_sent"}
    else:
        return {"status": "escalated", "action": "manual_review"}
"""
    
    await memory.procedural.store_procedure(
        procedure_id="proc_001",
        name="resolve_billing_issue",
        description="Resolve billing issues for customers",
        code=procedure_code,
        language="python",
        parameters_schema={
            "type": "object",
            "properties": {
                "account_number": {"type": "string"},
                "issue_type": {"type": "string", "enum": ["overcharge", "missing_payment", "other"]}
            },
            "required": ["account_number", "issue_type"]
        },
        tags=["billing", "support", "automation"]
    )
    logger.info("Stored billing resolution procedure")
    
    # Example 5: User Facts - Store user information
    logger.info("Example 5: User Facts")
    
    await memory.facts.store_fact(
        fact_id="fact_001",
        user_id="user_123",
        fact_type="personal",
        key="name",
        value="John Doe",
        confidence=1.0,
        source="user_stated",
        evidence=["episode_001"]
    )
    
    await memory.facts.store_fact(
        fact_id="fact_002",
        user_id="user_123",
        fact_type="preference",
        key="communication_preference",
        value="email",
        confidence=0.9,
        source="observed",
        evidence=["episode_001"]
    )
    logger.info("Stored user facts")
    
    # Example 6: Comprehensive Context Retrieval
    logger.info("Example 6: Comprehensive Context Retrieval")
    
    comprehensive_context = await memory.retrieve_comprehensive_context(
        agent_id="support_agent_001",
        user_id="user_123",
        session_id="session_001",
        include_episodes=True,
        include_knowledge=True,
        include_facts=True,
        max_episodes=5,
        max_knowledge=5
    )
    
    logger.info(f"Retrieved comprehensive context with {len(comprehensive_context.get('episodes', []))} episodes")
    logger.info(f"User facts: {list(comprehensive_context.get('facts', {}).keys())}")
    
    # Example 7: Query Episodes
    logger.info("Example 7: Query Episodes")
    
    episodes = await memory.query_episodes(
        filter_by_agent_id="support_agent_001",
        filter_by_user_id="user_123",
        filter_by_tags=["billing"],
        limit=10
    )
    
    logger.info(f"Found {len(episodes)} billing-related episodes")
    
    # Example 8: Health Check
    logger.info("Example 8: Health Check")
    
    health = await memory.health_check()
    logger.info(f"Memory system health: {health['status']}")
    
    # Example 9: Metrics
    logger.info("Example 9: Metrics")
    
    metrics = await memory.get_metrics()
    logger.info(f"Episodic memory episodes: {metrics['episodic_memory'].get('total_episodes', 0)}")
    logger.info(f"Semantic memory knowledge: {metrics['semantic_memory'].get('total_knowledge', 0)}")
    logger.info(f"User facts: {metrics['facts'].get('total_facts', 0)}")
    
    logger.info("Memory-Agents example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
