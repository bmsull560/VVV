from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import json
import asyncpg
import logging

from memory.types import from_dict, MemoryEntity, to_dict as global_to_dict

logger = logging.getLogger(__name__)

class StorageBackend(ABC):
    """
    Abstract base class for pluggable memory storage backends.
    Implementations must provide async CRUD operations.
    """
    @abstractmethod
    async def store(self, entity: Any) -> str:
        pass

    @abstractmethod
    async def retrieve(self, entity_id: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        pass

    @abstractmethod
    async def search(self, query: Dict[str, Any], limit: int = 10) -> List[Any]:
        pass

class SQLiteStorageBackend(StorageBackend):
    """
    SQLite-based backend for persistent storage.
    This is a minimal scaffold for demonstration and extension.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    async def connect(self):
        if self.conn:
            return
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            data TEXT
        )''')

    async def store(self, entity: Any) -> str:
        await self.connect()
        import json
        self.conn.execute(
            'REPLACE INTO entities (id, data) VALUES (?, ?)',
            (entity.id, json.dumps(global_to_dict(entity)))
        )
        self.conn.commit()
        return entity.id

    async def retrieve(self, entity_id: str) -> Optional[MemoryEntity]:
        await self.connect()
        cursor = self.conn.execute('SELECT data FROM entities WHERE id=?', (entity_id,))
        row = cursor.fetchone()
        if row:
            import json
            return from_dict(json.loads(row[0]))
        return None

    async def delete(self, entity_id: str) -> bool:
        await self.connect()
        cur = self.conn.execute('DELETE FROM entities WHERE id=?', (entity_id,))
        self.conn.commit()
        return cur.rowcount > 0

    async def search(self, query: Dict[str, Any], limit: int = 10) -> List[MemoryEntity]:
        await self.connect()
        # This is a stub: for demo, return all entities (real impl should filter by query)
        cursor = self.conn.execute('SELECT data FROM entities LIMIT ?', (limit,))
        import json
        return [from_dict(json.loads(row[0])) for row in cursor.fetchall()]




class PostgreSQLStorageBackend(StorageBackend):
    """
    PostgreSQL-based backend for persistent storage using asyncpg.
    """
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Establishes the connection pool and creates table if not exists."""
        if self._pool and not self._pool._closed:
            logger.info("PostgreSQL connection pool already established.")
            return
        try:
            self._pool = await asyncpg.create_pool(self._dsn)
            if self._pool is None: # Should not happen if create_pool doesn't raise
                 raise ConnectionError("Failed to create PostgreSQL connection pool: pool is None.")
            # Ensure entities table exists
            async with self._pool.acquire() as connection:
                await connection.execute('CREATE EXTENSION IF NOT EXISTS vector;')
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS entities (
                        id TEXT PRIMARY KEY,
                        data JSONB,
                        vector vector(384)
                    )
                ''')
            logger.info("PostgreSQL connection pool established and 'entities' table verified.")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL or create table: {e}")
            self._pool = None # Ensure pool is None if connection failed
            raise

    async def close(self):
        """Closes the connection pool."""
        if self._pool and not self._pool._closed:
            await self._pool.close()
            logger.info("PostgreSQL connection pool closed.")
        self._pool = None

    async def _get_pool(self) -> asyncpg.Pool:
        if not self._pool or self._pool._closed:
            logger.warning("PostgreSQL connection pool not initialized or closed. Attempting to reconnect.")
            await self.connect()
        if not self._pool: # Still None after connect attempt
             raise ConnectionError("PostgreSQL connection pool is not available.")
        return self._pool

    async def store(self, entity: MemoryEntity) -> str:
        pool = await self._get_pool()
        entity_data_dict = global_to_dict(entity)
        
        # Extract vector embedding and remove it from the main JSONB data to avoid duplication
        vector = entity_data_dict.pop('vector_embedding', None)

        async with pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO entities (id, data, vector) VALUES ($1, $2, $3)
                ON CONFLICT (id) DO UPDATE SET 
                    data = EXCLUDED.data,
                    vector = EXCLUDED.vector
                """,
                entity.id,
                entity_data_dict,
                vector
            )
        return entity.id

    async def retrieve(self, entity_id: str) -> Optional[MemoryEntity]:
        pool = await self._get_pool()
        async with pool.acquire() as connection:
            row = await connection.fetchrow(
                'SELECT data, vector FROM entities WHERE id = $1',
                entity_id
            )
        
        if row and row['data']:
            # asyncpg automatically decodes JSONB to a Python dict
            entity = from_dict(row['data'])
            if entity:
                # Manually add the vector embedding back to the entity
                # asyncpg returns pgvector data as a string, so we parse it.
                vector_str = row['vector']
                if vector_str:
                    entity.vector_embedding = json.loads(vector_str)
                else:
                    entity.vector_embedding = None
            return entity
        return None

    async def delete(self, entity_id: str) -> bool:
        pool = await self._get_pool()
        async with pool.acquire() as connection:
            result = await connection.execute(
                'DELETE FROM entities WHERE id = $1',
                entity_id
            )
        # result is a string like 'DELETE 1' or 'DELETE 0'
        return result.startswith('DELETE') and result != 'DELETE 0'

    async def clear_all_entities(self):
        """Clears all entities from the storage for testing purposes."""
        pool = await self._get_pool()
        async with pool.acquire() as connection:
            await connection.execute('DELETE FROM entities')
        logger.info("Cleared all entities from PostgreSQL backend.")

    async def search(self, query: Dict[str, Any], limit: int = 10, offset: int = 0) -> List[MemoryEntity]:
        """
        Searches for entities. If a 'vector' key is present in the query,
        it performs a semantic search. Otherwise, it performs a metadata search.
        """
        pool = await self._get_pool()
        
        query_vector = query.get("vector")
        
        if query_vector:
            # Perform vector similarity search
            async with pool.acquire() as connection:
                # The vector is passed as a string representation of a list
                vector_str = str(query_vector)
                rows = await connection.fetch(
                    """
                    SELECT data, vector, vector <=> $1 AS distance
                    FROM entities
                    ORDER BY distance
                    LIMIT $2 OFFSET $3
                    """,
                    vector_str, limit, offset
                )
        else:
            # Fallback to simple metadata search (or the previous stub)
            logger.warning(f"Performing non-vector search. Query: {query}")
            async with pool.acquire() as connection:
                rows = await connection.fetch(
                    'SELECT data, vector FROM entities ORDER BY id LIMIT $1 OFFSET $2',
                    limit, offset
                )
                
        results = []
        for row in rows:
            if row['data']:
                entity = from_dict(row['data'])
                if entity:
                    vector_str = row['vector']
                    if vector_str:
                        entity.vector_embedding = json.loads(vector_str)
                    else:
                        entity.vector_embedding = None
                    results.append(entity)
        return results

