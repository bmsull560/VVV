"""
PostgreSQL storage backend implementation.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, JSON

from src.memory.storage_backend import StorageBackend
from src.memory.types import MemoryEntity, to_dict, from_dict

logger = logging.getLogger(__name__)

Base = declarative_base()

class EntityStore(Base):
    __tablename__ = 'entities'
    id = Column(String, primary_key=True)
    data = Column(JSON)

class PostgreSQLStorageBackend(StorageBackend):
    """
    A storage backend that uses PostgreSQL for persistence.
    """

    def __init__(self, db_url: str):
        self._engine = create_async_engine(db_url)
        self._async_session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    async def initialize(self):
        """Create the necessary tables in the database."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL backend initialized and tables created.")

    async def store(self, entity: MemoryEntity) -> str:
        """Store an entity in the database."""
        async with self._async_session() as session:
            async with session.begin():
                entity_data = to_dict(entity)
                stmt = text("""
                    INSERT INTO entities (id, data)
                    VALUES (:id, :data)
                    ON CONFLICT (id) DO UPDATE SET data = :data;
                """)
                await session.execute(stmt, {"id": entity.id, "data": json.dumps(entity_data)})
            await session.commit()
        return entity.id

    async def retrieve(self, entity_id: str) -> Optional[MemoryEntity]:
        """Retrieve an entity from the database."""
        async with self._async_session() as session:
            stmt = text("SELECT data FROM entities WHERE id = :id")
            result = await session.execute(stmt, {"id": entity_id})
            row = result.fetchone()
            if row:
                return from_dict(json.loads(row[0]))
        return None

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity from the database."""
        async with self._async_session() as session:
            stmt = text("DELETE FROM entities WHERE id = :id")
            result = await session.execute(stmt, {"id": entity_id})
            await session.commit()
            return result.rowcount > 0

    async def search(self, query: Dict[str, Any], limit: int = 10) -> List[MemoryEntity]:
        """Search for entities in the database."""
        # This is a simplified search. A real implementation would need more complex JSONB queries.
        async with self._async_session() as session:
            # Example of a simple key-value search on the JSON data
            where_clauses = []
            params = {}
            # For more efficient JSONB querying, use the @> operator with a JSONB query.
            # Consider adding a GIN index on the 'data' column for optimal performance:
            # CREATE INDEX idx_entities_data_gin ON entities USING GIN (data jsonb_path_ops);
            query_jsonb = json.dumps(query)
            stmt_str = f"SELECT data FROM entities WHERE data @> :query_jsonb LIMIT :limit"
            params = {"query_jsonb": query_jsonb, "limit": limit}

            stmt = text(stmt_str)
            result = await session.execute(stmt, params)
            return [from_dict(json.loads(row[0])) for row in result.fetchall()]
