"""
Core Memory Manager for B2BValue Memory Architecture.

This module provides the central orchestrator for all memory tiers:
- Working Memory (ephemeral context)
- Episodic Memory (workflow history)
- Semantic Memory (knowledge store)
- Knowledge Graph (entity relationships)

The MemoryManager enforces security, compliance, and data governance policies.
"""

import logging
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple, Union, Type
from datetime import datetime, timezone
import asyncio



from memory.memory_types import (
    MemoryEntity, ContextMemoryEntity, WorkflowMemoryEntity, 
    KnowledgeEntity, RelationshipEntity, MemoryTier,
    DataSensitivity, MemoryAccess, MemoryAccessControl, AuditLogEntry
)

# Configure logging
logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Central orchestrator for the B2BValue Memory Architecture.
    
    This class manages all memory tiers and provides a unified interface
    for storing, retrieving, and managing memory entities across the system.
    """
    
    def __init__(self):
        """Initialize the memory manager with all memory tier handlers."""
        self._working_memory = None  # Will be set when modules are loaded
        self._episodic_memory = None
        self._semantic_memory = None
        self._knowledge_graph = None
        self._audit_log = []
        self._access_controls: Dict[str, MemoryAccessControl] = {}
        
    def initialize(self, working_memory=None, episodic_memory=None, 
                  semantic_memory=None, knowledge_graph=None):
        """Initialize memory tier handlers."""
        from memory.working import WorkingMemory
        from memory.episodic import EpisodicMemory
        from memory.semantic import SemanticMemory
        from memory.storage_backend import SQLiteStorageBackend
        from memory.knowledge_graph import KnowledgeGraph
        
        # Instantiate memory tiers
        self._working_memory = working_memory or WorkingMemory()
        self._episodic_memory = episodic_memory or EpisodicMemory()
        self._semantic_memory = semantic_memory or SemanticMemory(backend=SQLiteStorageBackend(db_path=":memory:"))
        self._knowledge_graph = knowledge_graph or KnowledgeGraph()
        
        # Explicitly initialize tiers that require it (e.g., for I/O)
        if self._working_memory:
            self._working_memory.initialize()
        if self._episodic_memory:
            self._episodic_memory.initialize()
        if self._semantic_memory:
            self._semantic_memory.initialize()
        if self._knowledge_graph:
            self._knowledge_graph.initialize()
        
        logger.info("Memory Manager initialized with all tiers")

    def set_default_access_control(self, control_key: str, control_object: MemoryAccessControl):
        """
        Sets a default access control configuration.

        Args:
            control_key: The key for this access control (e.g., role name).
            control_object: The MemoryAccessControl object.
        """
        self._access_controls[control_key] = control_object
        logger.info(f"Default access control set for '{control_key}'.")
    
    def _calculate_checksum(self, entity: MemoryEntity) -> str:
        """Calculate a cryptographic checksum for a memory entity."""
        # Convert entity to JSON string representation
        entity_dict = entity.to_dict()
        # Remove existing checksum if present to avoid circular reference
        if 'checksum' in entity_dict:
            del entity_dict['checksum']
            
        # Sort keys to ensure consistent serialization
        entity_json = json.dumps(entity_dict, sort_keys=True)
        # Calculate SHA-256 hash
        return hashlib.sha256(entity_json.encode('utf-8')).hexdigest()
    
    def _log_audit_event(self, entity_id: str, action: str, 
                        user_id: str, details: Dict[str, Any],
                        prev_checksum: Optional[str] = None,
                        new_checksum: Optional[str] = None):
        """Log an audit event for a memory operation."""
        audit_entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            details=details,
            prev_checksum=prev_checksum,
            new_checksum=new_checksum
        )
        self._audit_log.append(audit_entry)
        
        # In production, this would write to a secure audit log store
        logger.info(f"Audit: {action} on {entity_id} by {user_id}")
    
    def _check_access(self, entity_id: Optional[str], user_id: str, 
                     role: str, access_type: MemoryAccess) -> bool:
        """Check if user has required access to memory entity."""
        if entity_id is None:
            # This is a tier-level check (e.g., for search).
            # For now, we'll grant read access to admins and agents.
            # A more robust system would have configurable tier-level ACLs.
            if role in ["admin", "agent"] and access_type == MemoryAccess.READ:
                return True
            return False

        if entity_id not in self._access_controls:
            # Default to restricted if no specific ACL is defined for the entity
            logger.warning(f"No access control found for entity {entity_id}. Access denied.")
            return False
            
        return self._access_controls[entity_id].can_access(user_id, role, access_type)

    def _validate_entity(self, entity: MemoryEntity):
        """Validate entity fields and types according to schema."""
        # Basic type and required field checks for all entities
        if not hasattr(entity, 'id') or not isinstance(entity.id, str):
            raise ValueError("Entity must have string 'id'")
        if not hasattr(entity, 'created_at'):
            raise ValueError("Entity must have 'created_at' timestamp")
        if not hasattr(entity, 'updated_at'):
            raise ValueError("Entity must have 'updated_at' timestamp")
        if not hasattr(entity, 'creator_id') or not isinstance(entity.creator_id, str):
            raise ValueError("Entity must have string 'creator_id'")
        if not hasattr(entity, 'sensitivity'):
            raise ValueError("Entity must have 'sensitivity'")
        if not hasattr(entity, 'tier'):
            raise ValueError("Entity must have 'tier'")

        if isinstance(entity, ContextMemoryEntity):
            if not hasattr(entity, 'workflow_id') or not isinstance(entity.workflow_id, str):
                raise ValueError("Context must have workflow_id as str")
            if not hasattr(entity, 'version') or not isinstance(entity.version, int):
                raise ValueError("Context must have version as int")
            if not hasattr(entity, 'context_data') or not isinstance(entity.context_data, dict):
                raise ValueError("Context must have context_data as dict")
        elif isinstance(entity, WorkflowMemoryEntity):
            if not hasattr(entity, 'workflow_id') or not isinstance(entity.workflow_id, str):
                raise ValueError("Workflow must have workflow_id as str")
            if not hasattr(entity, 'workflow_name') or not isinstance(entity.workflow_name, str):
                raise ValueError("Workflow must have workflow_name as str")
            if not hasattr(entity, 'workflow_status') or not isinstance(entity.workflow_status, str):
                raise ValueError("Workflow must have workflow_status as str")
            if not hasattr(entity, 'start_time'):
                raise ValueError("Workflow must have start_time")
        elif isinstance(entity, KnowledgeEntity):
            if not hasattr(entity, 'content') or not isinstance(entity.content, str):
                raise ValueError("Knowledge must have content as str")
            if not hasattr(entity, 'content_type') or not isinstance(entity.content_type, str):
                raise ValueError("Knowledge must have content_type as str")
            if not hasattr(entity, 'source') or not isinstance(entity.source, str):
                raise ValueError("Knowledge must have source as str")
            if not hasattr(entity, 'confidence') or not isinstance(entity.confidence, float):
                raise ValueError("Knowledge must have confidence as float")
            if not hasattr(entity, 'references') or not isinstance(entity.references, list):
                raise ValueError("Knowledge must have references as list")
        elif isinstance(entity, RelationshipEntity):
            if not hasattr(entity, 'from_id') or not isinstance(entity.from_id, str):
                raise ValueError("Relationship must have from_id as str")
            if not hasattr(entity, 'to_id') or not isinstance(entity.to_id, str):
                raise ValueError("Relationship must have to_id as str")
            if not hasattr(entity, 'relation_type') or not isinstance(entity.relation_type, str):
                raise ValueError("Relationship must have relation_type as str")
            if not hasattr(entity, 'strength') or not isinstance(entity.strength, float):
                raise ValueError("Relationship must have strength as float")
            if not hasattr(entity, 'bidirectional') or not isinstance(entity.bidirectional, bool):
                raise ValueError("Relationship must have bidirectional as bool")
            if not hasattr(entity, 'properties') or not isinstance(entity.properties, dict):
                raise ValueError("Relationship must have properties as dict")
        # Add more entity-type checks as needed
        # (See docs/entity_schemas.md for full schema)
    
    def set_access_control(self, access_control: MemoryAccessControl):
        """Set access control for a memory entity."""
        self._access_controls[access_control.entity_id] = access_control
    
    async def store(self, entity: MemoryEntity, user_id: str = "system", 
                  role: str = "admin") -> str:
        """
        Store an entity in the appropriate memory tier.
        
        Args:
            entity: The memory entity to store
            user_id: ID of user performing the operation
            role: Role of the user
            
        Returns:
            str: ID of the stored entity
            
        Raises:
            PermissionError: If user lacks write access
        """
        # For new entities, no access check is needed
        is_new = not entity.id or entity.id not in self._access_controls
        
        if not is_new and not self._check_access(
            entity.id, user_id, role, MemoryAccess.WRITE
        ):
            raise PermissionError(f"User {user_id} with role {role} lacks write access to entity {entity.id}")
            
        # Validate entity before storing
        self._validate_entity(entity)  # Validate entity schema
        
        try:
            # Calculate checksum for integrity verification
            entity.updated_at = datetime.now(timezone.utc)
            prev_checksum = entity.checksum
            entity.checksum = self._calculate_checksum(entity)
            # Store in appropriate memory tier
            if entity.tier == MemoryTier.WORKING:
                entity_id = await self._working_memory.store(entity)
            elif entity.tier == MemoryTier.EPISODIC:
                entity_id = await self._episodic_memory.store(entity)
            elif entity.tier == MemoryTier.SEMANTIC:
                entity_id = await self._semantic_memory.store(entity)
            elif entity.tier == MemoryTier.GRAPH:
                entity_id = await self._knowledge_graph.store(entity)
            else:
                raise ValueError(f"Unknown memory tier: {entity.tier}")
            # Log audit event
            self._log_audit_event(
                entity_id=entity_id,
                action="store",
                user_id=user_id,
                details={"tier": entity.tier.name},
                prev_checksum=prev_checksum,
                new_checksum=entity.checksum
            )
            # Setup default access control if this is a new entity
            if is_new:
                if hasattr(entity, 'access_policy') and entity.access_policy:
                    # Use the policy defined on the entity itself
                    roles = {}
                    user_overrides = {}
                    for rule in entity.access_policy:
                        access_enums = [MemoryAccess[a.upper()] for a in rule.get("access", [])]
                        if "role" in rule:
                            roles[rule["role"]] = access_enums
                        elif "user_id" in rule and rule["user_id"]:
                            user_overrides[rule["user_id"]] = access_enums
                    
                    # Ensure admin always has full access
                    roles["admin"] = list(MemoryAccess)

                    access_control = MemoryAccessControl(
                        entity_id=entity_id,
                        roles=roles,
                        user_overrides=user_overrides
                    )
                else:
                    # Fallback to the old default behavior if no policy is provided
                    new_entity_roles = {"admin": list(MemoryAccess)}
                    for acl_key, role_default_acl_obj in self._access_controls.items():
                        if acl_key.startswith("role:"):
                            for role_name_from_default, permissions_from_default in role_default_acl_obj.roles.items():
                                if role_name_from_default not in new_entity_roles:
                                    new_entity_roles[role_name_from_default] = []
                                for perm in permissions_from_default:
                                    if perm not in new_entity_roles[role_name_from_default]:
                                        new_entity_roles[role_name_from_default].append(perm)
                                        
                    access_control = MemoryAccessControl(
                        entity_id=entity_id,
                        roles=new_entity_roles
                    )
                self.set_access_control(access_control)
            logger.info(f"STORE: Entity {entity_id} stored in tier {entity.tier.name} by {user_id}")
            return entity_id
        except Exception as e:
            logger.error(f"STORE ERROR: Failed to store entity {getattr(entity, 'id', 'unknown')} in tier {getattr(entity, 'tier', 'unknown')}: {e}")
            # Log critical errors for alerting
            logger.critical(f"CRITICAL STORE ERROR: {e}")
            raise
        
    async def retrieve(self, entity_id: str, tier: MemoryTier,
                     user_id: str = "system", role: str = "admin") -> Optional[MemoryEntity]:
        """
        Retrieve a memory entity by ID from the specified tier.
        
        Args:
            entity_id: ID of the entity to retrieve
        """
        try:
            if not self._check_access(entity_id, user_id, role, MemoryAccess.READ):
                logger.warning(f"User {user_id} with role {role} denied READ access to entity {entity_id}")
                raise PermissionError(f"User {user_id} with role {role} lacks read access to entity {entity_id}")
            # Retrieve from appropriate tier
            if tier == MemoryTier.WORKING:
                entity = await self._working_memory.retrieve(entity_id)
            elif tier == MemoryTier.EPISODIC:
                entity = await self._episodic_memory.retrieve(entity_id)
            elif tier == MemoryTier.SEMANTIC:
                entity = await self._semantic_memory.retrieve(entity_id)
            elif tier == MemoryTier.GRAPH:
                entity = await self._knowledge_graph.retrieve(entity_id)
            else:
                raise ValueError(f"Unknown memory tier: {tier}")
            logger.info(f"RETRIEVE: Entity {entity_id} from tier {tier.name} by {user_id}")
            return entity
        except Exception as e:
            logger.error(f"RETRIEVE ERROR: Failed to retrieve entity {entity_id} from tier {tier.name}: {e}")
            logger.critical(f"CRITICAL RETRIEVE ERROR: {e}")
            raise
    
    async def search(self, query: Dict[str, Any], tier: MemoryTier,
                   user_id: str = "system", role: str = "admin", limit: int = 10) -> List[MemoryEntity]:
        """Search for memory entities by query and tier. Logs all search activity for monitoring."""
        try:
            if not self._check_access(None, user_id, role, MemoryAccess.READ):
                logger.warning(f"User {user_id} with role {role} denied READ access to tier {tier.name}")
                raise PermissionError(f"User {user_id} with role {role} lacks read access to tier {tier.name}")
            # Search in appropriate tier
            if tier == MemoryTier.WORKING:
                results = await self._working_memory.search(query, limit=limit)
            elif tier == MemoryTier.EPISODIC:
                results = await self._episodic_memory.search(query, limit=limit)
            elif tier == MemoryTier.SEMANTIC:
                results = await self._semantic_memory.search(query, limit=limit)
            elif tier == MemoryTier.GRAPH:
                results = await self._knowledge_graph.search(query, limit=limit)
            else:
                raise ValueError(f"Unknown memory tier: {tier}")
            logger.info(f"SEARCH: Query {query} in tier {tier.name} by {user_id}, {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"SEARCH ERROR: Failed to search in tier {tier.name}: {e}")
            logger.critical(f"CRITICAL SEARCH ERROR: {e}")
            raise
    
    async def delete(self, entity_id: str, tier: MemoryTier,
                   user_id: str = "system", role: str = "admin") -> bool:
        """
        Delete a memory entity by ID from the specified tier. Logs all delete activity for monitoring/alerting.
        """
        try:
            if not self._check_access(entity_id, user_id, role, MemoryAccess.DELETE):
                logger.warning(f"User {user_id} with role {role} denied DELETE access to entity {entity_id}")
                raise PermissionError(f"User {user_id} with role {role} lacks delete access to entity {entity_id}")
            # Get entity for audit trail before deletion
            entity = await self.retrieve(entity_id, tier, user_id, role)
            if not entity:
                return False
            # Delete from appropriate memory tier
            if tier == MemoryTier.WORKING:
                success = await self._working_memory.delete(entity_id)
            elif tier == MemoryTier.EPISODIC:
                success = await self._episodic_memory.delete(entity_id)
            elif tier == MemoryTier.SEMANTIC:
                success = await self._semantic_memory.delete(entity_id)
            elif tier == MemoryTier.GRAPH:
                success = await self._knowledge_graph.delete(entity_id)
            else:
                raise ValueError(f"Unknown memory tier: {tier}")
            if success:
                # Log audit event
                self._log_audit_event(
                    entity_id=entity_id,
                    action="delete",
                    user_id=user_id,
                    details={"tier": tier.name, "entity_type": type(entity).__name__}
                )
                # Remove access controls
                if entity_id in self._access_controls:
                    del self._access_controls[entity_id]
            logger.info(f"DELETE: Entity {entity_id} from tier {tier.name} by {user_id}")
            return success
        except Exception as e:
            logger.error(f"DELETE ERROR: Failed to delete entity {entity_id} from tier {tier.name}: {e}")
            logger.critical(f"CRITICAL DELETE ERROR: {e}")
            raise
        self._log_audit_event(
            entity_id="search",
            action="search",
            user_id=user_id,
            details={"tier": tier.name, "query": query, "result_count": len(filtered_results)}
        )
            
        return filtered_results
    
    async def semantic_search(self, text: str, limit: int = 10,
                            user_id: str = "system", role: str = "admin") -> List[KnowledgeEntity]:
        """
        Perform semantic search on knowledge entities.
        
        Args:
            text: Text to search for semantically similar content
            limit: Maximum number of results
            user_id: ID of user performing the operation
            role: Role of the user
            
        Returns:
            List[KnowledgeEntity]: Semantically similar entities
        """
        results = await self._semantic_memory.semantic_search(text, limit)
        
        # Filter by access control
        filtered_results = []
        for entity in results:
            if self._check_access(entity.id, user_id, role, MemoryAccess.READ):
                filtered_results.append(entity)
                
        # Log audit event
        self._log_audit_event(
            entity_id="semantic_search",
            action="semantic_search",
            user_id=user_id,
            details={"query": text, "result_count": len(filtered_results)}
        )
            
        return filtered_results
    
    async def get_context_history(self, workflow_id: str, 
                                user_id: str = "system", 
                                role: str = "admin") -> List[ContextMemoryEntity]:
        """
        Get the history of context changes for a workflow.
        
        Args:
            workflow_id: ID of the workflow
            user_id: ID of user performing the operation
            role: Role of the user
            
        Returns:
            List[ContextMemoryEntity]: Context history
        """
        # Search for context entities belonging to workflow
        query = {"workflow_id": workflow_id}
        context_entities = await self._working_memory.search(query)
        
        # Filter by access control
        filtered_results = []
        for entity in context_entities:
            if self._check_access(entity.id, user_id, role, MemoryAccess.READ):
                filtered_results.append(entity)
                
        # Sort by version number
        filtered_results.sort(key=lambda e: e.version)
        
        return filtered_results
    
    async def get_workflow_history(self, customer_id: Optional[str] = None,
                                 user_id: str = "system",
                                 role: str = "admin",
                                 limit: int = 10,
                                 offset: int = 0) -> List[WorkflowMemoryEntity]:
        """
        Get workflow execution history.
        
        Args:
            customer_id: Optional filter for specific customer
            user_id: ID of user performing the operation
            role: Role of the user
            
        Returns:
            List[WorkflowMemoryEntity]: Workflow history
        """
        # Construct query
        query = {}
        if customer_id:
            query["customer_id"] = customer_id
            
        # Get workflow history
        workflows = await self._episodic_memory.search(query, limit, offset)
        
        # Filter by access control
        filtered_results = []
        for entity in workflows:
            if self._check_access(entity.id, user_id, role, MemoryAccess.READ):
                filtered_results.append(entity)
                
        return filtered_results
    
    async def get_entity_relationships(self, entity_id: str,
                                     user_id: str = "system",
                                     role: str = "admin") -> List[RelationshipEntity]:
        """
        Get relationships for a specific entity.
        
        Args:
            entity_id: ID of the entity
            user_id: ID of user performing the operation
            role: Role of the user
            
        Returns:
            List[RelationshipEntity]: Relationships
        """
        if not self._check_access(entity_id, user_id, role, MemoryAccess.READ):
            raise PermissionError(f"User {user_id} with role {role} lacks read access to entity {entity_id}")
            
        # Get relationships
        return await self._knowledge_graph.get_entity_relationships(entity_id)
    
    async def get_audit_log(self, entity_id: Optional[str] = None,
                          user_id: Optional[str] = None,
                          action: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None) -> List[AuditLogEntry]:
        """
        Get audit log entries matching the filters.
        
        Args:
            entity_id: Optional filter for specific entity
            user_id: Optional filter for specific user
            action: Optional filter for specific action
            start_time: Optional filter for start time
            end_time: Optional filter for end time
            
        Returns:
            List[AuditLogEntry]: Matching audit log entries
        """
        # In production, this would query a secure audit log database
        # Here we filter the in-memory audit log
        filtered_log = self._audit_log
        
        if entity_id:
            filtered_log = [entry for entry in filtered_log if entry.entity_id == entity_id]
            
        if user_id:
            filtered_log = [entry for entry in filtered_log if entry.user_id == user_id]
            
        if action:
            filtered_log = [entry for entry in filtered_log if entry.action == action]
            
        if start_time:
            filtered_log = [entry for entry in filtered_log if entry.timestamp >= start_time]
            
        if end_time:
            filtered_log = [entry for entry in filtered_log if entry.timestamp <= end_time]
            
        return filtered_log
