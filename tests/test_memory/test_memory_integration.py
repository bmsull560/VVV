import unittest
import asyncio
import os
from memory.semantic import SemanticMemory
from memory.storage_backend import PostgreSQLStorageBackend, SQLiteStorageBackend
from memory.types import KnowledgeEntity

class TestMemoryIntegration(unittest.TestCase):

    def setUp(self):
        """Set up the backend based on environment variables."""
        self.postgres_dsn = os.getenv('TEST_POSTGRES_DSN', '').replace('+asyncpg', '')
        if self.postgres_dsn:
            self.backend = PostgreSQLStorageBackend(dsn=self.postgres_dsn)
        else:
            self.backend = SQLiteStorageBackend(db_path=":memory:")
        
        self.memory = SemanticMemory(backend=self.backend)
        
        async def init_db():
            if hasattr(self.backend, 'connect'):
                await self.backend.connect()
            # Clear previous test data if any
            if hasattr(self.backend, '_pool'): # Check if it's Postgres
                async with self.backend._pool.acquire() as conn:
                    await conn.execute('TRUNCATE TABLE entities')

        asyncio.run(init_db())

    def test_store_and_retrieve(self):
        """Test storing and retrieving an entity from the backend."""
        async def run_test():
            entity = KnowledgeEntity(id="integ-test-1", content="Integration test content.")
            await self.memory.store(entity)
            retrieved = await self.memory.retrieve("integ-test-1")
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.id, "integ-test-1")
        asyncio.run(run_test())

    @unittest.skipIf(not os.getenv('TEST_POSTGRES_DSN'), "PostgreSQL DSN not set, skipping vector search test.")
    def test_semantic_search_with_pgvector(self):
        """Test end-to-end semantic search with pgvector."""
        async def run_test():
            await self.memory.store(KnowledgeEntity(id="tech-1", content="Kubernetes is an open-source container orchestration system."))
            await self.memory.store(KnowledgeEntity(id="food-1", content="A banana is an elongated, edible fruit."))

            # This query should be closer to Kubernetes than a banana
            results = await self.memory.semantic_search("What is a container orchestrator?")

            self.assertGreater(len(results), 0)
            self.assertEqual(results[0].id, "tech-1")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
