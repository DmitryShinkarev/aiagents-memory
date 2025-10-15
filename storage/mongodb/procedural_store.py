"""MongoDB-based procedural memory implementation."""

from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

from models.memory.procedural import Procedure, ProcedureType, PROCEDURAL_MEMORY_INDEXES
from config.settings import get_settings


class ProceduralMemoryStore:
    """Procedural memory storage using MongoDB."""
    
    def __init__(self, mongo_client: AsyncIOMotorClient, db_name: Optional[str] = None):
        """
        Initialize procedural memory store.
        
        Args:
            mongo_client: Motor async MongoDB client
            db_name: Database name
        """
        settings = get_settings()
        self.db: AsyncIOMotorDatabase = mongo_client[db_name or settings.mongodb_database]
        self.collection = self.db.procedures
        self.settings = settings
    
    async def initialize(self):
        """Create indexes for the collection."""
        for index_spec in PROCEDURAL_MEMORY_INDEXES:
            if len(index_spec) == 1:
                await self.collection.create_index(index_spec[0])
            else:
                await self.collection.create_index(index_spec[0])
    
    async def save_procedure(self, procedure: Procedure) -> str:
        """
        Save a procedure to the database.
        
        Args:
            procedure: Procedure to save
            
        Returns:
            Procedure ID
        """
        procedure_dict = procedure.model_dump(by_alias=True, exclude_none=True)
        
        # Remove _id if None
        if procedure_dict.get("_id") is None:
            procedure_dict.pop("_id", None)
        
        result = await self.collection.insert_one(procedure_dict)
        return str(result.inserted_id)
    
    async def get_procedure(
        self,
        name: str,
        namespace: str = "default"
    ) -> Optional[Procedure]:
        """
        Get a procedure by name.
        
        Args:
            name: Procedure name
            namespace: Namespace
            
        Returns:
            Procedure or None if not found
        """
        doc = await self.collection.find_one({
            "name": name,
            "namespace": namespace,
            "is_active": True
        })
        
        return Procedure(**doc) if doc else None
    
    async def get_procedure_by_id(self, procedure_id: str) -> Optional[Procedure]:
        """Get a procedure by ID."""
        doc = await self.collection.find_one({"_id": ObjectId(procedure_id)})
        return Procedure(**doc) if doc else None
    
    async def search_procedures(
        self,
        procedure_type: Optional[ProcedureType] = None,
        tags: Optional[List[str]] = None,
        namespace: str = "default",
        min_success_rate: float = 0.7,
        limit: int = 20
    ) -> List[Procedure]:
        """
        Search procedures by criteria.
        
        Args:
            procedure_type: Optional type filter
            tags: Optional tag filter
            namespace: Namespace
            min_success_rate: Minimum success rate threshold
            limit: Maximum results
            
        Returns:
            List of matching procedures
        """
        query = {
            "is_active": True,
            "namespace": namespace,
            "success_rate": {"$gte": min_success_rate}
        }
        
        if procedure_type:
            query["procedure_type"] = procedure_type.value
        
        if tags:
            query["tags"] = {"$in": tags}
        
        cursor = self.collection.find(query).sort([
            ("success_rate", -1),
            ("usage_count", -1)
        ]).limit(limit)
        
        procedures = await cursor.to_list(length=limit)
        return [Procedure(**p) for p in procedures]
    
    async def get_best_procedures(
        self,
        procedure_type: ProcedureType,
        limit: int = 5
    ) -> List[Procedure]:
        """
        Get best performing procedures of a given type.
        
        Args:
            procedure_type: Procedure type
            limit: Maximum results
            
        Returns:
            Top procedures sorted by success rate
        """
        return await self.search_procedures(
            procedure_type=procedure_type,
            min_success_rate=0.0,
            limit=limit
        )
    
    async def update_usage_stats(
        self,
        procedure_id: str,
        success: bool,
        execution_time: float
    ):
        """
        Update procedure usage statistics.
        
        Uses exponential moving average for success_rate and execution_time.
        
        Args:
            procedure_id: Procedure ID
            success: Whether execution was successful
            execution_time: Execution time in seconds
        """
        # Get current stats
        doc = await self.collection.find_one({"_id": ObjectId(procedure_id)})
        
        if not doc:
            return
        
        # Calculate new statistics
        total_uses = doc.get("usage_count", 0) + 1
        current_success_rate = doc.get("success_rate", 1.0)
        current_avg_time = doc.get("average_execution_time")
        
        # Exponential moving average (EMA) with alpha=0.1
        alpha = 0.1
        
        # Update success rate
        new_success_rate = (
            alpha * (1.0 if success else 0.0) +
            (1 - alpha) * current_success_rate
        )
        
        # Update average execution time
        if current_avg_time is not None:
            new_avg_time = (
                alpha * execution_time +
                (1 - alpha) * current_avg_time
            )
        else:
            new_avg_time = execution_time
        
        # Update document
        await self.collection.update_one(
            {"_id": ObjectId(procedure_id)},
            {
                "$set": {
                    "usage_count": total_uses,
                    "success_rate": new_success_rate,
                    "average_execution_time": new_avg_time,
                    "last_used": datetime.utcnow()
                }
            }
        )
    
    async def deactivate_procedure(self, procedure_id: str):
        """Deactivate a procedure (soft delete)."""
        await self.collection.update_one(
            {"_id": ObjectId(procedure_id)},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def activate_procedure(self, procedure_id: str):
        """Reactivate a procedure."""
        await self.collection.update_one(
            {"_id": ObjectId(procedure_id)},
            {
                "$set": {
                    "is_active": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    async def update_procedure(self, procedure_id: str, updates: dict):
        """
        Update procedure fields.
        
        Args:
            procedure_id: Procedure ID
            updates: Update dictionary
        """
        updates["updated_at"] = datetime.utcnow()
        updates["version"] = {"$inc": 1}
        
        await self.collection.update_one(
            {"_id": ObjectId(procedure_id)},
            {"$set": updates}
        )
    
    async def cleanup_unused_procedures(self, days_unused: int = 90) -> int:
        """
        Deactivate procedures that haven't been used in specified days.
        
        Args:
            days_unused: Days threshold
            
        Returns:
            Number of procedures deactivated
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_unused)
        
        result = await self.collection.update_many(
            {
                "is_active": True,
                "last_used": {"$lt": cutoff_date}
            },
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count
    
    async def get_procedure_statistics(self, namespace: str = "default") -> dict:
        """
        Get statistics for procedures in a namespace.
        
        Returns:
            Dictionary with procedure counts and metrics
        """
        pipeline = [
            {"$match": {"namespace": namespace, "is_active": True}},
            {
                "$group": {
                    "_id": "$procedure_type",
                    "count": {"$sum": 1},
                    "avg_success_rate": {"$avg": "$success_rate"},
                    "total_usage": {"$sum": "$usage_count"}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(length=None)
        
        stats = {
            "by_type": {item["_id"]: {
                "count": item["count"],
                "avg_success_rate": item["avg_success_rate"],
                "total_usage": item["total_usage"]
            } for item in result}
        }
        
        # Overall stats
        total_count = sum(item["count"] for item in result)
        total_usage = sum(item["total_usage"] for item in result)
        
        stats["total"] = {
            "count": total_count,
            "total_usage": total_usage
        }
        
        return stats


