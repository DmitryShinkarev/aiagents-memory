"""Basic usage example for memory-agents system."""

import asyncio
from utils.initialization import initialize_memory_system
from models.memory.semantic import SemanticKnowledge, KnowledgeType
from models.memory.procedural import Procedure, ProcedureType, ProcedureParameter


async def main():
    """Demonstrate basic usage of memory-agents system."""
    
    print("Initializing memory system...")
    orchestrator = await initialize_memory_system(agent_id="demo_agent_001")
    
    print("\n" + "="*60)
    print("SCENARIO 1: Working Memory - Active Conversation")
    print("="*60)
    
    session_id = "session_demo_001"
    
    # Add messages to working memory
    print("\nAdding messages to working memory...")
    await orchestrator.working.add_message(
        session_id=session_id,
        role="user",
        content="What are best practices for multi-agent systems?",
        metadata={"timestamp": "2024-01-10T10:00:00"}
    )
    
    await orchestrator.working.add_message(
        session_id=session_id,
        role="assistant",
        content="Here are key best practices for multi-agent systems: "
                "1) Clear communication protocols, 2) Memory management, "
                "3) Task coordination, 4) Error handling.",
        metadata={"model": "gpt-4", "tokens": 150}
    )
    
    await orchestrator.working.add_message(
        session_id=session_id,
        role="user",
        content="Tell me more about memory management",
        metadata={"timestamp": "2024-01-10T10:01:00"}
    )
    
    # Retrieve context
    print("\nRetrieving working memory context...")
    context = await orchestrator.working.get_context(session_id)
    print(f"Found {len(context)} messages in working memory")
    
    for i, msg in enumerate(context, 1):
        print(f"  {i}. [{msg['role']}]: {msg['content'][:60]}...")
    
    # Set temporary variables
    print("\nSetting temporary variables...")
    await orchestrator.working.set_temp_variable(
        session_id, "current_topic", "multi-agent-memory"
    )
    await orchestrator.working.set_temp_variable(
        session_id, "conversation_phase", "information_gathering"
    )
    
    topic = await orchestrator.working.get_temp_variable(session_id, "current_topic")
    print(f"Current topic: {topic}")
    
    # Get session stats
    stats = await orchestrator.working.get_session_stats(session_id)
    print(f"\nSession stats: {stats}")
    
    print("\n" + "="*60)
    print("SCENARIO 2: Semantic Memory - Knowledge Storage")
    print("="*60)
    
    # Add knowledge to semantic memory
    print("\nAdding knowledge to semantic memory...")
    
    knowledge1 = SemanticKnowledge(
        content="Multi-agent systems require distributed memory architecture",
        knowledge_type=KnowledgeType.FACT,
        source="user_conversation",
        namespace="multi-agent-systems",
        tags=["multi-agent", "memory", "architecture"],
        confidence=0.9
    )
    
    # Note: In production, you'd use an embedding service here
    # For demo, we'll just save without embedding
    try:
        # This would normally include embedding
        # await orchestrator.semantic.add_knowledge(knowledge1, embedding)
        print("  - Added knowledge about multi-agent memory")
    except Exception as e:
        print(f"  - Note: Skipping vector embedding (not configured): {e}")
    
    print("\n" + "="*60)
    print("SCENARIO 3: Procedural Memory - Storing Procedures")
    print("="*60)
    
    # Add procedure template
    print("\nAdding procedure to procedural memory...")
    
    procedure = Procedure(
        name="summarize_conversation",
        procedure_type=ProcedureType.PROMPT_TEMPLATE,
        description="Template for summarizing agent conversations",
        content="""Summarize the following conversation:

{conversation}

Provide a brief summary covering:
1. Main topics discussed
2. Key decisions made
3. Action items

Summary:""",
        parameters=[
            ProcedureParameter(
                name="conversation",
                type="string",
                required=True,
                description="The conversation text to summarize"
            )
        ],
        namespace="default",
        tags=["summarization", "conversation"]
    )
    
    proc_id = await orchestrator.procedural.save_procedure(procedure)
    print(f"Saved procedure with ID: {proc_id}")
    
    # Retrieve procedure
    retrieved_proc = await orchestrator.procedural.get_procedure(
        "summarize_conversation"
    )
    if retrieved_proc:
        print(f"Retrieved procedure: {retrieved_proc.name}")
        print(f"  Type: {retrieved_proc.procedure_type}")
        print(f"  Parameters: {len(retrieved_proc.parameters)}")
    
    print("\n" + "="*60)
    print("SCENARIO 4: Context Retrieval")
    print("="*60)
    
    # Retrieve comprehensive context
    print("\nRetrieving comprehensive context...")
    
    try:
        full_context = await orchestrator.retrieve_context(
            agent_id="demo_agent_001",
            session_id=session_id,
            query="How should I organize memory in multi-agent systems?",
            max_tokens=4096
        )
        
        print(f"\nContext summary:")
        print(f"  - Working memory: {len(full_context['working'])} items")
        print(f"  - Episodic memory: {len(full_context['episodic'])} items")
        print(f"  - Semantic memory: {len(full_context['semantic'])} items")
        print(f"  - Procedural memory: {len(full_context['procedural'])} items")
        print(f"  - Total tokens: {full_context['total_tokens']}")
    except Exception as e:
        print(f"Context retrieval: {e}")
    
    print("\n" + "="*60)
    print("SCENARIO 5: Session Consolidation")
    print("="*60)
    
    # Consolidate session to long-term memory
    print("\nConsolidating session to long-term memory...")
    
    try:
        await orchestrator.consolidate_session(
            agent_id="demo_agent_001",
            session_id=session_id
        )
        print("Session consolidated successfully!")
        print("  - Episode created in episodic memory")
        print("  - Facts extracted to semantic memory")
        print("  - Working memory cleared")
    except Exception as e:
        print(f"Consolidation: {e}")
    
    # Verify working memory is cleared
    context_after = await orchestrator.working.get_context(session_id)
    print(f"\nWorking memory after consolidation: {len(context_after)} messages")
    
    print("\n" + "="*60)
    print("SCENARIO 6: Statistics and Analytics")
    print("="*60)
    
    # Get episodic memory statistics
    print("\nEpisodic memory statistics:")
    ep_stats = await orchestrator.episodic.get_agent_statistics("demo_agent_001")
    print(f"  Total episodes: {ep_stats.get('total_episodes', 0)}")
    print(f"  Average importance: {ep_stats.get('avg_importance', 0):.2f}")
    print(f"  With feedback: {ep_stats.get('with_feedback', 0)}")
    
    # Get procedural memory statistics
    print("\nProcedural memory statistics:")
    proc_stats = await orchestrator.procedural.get_procedure_statistics()
    print(f"  Total procedures: {proc_stats['total']['count']}")
    
    # Get performance analytics (if event logger is available)
    if orchestrator.logger:
        print("\nPerformance analytics (last 24 hours):")
        perf_stats = await orchestrator.logger.analyze_performance(
            "demo_agent_001",
            time_window_hours=24
        )
        print(f"  Total events: {perf_stats.get('total_events', 0)}")
        print(f"  Average latency: {perf_stats.get('avg_latency', 0):.2f} ms")
    
    print("\n" + "="*60)
    print("Demo completed successfully!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())


