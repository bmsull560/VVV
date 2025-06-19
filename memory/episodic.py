"""
Episodic Memory for B2BValue Memory Architecture.

This module implements the Episodic Memory tier, which provides
persistent storage for completed workflow execution histories using a 
PostgreSQL backend.
"""

import logging
from typing import Dict, Any, List, Optional

from memory.types import WorkflowMemoryEntity
from memory.episodic_storage_backend import EpisodicStorageBackend

logger = logging.getLogger(__name__)

class EpisodicMemory:
    """
    Episodic Memory implementation - stores complete workflow execution histories
    for audit, analysis, and learning purposes.

    This implementation uses a dedicated PostgreSQL backend via the EpisodicStorageBackend.
    """
    
    def __init__(self, dsn: str):
        """
        Initialize episodic memory store.

        Args:
            dsn: The Data Source Name for connecting to the PostgreSQL database.
        """
        self._backend = EpisodicStorageBackend(dsn)
        self._initialized = False
        logger.info("EpisodicMemory instance created. Call initialize() to connect to the database.")

    async def initialize(self):
        """Initializes the storage backend. Must be called before use."""
        if self._initialized:
            return

        try:
            # The schema initialization can be handled by a separate migration tool/script
            # but providing a method for it can be useful for testing or initial setup.
            # For production, migrations should be run manually.
            # await self._backend.initialize_schema() 
            logger.info("Episodic Memory initialized with PostgreSQL backend.")
            self._initialized = True
        except Exception as e:
            logger.error(f"Could not initialize PostgreSQL backend for Episodic Memory: {e}")
            raise
    
    async def store(self, entity: WorkflowMemoryEntity) -> str:
        """
        Store a workflow entity in episodic memory.
        
        Args:
            entity: The workflow entity to store
            
        Returns:
            str: ID of the stored entity
        """
        if not self._initialized:
            raise RuntimeError("EpisodicMemory must be initialized before use.")
        return await self._backend.store(entity)
    
    async def retrieve(self, entity_id: str) -> Optional[WorkflowMemoryEntity]:
        """
        Retrieve a workflow entity from episodic memory.
        
        Args:
            entity_id: ID of the entity to retrieve
            
        Returns:
            Optional[WorkflowMemoryEntity]: The retrieved entity or None if not found
        """
        if not self._initialized:
            raise RuntimeError("EpisodicMemory must be initialized before use.")
        return await self._backend.retrieve(entity_id)
    
    async def delete(self, entity_id: str) -> bool:
        """
        Delete a workflow entity from episodic memory.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        if not self._initialized:
            raise RuntimeError("EpisodicMemory must be initialized before use.")
        return await self._backend.delete(entity_id)

    async def search(self, query: Dict[str, Any], limit: int = 10) -> List[WorkflowMemoryEntity]:
        """
        Search for workflow entities in episodic memory.
        
        Args:
            query: A dictionary of search criteria.
            limit: The maximum number of results to return.
            
        Returns:
            List[WorkflowMemoryEntity]: A list of matching workflow entities.
        """
        if not self._initialized:
            raise RuntimeError("EpisodicMemory must be initialized before use.")
        return await self._backend.search(query, limit)
