"""
Types and enumerations for the B2BValue Memory Architecture.
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import uuid


class DataSensitivity(Enum):
    """Defines sensitivity levels for data in memory system."""
    PUBLIC = auto()       # Can be shared freely
    INTERNAL = auto()     # Internal to organization
    RESTRICTED = auto()   # Limited access within organization
    CONFIDENTIAL = auto() # Highly sensitive business data
    
    
class MemoryAccess(Enum):
    """Defines access control levels for memory entities."""
    READ = auto()
    WRITE = auto()
    DELETE = auto()
    ADMIN = auto()


class MemoryTier(Enum):
    """Defines the tier/layer where memory is stored."""
    WORKING = auto()  # Ephemeral, in-memory during workflow
    EPISODIC = auto() # Persisted workflow histories
    SEMANTIC = auto() # Long-term knowledge
    GRAPH = auto()    # Relationship data


@dataclass
class MemoryEntity:
    """Base class for all memory entities in the system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    creator_id: str = field(default="system")
    sensitivity: DataSensitivity = field(default=DataSensitivity.INTERNAL)
    tier: MemoryTier = field(default=MemoryTier.WORKING)
    ttl: Optional[int] = field(default=None)  # Time to live in seconds
    entry_metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: int = field(default=1)
    checksum: Optional[str] = field(default=None)  # For integrity verification
    access_policy: Optional[List[Dict[str, Any]]] = field(default=None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        result = {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "creator_id": self.creator_id,
            "sensitivity": self.sensitivity.name if isinstance(self.sensitivity, DataSensitivity) else self.sensitivity,
            "tier": self.tier.name if isinstance(self.tier, MemoryTier) else self.tier,
            "version": self.version,
            "entry_metadata": self.entry_metadata,
            "tags": self.tags,
        }
        
        if self.ttl is not None:
            result["ttl"] = self.ttl
        
        if self.checksum is not None:
            result["checksum"] = self.checksum
            
        return result


@dataclass
class ContextMemoryEntity(MemoryEntity):
    """Represents a context object in working memory."""
    context_data: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = field(default=None)
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stage_id: Optional[str] = field(default=None)
    agent_id: Optional[str] = field(default=None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        result = super().to_dict()
        result.update({
            "context_data": self.context_data,
            "workflow_id": self.workflow_id,
        })
        
        if self.parent_id is not None:
            result["parent_id"] = self.parent_id
            
        if self.stage_id is not None:
            result["stage_id"] = self.stage_id
            
        if self.agent_id is not None:
            result["agent_id"] = self.agent_id
            
        return result


@dataclass
class WorkflowMemoryEntity(MemoryEntity):
    """Represents a complete workflow execution history."""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str = field(default="Unnamed Workflow")
    workflow_status: str = field(default="created")
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    user_id: Optional[str] = None
    customer_id: Optional[str] = None
    context_versions: List[str] = field(default_factory=list)  # List of context entity IDs
    stages: List[Dict[str, Any]] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        result = super().to_dict()
        result.update({
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "workflow_status": self.workflow_status,
            "start_time": self.start_time.isoformat(),
            "context_versions": self.context_versions,
            "stages": self.stages,
        })
        
        if self.end_time is not None:
            result["end_time"] = self.end_time.isoformat()
            
        if self.result is not None:
            result["result"] = self.result
            
        if self.user_id is not None:
            result["user_id"] = self.user_id
            
        if self.customer_id is not None:
            result["customer_id"] = self.customer_id
            
        return result


@dataclass
class KnowledgeEntity(MemoryEntity):
    """Represents a knowledge item in semantic memory."""
    title: str = field(default="")
    content: str = field(default="")
    content_type: str = field(default="text")
    vector_embedding: Optional[List[float]] = None
    source: str = field(default="system")
    confidence: float = field(default=1.0)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        result = super().to_dict()
        result.update({
            "content": self.content,
            "content_type": self.content_type,
            "source": self.source,
            "confidence": self.confidence,
            "references": self.references,
            "metadata": self.metadata,
        })
        
        if self.vector_embedding is not None:
            result["vector_embedding"] = self.vector_embedding
            
        return result


@dataclass
class RelationshipEntity(MemoryEntity):
    """Represents a relationship between entities in the knowledge graph."""
    from_id: str = field(default="")
    to_id: str = field(default="")
    relation_type: str = field(default="related_to")
    strength: float = field(default=1.0)
    bidirectional: bool = field(default=False)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        result = super().to_dict()
        result.update({
            "from_id": self.from_id,
            "to_id": self.to_id,
            "relation_type": self.relation_type,
            "strength": self.strength,
            "bidirectional": self.bidirectional,
            "properties": self.properties,
        })
        return result


@dataclass
class MemoryAccessControl:
    """Defines access control for memory entities."""
    entity_id: str
    roles: Dict[str, List[MemoryAccess]]
    user_overrides: Dict[str, List[MemoryAccess]] = field(default_factory=dict)
    
    def can_access(self, user_id: str, role: str, access_type: MemoryAccess) -> bool:
        """Check if a user with a given role can access entity with specified access type."""
        # Check user-specific overrides first
        if user_id in self.user_overrides and access_type in self.user_overrides[user_id]:
            return True
            
        # Then check role-based permissions
        return role in self.roles and access_type in self.roles[role]


@dataclass
class AuditLogEntry:
    """Represents an entry in the audit log."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    entity_id: str = field(default="")
    action: str = field(default="") # e.g., 'create', 'update', 'delete', 'read'
    user_id: str = field(default="system")
    details: Dict[str, Any] = field(default_factory=dict)
    prev_checksum: Optional[str] = field(default=None)
    new_checksum: Optional[str] = field(default=None)

def to_dict(entity: MemoryEntity) -> Dict[str, Any]:
    """Serialize a MemoryEntity object to a dictionary."""
    d = entity.to_dict()
    d['entity_type'] = entity.__class__.__name__
    return d

import logging
logger = logging.getLogger(__name__)

def from_dict(data: Dict[str, Any]) -> Optional[MemoryEntity]:
    """Deserialize a dictionary into a MemoryEntity object."""
    entity_id_for_log = data.get('id', 'Unknown ID')
    entity_type_for_log = data.get('entity_type', 'Unknown Type')
    logger.info(f"from_dict: Attempting to deserialize entity ID: {entity_id_for_log}, Type: {entity_type_for_log}. Raw data: {data}")

    entity_type = data.get("entity_type")

    entity_class_map = {
        "MemoryEntity": MemoryEntity,
        "ContextMemoryEntity": ContextMemoryEntity,
        "KnowledgeEntity": KnowledgeEntity,
        "WorkflowMemoryEntity": WorkflowMemoryEntity,
        "RelationshipEntity": RelationshipEntity,
        "AuditLogEntry": AuditLogEntry,
        "AccessControlPolicy": MemoryAccessControl,
    }

    entity_class = entity_class_map.get(entity_type)
    logger.debug(f"from_dict (ID: {entity_id_for_log}): Resolved entity_type '{entity_type}' to class {entity_class}")

    if not entity_class:
        logger.warning(f"from_dict (ID: {entity_id_for_log}): No entity class found for type '{entity_type}'. Returning None.")
        return None

    # Operate on a copy to avoid modifying the input dict for logging purposes if something goes wrong
    constructor_data = data.copy()
    # Pop entity_type as it's not a constructor argument for all classes and not part of MemoryEntity itself
    constructor_data.pop('entity_type', None) 

    # Convert enum strings back to enums
    if 'tier' in constructor_data and isinstance(constructor_data['tier'], str):
        try:
            constructor_data['tier'] = MemoryTier[constructor_data['tier']]
        except KeyError:
            logger.error(f"from_dict (ID: {entity_id_for_log}): Invalid MemoryTier value '{constructor_data['tier']}'.")
            return None
    if 'sensitivity' in constructor_data and isinstance(constructor_data['sensitivity'], str):
        try:
            constructor_data['sensitivity'] = DataSensitivity[constructor_data['sensitivity']]
        except KeyError:
            logger.error(f"from_dict (ID: {entity_id_for_log}): Invalid DataSensitivity value '{constructor_data['sensitivity']}'.")
            return None
    if 'action' in constructor_data and isinstance(constructor_data['action'], str):
        # This field is specific to AuditLogEntry, check entity_type if necessary for context
        try:
            constructor_data['action'] = MemoryAccess[constructor_data['action']]
        except KeyError:
            logger.error(f"from_dict (ID: {entity_id_for_log}, Type: {entity_type_for_log}): Invalid MemoryAccess value for 'action' field '{constructor_data['action']}'.")
            return None
    
    # Convert timestamps from ISO format strings to datetime objects
    for key in ['created_at', 'updated_at', 'timestamp', 'start_time', 'end_time']:
        if key in constructor_data and constructor_data[key] and isinstance(constructor_data[key], str):
            try:
                constructor_data[key] = datetime.fromisoformat(constructor_data[key])
            except ValueError as e:
                logger.error(f"from_dict (ID: {entity_id_for_log}): Invalid ISO date format for key '{key}' value '{constructor_data[key]}': {e}")
                return None

    # Filter out keys that are not in the entity's constructor
    import inspect
    sig = inspect.signature(entity_class)
    valid_keys = {p.name for p in sig.parameters.values()}
    filtered_data = {k: v for k, v in constructor_data.items() if k in valid_keys}
    logger.info(f"from_dict (ID: {entity_id_for_log}, Class: {entity_class.__name__}): Filtered data for constructor: {filtered_data}")

    # Log keys present in constructor_data but not in valid_keys (i.e., filtered out)
    unexpected_keys = set(constructor_data.keys()) - valid_keys
    if unexpected_keys:
        logger.debug(f"from_dict (ID: {entity_id_for_log}, Class: {entity_class.__name__}): Keys filtered out (not in constructor): {unexpected_keys}")

    try:
        instance = entity_class(**filtered_data)
        logger.info(f"from_dict (ID: {entity_id_for_log}): Successfully created instance of {entity_class.__name__}: {instance.id if hasattr(instance, 'id') else 'N/A'}")
        return instance
    except TypeError as e:
        logger.error(f"from_dict (ID: {entity_id_for_log}, Class: {entity_class.__name__}): TypeError during instantiation: {e}. Filtered data: {filtered_data}. Constructor signature: {list(sig.parameters.keys())}")
        return None
    except Exception as e:
        logger.error(f"from_dict (ID: {entity_id_for_log}, Class: {entity_class.__name__}): Unexpected error during instantiation: {e}. Filtered data: {filtered_data}")
        return None
