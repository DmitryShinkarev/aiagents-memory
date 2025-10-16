// MongoDB initialization script for memory-agents

// Switch to agent_memory database
db = db.getSiblingDB('agent_memory');

// Create collections if they don't exist
db.createCollection('episodes');
db.createCollection('semantic_memory');
db.createCollection('procedures');

// Create indexes for episodes
db.episodes.createIndex({ "agent_id": 1, "created_at": -1 });
db.episodes.createIndex({ "session_id": 1 });
db.episodes.createIndex({ "tags": 1 });
db.episodes.createIndex({ "importance": -1 });
db.episodes.createIndex(
    { "created_at": 1 },
    { expireAfterSeconds: 7776000 }  // 90 days
);

// Create indexes for semantic_memory
db.semantic_memory.createIndex({ "namespace": 1, "knowledge_type": 1 });
db.semantic_memory.createIndex({ "tags": 1 });
db.semantic_memory.createIndex({ "entities": 1 });
db.semantic_memory.createIndex({ "access_count": -1 });
db.semantic_memory.createIndex(
    { "created_at": 1 },
    { expireAfterSeconds: 31536000 }  // 365 days
);
db.semantic_memory.createIndex(
    { "content": "text" },
    { default_language: "english" }
);

// Create indexes for procedures
db.procedures.createIndex({ "name": 1, "namespace": 1, "is_active": 1 });
db.procedures.createIndex({ "procedure_type": 1 });
db.procedures.createIndex({ "tags": 1 });
db.procedures.createIndex({ "success_rate": -1, "usage_count": -1 });
db.procedures.createIndex({ "last_used": -1 });

print("MongoDB initialization completed!");





