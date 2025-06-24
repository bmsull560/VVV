"""
Specialized PostgreSQL storage backend for Episodic Memory using SQLAlchemy.
"""

import logging
import functools # New import
try:
    import orjson
except ImportError:
    import json
    class orjson:
        @staticmethod
        def dumps(v):
            return json.dumps(v).encode("utf-8")
        @staticmethod
        def loads(v):
            return json.loads(v)
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import delete as sqlalchemy_delete

from memory.storage_backend import StorageBackend
from memory.types import WorkflowMemoryEntity, from_dict, to_dict as global_to_dict
from memory.database_models import EpisodicMemoryEntry as EpisodicMemoryModel, Base

logger = logging.getLogger(__name__)

class EpisodicStorageBackend(StorageBackend):
    """
    A SQLAlchemy-based storage backend for persisting WorkflowMemoryEntity objects
    to a structured PostgreSQL table.
    """
    # Cache for search results (query: frozenset, limit: int -> List[WorkflowMemoryEntity])
    _search_cache: Dict[Any, List[WorkflowMemoryEntity]] = {}
    _search_cache_maxsize = 100 # Max items in search cache
    _search_cache_hits = 0
    _search_cache_misses = 0

    def __init__(self, dsn: str):
        """
        Initialize the PostgreSQL storage backend.
        
        Args:
            dsn: Database connection string (Data Source Name)
        """
        # For Supabase and other PostgreSQL services, we need to ensure SSL is enabled
        # when using asyncpg. The ssl=True parameter is required for secure connections.
        connect_args = {}
        if dsn.startswith("postgresql"):
            connect_args["ssl"] = True


        self._engine = create_async_engine(
            dsn,
            connect_args=connect_args
        )
        self._async_session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )
        # Clear caches on initialization
        self.clear_cache()

    def clear_cache(self):
        """Clears all internal caches."""
        self.retrieve.cache_clear()
        EpisodicStorageBackend._search_cache.clear()
        EpisodicStorageBackend._search_cache_hits = 0
        EpisodicStorageBackend._search_cache_misses = 0
        logger.info("EpisodicStorageBackend caches cleared.")

    async def initialize_schema(self):
        """Creates the necessary tables in the database."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _model_to_entity(self, model_instance: EpisodicMemoryModel) -> WorkflowMemoryEntity:
        """Converts a SQLAlchemy model instance to a WorkflowMemoryEntity dataclass."""
        entity_dict = {key: getattr(model_instance, key) for key in model_instance.__table__.columns.keys()}
        entity_dict['entity_type'] = WorkflowMemoryEntity.__name__ # Add entity_type for from_dict
        # The from_dict function expects enums and datetimes in specific formats
        entity_dict['created_at'] = model_instance.created_at.isoformat()
        entity_dict['updated_at'] = model_instance.updated_at.isoformat()
        entity_dict['start_time'] = model_instance.start_time.isoformat()
        if model_instance.end_time:
            entity_dict['end_time'] = model_instance.end_time.isoformat()

        return from_dict(entity_dict)

    async def store(self, entity: WorkflowMemoryEntity) -> str:
        """Stores a WorkflowMemoryEntity in the database."""
        if not isinstance(entity, WorkflowMemoryEntity):
            raise TypeError("EpisodicStorageBackend can only store WorkflowMemoryEntity objects")

        # Invalidate cache for this entity and any search results
        self.retrieve.cache_clear() # Clear retrieve cache for simplicity, or target specific ID
        EpisodicStorageBackend._search_cache.clear() # Clear search cache on any store operation
        EpisodicStorageBackend._search_cache_hits = 0
        EpisodicStorageBackend._search_cache_misses = 0

        entity_dict = global_to_dict(entity) # Use global to_dict to include entity_type
        # SQLAlchemy model expects python objects, not serialized strings
        entity_dict['created_at'] = entity.created_at
        entity_dict['updated_at'] = entity.updated_at
        entity_dict['start_time'] = entity.start_time
        entity_dict['end_time'] = entity.end_time

        # Remove fields from dict that are not in the model
        model_fields = {c.name for c in EpisodicMemoryModel.__table__.columns}
        filtered_dict = {k: v for k, v in entity_dict.items() if k in model_fields}

        new_entry = EpisodicMemoryModel(**filtered_dict)

        async with self._async_session() as session:
            async with session.begin():
                session.add(new_entry)
            await session.commit()
        logger.info(f"Stored episodic memory entry {entity.id} for workflow {entity.workflow_id}")
        return entity.id

    async def retrieve(self, entity_id: str) -> Optional[WorkflowMemoryEntity]:
        """Retrieves a workflow entity by its ID."""
        async with self._async_session() as session:
            stmt = select(EpisodicMemoryModel).where(EpisodicMemoryModel.id == entity_id)
            result = await session.execute(stmt)
            model_instance = result.scalar_one_or_none()

        if model_instance:
            logger.info(f"Retrieved episodic memory entry {entity_id}")
            return self._model_to_entity(model_instance)
        else:
            logger.warning(f"Episodic memory entry {entity_id} not found")
            return None

    async def delete(self, entity_id: str) -> bool:
        """Deletes a workflow entity by its ID."""
        # Invalidate cache for this entity and any search results
        self.retrieve.cache_clear() # Clear retrieve cache for simplicity, or target specific ID
        EpisodicStorageBackend._search_cache.clear() # Clear search cache on any delete operation
        EpisodicStorageBackend._search_cache_hits = 0
        EpisodicStorageBackend._search_cache_misses = 0

        async with self._async_session() as session:
            stmt = sqlalchemy_delete(EpisodicMemoryModel).where(EpisodicMemoryModel.id == entity_id)
            result = await session.execute(stmt)
            await session.commit()

        if result.rowcount > 0:
            logger.info(f"Deleted episodic memory entry {entity_id}")
            return True
        else:
            logger.warning(f"Attempted to delete non-existent episodic entry {entity_id}")
            return False

    async def search(self, query: Dict[str, Any], limit: int = 10) -> List[WorkflowMemoryEntity]:
        """Searches for workflow entities based on a dictionary of criteria."""
        # Convert query dict to a hashable key for caching
        cache_key = (frozenset(query.items()), limit)

        if cache_key in EpisodicStorageBackend._search_cache:
            EpisodicStorageBackend._search_cache_hits += 1
            logger.info(f"Search cache hit for query: {query}")
            return EpisodicStorageBackend._search_cache[cache_key]

        EpisodicStorageBackend._search_cache_misses += 1
        logger.info(f"Search cache miss for query: {query}")

        async with self._async_session() as session:
            stmt = select(EpisodicMemoryModel)
            for key, value in query.items():
                if hasattr(EpisodicMemoryModel, key):
                    stmt = stmt.where(getattr(EpisodicMemoryModel, key) == value)
            
            stmt = stmt.limit(limit)
            result = await session.execute(stmt)
            model_instances = result.scalars().all()

        logger.info(f"Search found {len(model_instances)} episodic entries for query: {query}")
        entities = [self._model_to_entity(inst) for inst in model_instances]

        # Store in cache, managing max size
        if len(EpisodicStorageBackend._search_cache) >= EpisodicStorageBackend._search_cache_maxsize:
            # Simple eviction: remove the oldest (arbitrary) item
            EpisodicStorageBackend._search_cache.pop(next(iter(EpisodicStorageBackend._search_cache)))
        EpisodicStorageBackend._search_cache[cache_key] = entities

        return entities
