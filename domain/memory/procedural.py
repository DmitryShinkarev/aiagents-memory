"""
Procedural Memory Service - Skills and procedures memory.

This service manages procedural memory in MongoDB, including skills,
procedures, and executable code with usage tracking and metrics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId

from ...storage.clients.mongo_client import get_mongo_client
from ...config.settings import get_settings

logger = logging.getLogger(__name__)


class ProceduralMemoryService:
    """Service for managing procedural memory in MongoDB."""
    
    def __init__(self):
        self._mongo_client = None
        self._settings = get_settings()
    
    async def _get_mongo_client(self):
        """Get MongoDB client instance."""
        if self._mongo_client is None:
            self._mongo_client = await get_mongo_client()
        return self._mongo_client
    
    # Procedure creation and management
    
    async def store_procedure(
        self,
        procedure_id: str,
        name: str,
        description: str,
        code: str,
        language: str = "python",
        parameters_schema: Optional[Dict[str, Any]] = None,
        return_schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        created_by: str = "system"
    ) -> str:
        """
        Store a new procedure.
        
        Args:
            procedure_id: Unique procedure identifier
            name: Procedure name (must be unique)
            description: Procedure description
            code: Executable code
            language: Programming language (python, javascript, sql)
            parameters_schema: JSON Schema for parameters
            return_schema: JSON Schema for return value
            tags: Procedure tags
            created_by: Creator identifier
            
        Returns:
            Created procedure ID
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Check if procedure with same name already exists
            existing = await mongo_client.find_one(
                "procedures",
                {"name": name, "active": True}
            )
            
            if existing:
                raise ValueError(f"Procedure with name '{name}' already exists")
            
            # Create procedure document
            procedure_doc = {
                "procedure_id": procedure_id,
                "name": name,
                "description": description,
                "code": code,
                "language": language,
                "parameters_schema": parameters_schema or {},
                "return_schema": return_schema or {},
                "tags": tags or [],
                "created_at": datetime.utcnow(),
                "active": True,
                "deactivated_at": None,
                "usage_count": 0,
                "success_rate": 1.0,
                "avg_execution_time_ms": 0.0,
                "last_used": None,
                "created_by": created_by
            }
            
            # Insert into MongoDB
            inserted_id = await mongo_client.insert_one("procedures", procedure_doc)
            
            logger.info(f"Stored procedure {name} with ID {procedure_id}")
            return str(inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store procedure {name}: {e}")
            raise
    
    async def get_procedure(
        self,
        name: str,
        include_code: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get procedure by name.
        
        Args:
            name: Procedure name
            include_code: Whether to include code in response
            
        Returns:
            Procedure data or None if not found
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            projection = None
            if not include_code:
                projection = {"code": 0}
            
            procedure = await mongo_client.find_one(
                "procedures",
                {"name": name, "active": True},
                projection
            )
            
            if procedure:
                # Convert ObjectId to string
                procedure["_id"] = str(procedure["_id"])
                logger.debug(f"Retrieved procedure {name}")
            
            return procedure
            
        except Exception as e:
            logger.error(f"Failed to get procedure {name}: {e}")
            return None
    
    async def get_procedure_by_id(
        self,
        procedure_id: str,
        include_code: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get procedure by ID.
        
        Args:
            procedure_id: Procedure identifier
            include_code: Whether to include code in response
            
        Returns:
            Procedure data or None if not found
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            projection = None
            if not include_code:
                projection = {"code": 0}
            
            procedure = await mongo_client.find_one(
                "procedures",
                {"procedure_id": procedure_id, "active": True},
                projection
            )
            
            if procedure:
                # Convert ObjectId to string
                procedure["_id"] = str(procedure["_id"])
                logger.debug(f"Retrieved procedure {procedure_id}")
            
            return procedure
            
        except Exception as e:
            logger.error(f"Failed to get procedure {procedure_id}: {e}")
            return None
    
    async def update_procedure(
        self,
        name: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update procedure.
        
        Args:
            name: Procedure name
            updates: Updates to apply
            
        Returns:
            True if successful
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Add update timestamp
            updates["updated_at"] = datetime.utcnow()
            
            result = await mongo_client.update_one(
                "procedures",
                {"name": name, "active": True},
                {"$set": updates}
            )
            
            success = result["modified_count"] > 0
            
            if success:
                logger.debug(f"Updated procedure {name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update procedure {name}: {e}")
            return False
    
    async def deactivate_procedure(self, name: str) -> bool:
        """
        Deactivate procedure (soft delete).
        
        Args:
            name: Procedure name
            
        Returns:
            True if successful
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            result = await mongo_client.update_one(
                "procedures",
                {"name": name, "active": True},
                {
                    "$set": {
                        "active": False,
                        "deactivated_at": datetime.utcnow()
                    }
                }
            )
            
            success = result["modified_count"] > 0
            
            if success:
                logger.info(f"Deactivated procedure {name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to deactivate procedure {name}: {e}")
            return False
    
    async def delete_procedure(self, name: str) -> bool:
        """
        Delete procedure (hard delete).
        
        Args:
            name: Procedure name
            
        Returns:
            True if successful
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            deleted_count = await mongo_client.delete_one(
                "procedures",
                {"name": name}
            )
            
            success = deleted_count > 0
            
            if success:
                logger.info(f"Deleted procedure {name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete procedure {name}: {e}")
            return False
    
    # Procedure execution and metrics
    
    async def execute_procedure(
        self,
        name: str,
        parameters: Optional[Dict[str, Any]] = None,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute procedure and update metrics.
        
        Args:
            name: Procedure name
            parameters: Procedure parameters
            execution_context: Execution context
            
        Returns:
            Execution result with metadata
        """
        try:
            # Get procedure
            procedure = await self.get_procedure(name, include_code=True)
            if not procedure:
                raise ValueError(f"Procedure '{name}' not found")
            
            # Validate parameters against schema
            if procedure.get("parameters_schema") and parameters:
                # TODO: Implement parameter validation
                pass
            
            # Record execution start
            start_time = datetime.utcnow()
            execution_start_ms = start_time.timestamp() * 1000
            
            try:
                # Execute procedure
                result = await self._execute_code(
                    procedure["code"],
                    procedure["language"],
                    parameters or {},
                    execution_context or {}
                )
                
                # Record successful execution
                execution_time_ms = (datetime.utcnow().timestamp() * 1000) - execution_start_ms
                success = True
                
                # Update metrics
                await self._update_execution_metrics(
                    name,
                    execution_time_ms,
                    success
                )
                
                return {
                    "success": True,
                    "result": result,
                    "execution_time_ms": execution_time_ms,
                    "procedure_name": name,
                    "executed_at": start_time.isoformat()
                }
                
            except Exception as e:
                # Record failed execution
                execution_time_ms = (datetime.utcnow().timestamp() * 1000) - execution_start_ms
                success = False
                
                # Update metrics
                await self._update_execution_metrics(
                    name,
                    execution_time_ms,
                    success
                )
                
                return {
                    "success": False,
                    "error": str(e),
                    "execution_time_ms": execution_time_ms,
                    "procedure_name": name,
                    "executed_at": start_time.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to execute procedure {name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "procedure_name": name,
                "executed_at": datetime.utcnow().isoformat()
            }
    
    async def _execute_code(
        self,
        code: str,
        language: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute code in the specified language.
        
        Args:
            code: Code to execute
            language: Programming language
            parameters: Procedure parameters
            context: Execution context
            
        Returns:
            Execution result
        """
        if language == "python":
            return await self._execute_python_code(code, parameters, context)
        elif language == "javascript":
            return await self._execute_javascript_code(code, parameters, context)
        elif language == "sql":
            return await self._execute_sql_code(code, parameters, context)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    async def _execute_python_code(
        self,
        code: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """Execute Python code safely."""
        try:
            # Create execution environment
            exec_globals = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "abs": abs,
                    "round": round,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "sorted": sorted,
                    "reversed": reversed,
                    "any": any,
                    "all": all,
                    "isinstance": isinstance,
                    "type": type,
                    "hasattr": hasattr,
                    "getattr": getattr,
                    "setattr": setattr,
                },
                "parameters": parameters,
                "context": context,
                "datetime": datetime,
                "timedelta": timedelta
            }
            
            exec_locals = {}
            
            # Execute code
            exec(code, exec_globals, exec_locals)
            
            # Return result if available
            if "result" in exec_locals:
                return exec_locals["result"]
            elif "return_value" in exec_locals:
                return exec_locals["return_value"]
            else:
                return None
                
        except Exception as e:
            raise RuntimeError(f"Python execution failed: {str(e)}")
    
    async def _execute_javascript_code(
        self,
        code: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """Execute JavaScript code (placeholder)."""
        # TODO: Implement JavaScript execution using PyExecJS or similar
        raise NotImplementedError("JavaScript execution not yet implemented")
    
    async def _execute_sql_code(
        self,
        code: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """Execute SQL code (placeholder)."""
        # TODO: Implement SQL execution
        raise NotImplementedError("SQL execution not yet implemented")
    
    async def _update_execution_metrics(
        self,
        name: str,
        execution_time_ms: float,
        success: bool
    ) -> None:
        """Update procedure execution metrics."""
        try:
            mongo_client = await self._get_mongo_client()
            
            # Get current metrics
            procedure = await mongo_client.find_one(
                "procedures",
                {"name": name, "active": True},
                {"usage_count": 1, "success_rate": 1, "avg_execution_time_ms": 1}
            )
            
            if not procedure:
                return
            
            current_usage_count = procedure.get("usage_count", 0)
            current_success_rate = procedure.get("success_rate", 1.0)
            current_avg_time = procedure.get("avg_execution_time_ms", 0.0)
            
            # Calculate new metrics
            new_usage_count = current_usage_count + 1
            
            # Update success rate (exponential moving average)
            alpha = 0.1  # Smoothing factor
            new_success_rate = (1 - alpha) * current_success_rate + alpha * (1.0 if success else 0.0)
            
            # Update average execution time (exponential moving average)
            new_avg_time = (1 - alpha) * current_avg_time + alpha * execution_time_ms
            
            # Update procedure
            await mongo_client.update_one(
                "procedures",
                {"name": name, "active": True},
                {
                    "$set": {
                        "usage_count": new_usage_count,
                        "success_rate": new_success_rate,
                        "avg_execution_time_ms": new_avg_time,
                        "last_used": datetime.utcnow()
                    }
                }
            )
            
            logger.debug(f"Updated metrics for procedure {name}")
            
        except Exception as e:
            logger.warning(f"Failed to update metrics for procedure {name}: {e}")
    
    # Procedure querying
    
    async def query_procedures(
        self,
        filter_by_tags: Optional[List[str]] = None,
        filter_by_language: Optional[str] = None,
        min_usage_count: Optional[int] = None,
        min_success_rate: Optional[float] = None,
        sort_by: str = "usage_count",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query procedures with various filters.
        
        Args:
            filter_by_tags: Filter by tags
            filter_by_language: Filter by language
            min_usage_count: Minimum usage count
            min_success_rate: Minimum success rate
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of procedures
        """
        try:
            # Build MongoDB filter
            mongo_filter = {"active": True}
            
            if filter_by_tags:
                mongo_filter["tags"] = {"$in": filter_by_tags}
            
            if filter_by_language:
                mongo_filter["language"] = filter_by_language
            
            if min_usage_count is not None:
                mongo_filter["usage_count"] = {"$gte": min_usage_count}
            
            if min_success_rate is not None:
                mongo_filter["success_rate"] = {"$gte": min_success_rate}
            
            # Build sort criteria
            from pymongo import ASCENDING, DESCENDING
            sort_criteria = []
            if sort_by == "usage_count":
                sort_criteria.append(("usage_count", DESCENDING if sort_order == "desc" else ASCENDING))
            elif sort_by == "success_rate":
                sort_criteria.append(("success_rate", DESCENDING if sort_order == "desc" else ASCENDING))
            elif sort_by == "avg_execution_time_ms":
                sort_criteria.append(("avg_execution_time_ms", ASCENDING if sort_order == "asc" else DESCENDING))
            elif sort_by == "created_at":
                sort_criteria.append(("created_at", DESCENDING if sort_order == "desc" else ASCENDING))
            else:
                sort_criteria.append((sort_by, DESCENDING if sort_order == "desc" else ASCENDING))
            
            mongo_client = await self._get_mongo_client()
            procedures = await mongo_client.find_many(
                "procedures",
                mongo_filter,
                sort=sort_criteria,
                skip=offset,
                limit=limit
            )
            
            # Convert ObjectIds to strings and exclude code for list view
            for procedure in procedures:
                procedure["_id"] = str(procedure["_id"])
                if "code" in procedure:
                    del procedure["code"]  # Don't include code in list view
            
            logger.debug(f"Retrieved {len(procedures)} procedures")
            return procedures
            
        except Exception as e:
            logger.error(f"Failed to query procedures: {e}")
            return []
    
    # Health and monitoring
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on procedural memory service."""
        try:
            mongo_client = await self._get_mongo_client()
            mongo_health = await mongo_client.health_check()
            
            return {
                "service": "procedural_memory",
                "status": "healthy" if mongo_health["status"] == "healthy" else "unhealthy",
                "mongodb": mongo_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Procedural memory health check failed: {e}")
            return {
                "service": "procedural_memory",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get procedural memory metrics."""
        try:
            mongo_client = await self._get_mongo_client()
            
            # Get total procedure count
            total_count = await mongo_client.count_documents(
                "procedures",
                {"active": True}
            )
            
            # Get procedures by language
            language_counts = {}
            languages = ["python", "javascript", "sql"]
            for language in languages:
                count = await mongo_client.count_documents(
                    "procedures",
                    {"language": language, "active": True}
                )
                language_counts[language] = count
            
            # Get high-usage procedures
            high_usage_count = await mongo_client.count_documents(
                "procedures",
                {"usage_count": {"$gte": 10}, "active": True}
            )
            
            # Get high-success-rate procedures
            high_success_count = await mongo_client.count_documents(
                "procedures",
                {"success_rate": {"$gte": 0.9}, "active": True}
            )
            
            # Get recently used procedures
            recent_use_threshold = datetime.utcnow() - timedelta(days=7)
            recently_used_count = await mongo_client.count_documents(
                "procedures",
                {"last_used": {"$gte": recent_use_threshold}, "active": True}
            )
            
            return {
                "total_procedures": total_count,
                "procedures_by_language": language_counts,
                "high_usage_procedures": high_usage_count,
                "high_success_rate_procedures": high_success_count,
                "recently_used_procedures": recently_used_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get procedural memory metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
