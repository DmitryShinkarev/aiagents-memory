"""
User Facts Service - Personal information memory.

This service manages user facts in MongoDB with full version history,
conflict resolution, and automatic fact extraction.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId

from storage.clients.mongo_client import get_mongo_client
from config.settings import get_settings
from api.contracts.facts import SourceType

logger = logging.getLogger(__name__)


class FactsService:
    """Service for managing user facts with version history."""
    
    def __init__(self):
        self._mongo_client = None
        self._settings = get_settings()
    
    async def _get_mongo_client(self):
        """Get MongoDB client instance."""
        if self._mongo_client is None:
            self._mongo_client = await get_mongo_client()
        return self._mongo_client
    
    # Fact creation and management
    
    async def store_fact(
        self,
        fact_id: str,
        user_id: str,
        fact_type: str,
        key: str,
        value: str,
        confidence: float,
        source: SourceType,
        evidence: Optional[List[str]] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        force_update: bool = False
    ) -> str:
        """
        Store or update a user fact.
        
        Args:
            fact_id: Unique fact identifier
            user_id: User identifier
            fact_type: Type of fact (personal, location, preference, behavior, relationship)
            key: Fact key (e.g., 'name', 'city', 'favorite_color')
            value: Fact value
            confidence: Confidence level (0.0-1.0)
            source: Source of the fact
            evidence: Episode IDs that support this fact
            valid_from: When this fact becomes valid
            valid_until: When this fact expires
            force_update: Force update even if confidence is lower
            
        Returns:
            Created/updated fact ID
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Get existing fact
            existing_fact = await mongo_client.find_one(
                "user_facts",
                {"user_id": user_id, "key": key}
            )
            
            if existing_fact:
                # Handle conflict resolution
                should_update = await self._should_update_fact(
                    existing_fact,
                    value,
                    confidence,
                    source,
                    force_update
                )
                
                if should_update:
                    # Create new version
                    new_version = {
                        "version_id": f"{fact_id}_v{len(existing_fact.get('versions', [])) + 1}",
                        "value": value,
                        "confidence": confidence,
                        "valid_from": valid_from or datetime.utcnow(),
                        "valid_until": valid_until,
                        "source": source.value,
                        "evidence": evidence or [],
                        "deprecated": False
                    }
                    
                    # Update current value and add version
                    await mongo_client.update_one(
                        "user_facts",
                        {"user_id": user_id, "key": key},
                        {
                            "$set": {
                                "current_value": value,
                                "last_updated": datetime.utcnow()
                            },
                            "$push": {"versions": new_version}
                        }
                    )
                    
                    logger.info(f"Updated fact {key} for user {user_id}")
                else:
                    logger.debug(f"Fact {key} for user {user_id} not updated due to conflict resolution")
                
                return existing_fact["_id"]
            else:
                # Create new fact
                fact_doc = {
                    "fact_id": fact_id,
                    "user_id": user_id,
                    "fact_type": fact_type,
                    "key": key,
                    "current_value": value,
                    "versions": [
                        {
                            "version_id": f"{fact_id}_v1",
                            "value": value,
                            "confidence": confidence,
                            "valid_from": valid_from or datetime.utcnow(),
                            "valid_until": valid_until,
                            "source": source.value,
                            "evidence": evidence or [],
                            "deprecated": False
                        }
                    ],
                    "last_updated": datetime.utcnow(),
                    "access_count": 0
                }
                
                # Insert into MongoDB
                inserted_id = await mongo_client.insert_one("user_facts", fact_doc)
                
                logger.info(f"Created fact {key} for user {user_id}")
                return str(inserted_id)
                
        except Exception as e:
            logger.error(f"Failed to store fact {key} for user {user_id}: {e}")
            raise
    
    async def get_fact(
        self,
        user_id: str,
        key: str,
        valid_at: Optional[datetime] = None,
        update_access: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get user fact by key.
        
        Args:
            user_id: User identifier
            key: Fact key
            valid_at: Point in time for fact validity
            update_access: Whether to update access count
            
        Returns:
            Fact data or None if not found
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            fact = await mongo_client.find_one(
                "user_facts",
                {"user_id": user_id, "key": key}
            )
            
            if fact:
                # Convert ObjectId to string
                fact["_id"] = str(fact["_id"])
                
                # Filter versions by validity if valid_at specified
                if valid_at:
                    fact["versions"] = [
                        version for version in fact.get("versions", [])
                        if self._is_version_valid(version, valid_at)
                    ]
                
                # Update access count
                if update_access:
                    await mongo_client.update_one(
                        "user_facts",
                        {"user_id": user_id, "key": key},
                        {"$inc": {"access_count": 1}}
                    )
                
                logger.debug(f"Retrieved fact {key} for user {user_id}")
            
            return fact
            
        except Exception as e:
            logger.error(f"Failed to get fact {key} for user {user_id}: {e}")
            return None
    
    async def get_user_profile(
        self,
        user_id: str,
        include_history: bool = False,
        valid_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive user profile.
        
        Args:
            user_id: User identifier
            include_history: Whether to include version history
            valid_at: Point in time for fact validity
            
        Returns:
            User profile data
        """
        try:
            mongo_client = await self._get_mongo_client()
            
            # Get all facts for user
            facts = await mongo_client.find_many(
                "user_facts",
                {"user_id": user_id}
            )
            
            profile = {
                "user_id": user_id,
                "facts": {},
                "fact_types": {},
                "last_updated": None,
                "total_facts": len(facts)
            }
            
            for fact in facts:
                key = fact["key"]
                fact_type = fact["fact_type"]
                
                # Filter versions by validity if valid_at specified
                if valid_at:
                    fact["versions"] = [
                        version for version in fact.get("versions", [])
                        if self._is_version_valid(version, valid_at)
                    ]
                
                # Add to profile
                profile["facts"][key] = {
                    "current_value": fact["current_value"],
                    "fact_type": fact_type,
                    "last_updated": fact["last_updated"].isoformat(),
                    "access_count": fact.get("access_count", 0)
                }
                
                if include_history:
                    profile["facts"][key]["versions"] = fact.get("versions", [])
                
                # Group by fact type
                if fact_type not in profile["fact_types"]:
                    profile["fact_types"][fact_type] = []
                profile["fact_types"][fact_type].append(key)
                
                # Update last_updated
                if not profile["last_updated"] or fact["last_updated"] > datetime.fromisoformat(profile["last_updated"]):
                    profile["last_updated"] = fact["last_updated"].isoformat()
            
            logger.debug(f"Retrieved profile for user {user_id} with {len(facts)} facts")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get profile for user {user_id}: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    async def query_facts(
        self,
        user_id: str,
        filter_by_fact_type: Optional[List[str]] = None,
        filter_by_key: Optional[List[str]] = None,
        filter_by_source: Optional[List[SourceType]] = None,
        min_confidence: Optional[float] = None,
        only_current: bool = True,
        valid_at: Optional[datetime] = None,
        time_range_start: Optional[datetime] = None,
        time_range_end: Optional[datetime] = None,
        sort_by: str = "key",
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query user facts with various filters.
        
        Args:
            user_id: User identifier
            filter_by_fact_type: Filter by fact types
            filter_by_key: Filter by fact keys
            filter_by_source: Filter by source types
            min_confidence: Minimum confidence threshold
            only_current: Only return current (non-deprecated) facts
            valid_at: Point in time for fact validity
            time_range_start: Start of time range
            time_range_end: End of time range
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of facts
        """
        try:
            # Build MongoDB filter
            mongo_filter = {"user_id": user_id}
            
            if filter_by_fact_type:
                mongo_filter["fact_type"] = {"$in": filter_by_fact_type}
            
            if filter_by_key:
                mongo_filter["key"] = {"$in": filter_by_key}
            
            if time_range_start:
                mongo_filter["last_updated"] = {"$gte": time_range_start}
            
            if time_range_end:
                if "last_updated" in mongo_filter:
                    mongo_filter["last_updated"]["$lte"] = time_range_end
                else:
                    mongo_filter["last_updated"] = {"$lte": time_range_end}
            
            # Build sort criteria
            from pymongo import ASCENDING, DESCENDING
            sort_criteria = []
            if sort_by == "key":
                sort_criteria.append(("key", ASCENDING if sort_order == "asc" else DESCENDING))
            elif sort_by == "fact_type":
                sort_criteria.append(("fact_type", ASCENDING if sort_order == "asc" else DESCENDING))
            elif sort_by == "last_updated":
                sort_criteria.append(("last_updated", DESCENDING if sort_order == "desc" else ASCENDING))
            else:
                sort_criteria.append((sort_by, ASCENDING if sort_order == "asc" else DESCENDING))
            
            mongo_client = await self._get_mongo_client()
            facts = await mongo_client.find_many(
                "user_facts",
                mongo_filter,
                sort=sort_criteria,
                skip=offset,
                limit=limit
            )
            
            # Process facts
            processed_facts = []
            for fact in facts:
                # Convert ObjectId to string
                fact["_id"] = str(fact["_id"])
                
                # Filter versions by validity if valid_at specified
                if valid_at:
                    fact["versions"] = [
                        version for version in fact.get("versions", [])
                        if self._is_version_valid(version, valid_at)
                    ]
                
                # Filter by source and confidence if specified
                if filter_by_source or min_confidence is not None:
                    current_version = self._get_current_version(fact)
                    if current_version:
                        if filter_by_source and current_version.get("source") not in [s.value for s in filter_by_source]:
                            continue
                        if min_confidence is not None and current_version.get("confidence", 0) < min_confidence:
                            continue
                
                # Filter deprecated versions if only_current
                if only_current:
                    fact["versions"] = [
                        version for version in fact.get("versions", [])
                        if not version.get("deprecated", False)
                    ]
                
                processed_facts.append(fact)
            
            logger.debug(f"Retrieved {len(processed_facts)} facts for user {user_id}")
            return processed_facts
            
        except Exception as e:
            logger.error(f"Failed to query facts for user {user_id}: {e}")
            return []
    
    # Fact extraction
    
    async def extract_facts_from_text(
        self,
        text: str,
        user_id: str,
        fact_types: Optional[List[str]] = None,
        min_confidence: float = 0.5,
        auto_save: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract facts from text using LLM.
        
        Args:
            text: Text to extract facts from
            user_id: User to associate facts with
            fact_types: Specific fact types to extract
            min_confidence: Minimum confidence for extracted facts
            auto_save: Automatically save extracted facts
            context: Additional context for extraction
            
        Returns:
            List of extracted facts
        """
        try:
            # TODO: Implement LLM-based fact extraction
            # For now, return empty list
            logger.info(f"Extracting facts from text for user {user_id}")
            
            extracted_facts = []
            
            if auto_save:
                for fact in extracted_facts:
                    await self.store_fact(
                        fact_id=f"extracted_{datetime.utcnow().timestamp()}",
                        user_id=user_id,
                        fact_type=fact["fact_type"],
                        key=fact["key"],
                        value=fact["value"],
                        confidence=fact["confidence"],
                        source=SourceType.INFERRED,
                        evidence=fact.get("evidence", [])
                    )
            
            return extracted_facts
            
        except Exception as e:
            logger.error(f"Failed to extract facts from text: {e}")
            return []
    
    # Helper methods
    
    async def _should_update_fact(
        self,
        existing_fact: Dict[str, Any],
        new_value: str,
        new_confidence: float,
        new_source: SourceType,
        force_update: bool
    ) -> bool:
        """
        Determine if fact should be updated based on conflict resolution rules.
        
        Args:
            existing_fact: Existing fact data
            new_value: New fact value
            new_confidence: New confidence level
            new_source: New source
            force_update: Force update flag
            
        Returns:
            True if fact should be updated
        """
        if force_update:
            return True
        
        # Get current version
        current_version = self._get_current_version(existing_fact)
        if not current_version:
            return True
        
        current_confidence = current_version.get("confidence", 0)
        current_source = current_version.get("source")
        
        # If values are the same, no need to update
        if current_version.get("value") == new_value:
            return False
        
        # Compare confidence levels
        if new_confidence > current_confidence:
            return True
        
        # If confidence is the same, prefer certain sources
        if new_confidence == current_confidence:
            source_priority = {
                SourceType.USER_STATED.value: 5,
                SourceType.OBSERVED.value: 4,
                SourceType.INFERRED.value: 3,
                SourceType.CONSOLIDATED.value: 2,
                SourceType.SYSTEM.value: 1
            }
            
            new_priority = source_priority.get(new_source.value, 0)
            current_priority = source_priority.get(current_source, 0)
            
            if new_priority > current_priority:
                return True
        
        return False
    
    def _get_current_version(self, fact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get current (non-deprecated) version of fact."""
        versions = fact.get("versions", [])
        for version in reversed(versions):  # Check newest first
            if not version.get("deprecated", False):
                return version
        return None
    
    def _is_version_valid(self, version: Dict[str, Any], valid_at: datetime) -> bool:
        """Check if version is valid at given time."""
        valid_from = version.get("valid_from")
        valid_until = version.get("valid_until")
        
        if valid_from and isinstance(valid_from, str):
            valid_from = datetime.fromisoformat(valid_from.replace('Z', '+00:00'))
        
        if valid_until and isinstance(valid_until, str):
            valid_until = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
        
        if valid_from and valid_at < valid_from:
            return False
        
        if valid_until and valid_at > valid_until:
            return False
        
        return True
    
    # Health and monitoring
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on facts service."""
        try:
            mongo_client = await self._get_mongo_client()
            mongo_health = await mongo_client.health_check()
            
            return {
                "service": "facts",
                "status": "healthy" if mongo_health["status"] == "healthy" else "unhealthy",
                "mongodb": mongo_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Facts service health check failed: {e}")
            return {
                "service": "facts",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get facts service metrics."""
        try:
            mongo_client = await self._get_mongo_client()
            
            # Get total facts count
            total_count = await mongo_client.count_documents("user_facts", {})
            
            # Get facts by type
            fact_type_counts = {}
            fact_types = ["personal", "location", "preference", "behavior", "relationship"]
            for fact_type in fact_types:
                count = await mongo_client.count_documents(
                    "user_facts",
                    {"fact_type": fact_type}
                )
                fact_type_counts[fact_type] = count
            
            # Get facts by source
            source_counts = {}
            for source in SourceType:
                count = await mongo_client.count_documents(
                    "user_facts",
                    {"versions.source": source.value}
                )
                source_counts[source.value] = count
            
            # Get high-confidence facts
            high_confidence_count = await mongo_client.count_documents(
                "user_facts",
                {"versions.confidence": {"$gte": 0.8}}
            )
            
            # Get recently updated facts
            recent_update_threshold = datetime.utcnow() - timedelta(days=7)
            recently_updated_count = await mongo_client.count_documents(
                "user_facts",
                {"last_updated": {"$gte": recent_update_threshold}}
            )
            
            return {
                "total_facts": total_count,
                "facts_by_type": fact_type_counts,
                "facts_by_source": source_counts,
                "high_confidence_facts": high_confidence_count,
                "recently_updated_facts": recently_updated_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get facts service metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    # Knowledge Graph Methods (Entities, Relations, Facts)

    async def create_entity(
        self,
        entity_id: str,
        entity_type: str,
        name: str,
        agent_id: str,
        attributes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an entity in the knowledge graph.

        Args:
            entity_id: Unique entity identifier
            entity_type: Type of entity (person, system, component, etc.)
            name: Entity name
            agent_id: Agent identifier
            attributes: Entity attributes
            metadata: Additional metadata

        Returns:
            Created entity ID
        """
        try:
            mongo_client = await self._get_mongo_client()

            entity_doc = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "name": name,
                "agent_id": agent_id,
                "attributes": attributes or {},
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            await mongo_client.insert_one("entities", entity_doc)

            logger.info(f"Created entity {entity_id} ({name})")
            return entity_id

        except Exception as e:
            logger.error(f"Failed to create entity {entity_id}: {e}")
            raise

    async def create_relation(
        self,
        source_entity_id: str,
        relation_type: str,
        target_entity_id: str,
        agent_id: str,
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0
    ) -> str:
        """
        Create a relation between entities.

        Args:
            source_entity_id: Source entity ID
            relation_type: Type of relation (uses, contains, etc.)
            target_entity_id: Target entity ID
            agent_id: Agent identifier
            properties: Relation properties
            confidence: Confidence level

        Returns:
            Created relation ID
        """
        try:
            mongo_client = await self._get_mongo_client()

            relation_id = f"{source_entity_id}_{relation_type}_{target_entity_id}"
            relation_doc = {
                "relation_id": relation_id,
                "source_entity_id": source_entity_id,
                "relation_type": relation_type,
                "target_entity_id": target_entity_id,
                "agent_id": agent_id,
                "properties": properties or {},
                "confidence": confidence,
                "created_at": datetime.utcnow()
            }

            await mongo_client.insert_one("relations", relation_doc)

            logger.info(f"Created relation: {source_entity_id} -> {relation_type} -> {target_entity_id}")
            return relation_id

        except Exception as e:
            logger.error(f"Failed to create relation: {e}")
            raise

    async def create_fact(
        self,
        entity_id: str,
        attribute: str,
        value: Any,
        agent_id: str,
        confidence: float = 1.0,
        source: str = "user"
    ) -> str:
        """
        Create a fact about an entity.

        Args:
            entity_id: Entity identifier
            attribute: Attribute name
            value: Attribute value
            agent_id: Agent identifier
            confidence: Confidence level
            source: Fact source

        Returns:
            Created fact ID
        """
        try:
            mongo_client = await self._get_mongo_client()

            fact_id = f"{entity_id}_{attribute}"
            fact_doc = {
                "fact_id": fact_id,
                "entity_id": entity_id,
                "attribute": attribute,
                "value": value,
                "agent_id": agent_id,
                "confidence": confidence,
                "source": source,
                "created_at": datetime.utcnow()
            }

            await mongo_client.insert_one("entity_facts", fact_doc)

            logger.info(f"Created fact: {entity_id}.{attribute} = {value}")
            return fact_id

        except Exception as e:
            logger.error(f"Failed to create fact: {e}")
            raise

    async def get_entity(
        self,
        entity_id: str,
        include_relations: bool = False,
        include_facts: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get entity with optional relations and facts.

        Args:
            entity_id: Entity identifier
            include_relations: Include related entities
            include_facts: Include entity facts

        Returns:
            Entity data or None
        """
        try:
            mongo_client = await self._get_mongo_client()

            entity = await mongo_client.find_one(
                "entities",
                {"entity_id": entity_id}
            )

            if not entity:
                return None

            entity["_id"] = str(entity["_id"])

            if include_relations:
                relations = await mongo_client.find_many(
                    "relations",
                    {"source_entity_id": entity_id}
                )
                entity["relations"] = relations

            if include_facts:
                facts = await mongo_client.find_many(
                    "entity_facts",
                    {"entity_id": entity_id}
                )
                entity["facts"] = facts

            return entity

        except Exception as e:
            logger.error(f"Failed to get entity {entity_id}: {e}")
            return None

    async def query_relations(
        self,
        agent_id: Optional[str] = None,
        source_entity_id: Optional[str] = None,
        relation_type: Optional[str] = None,
        target_entity_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query relations with filters.

        Args:
            agent_id: Filter by agent ID
            source_entity_id: Filter by source entity
            relation_type: Filter by relation type
            target_entity_id: Filter by target entity

        Returns:
            List of relations
        """
        try:
            mongo_client = await self._get_mongo_client()

            query = {}
            if agent_id:
                query["agent_id"] = agent_id
            if source_entity_id:
                query["source_entity_id"] = source_entity_id
            if relation_type:
                query["relation_type"] = relation_type
            if target_entity_id:
                query["target_entity_id"] = target_entity_id

            relations = await mongo_client.find_many("relations", query)

            for relation in relations:
                relation["_id"] = str(relation["_id"])

            return relations

        except Exception as e:
            logger.error(f"Failed to query relations: {e}")
            return []


# Alias for consistency with naming pattern
FactsMemoryService = FactsService
