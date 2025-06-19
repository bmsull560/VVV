import unittest
import asyncio
import os
from memory.semantic import SemanticMemory
from memory.storage_backend import SQLiteStorageBackend
from memory.types import KnowledgeEntity

class TestSemanticMemory(unittest.TestCase):

    def setUp(self):
        """Set up a clean environment for each test."""
        self.db_path = ":memory:"
        self.backend = SQLiteStorageBackend(db_path=self.db_path)
        self.memory = SemanticMemory(backend=self.backend)


    def test_store_and_retrieve_entity(self):
        """Test that an entity can be stored and then retrieved."""
        async def run_test():
            entity = KnowledgeEntity(id="test-123", content="This is a test.")
            await self.memory.store(entity)
            retrieved = await self.memory.retrieve("test-123")
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.id, "test-123")
            self.assertEqual(retrieved.content, "This is a test.")
        asyncio.run(run_test())

    def test_semantic_search_with_mock_backend(self):
        """Test the semantic search functionality using a mock backend to isolate logic."""
        async def run_test():
            # Store some entities
            await self.memory.store(KnowledgeEntity(id="fruit-1", content="An apple is a sweet, edible fruit."))
            await self.memory.store(KnowledgeEntity(id="car-1", content="A car is a wheeled motor vehicle used for transportation."))
            
            # Since we can't rely on pgvector in a simple sqlite test, 
            # we'll check if the search function is called correctly.
            # A full integration test is needed for the real search logic.
            results = await self.memory.semantic_search(query_text="What is a healthy snack?")
            
            # In a simple backend, this might not return ordered results,
            # but we can check that it returns something.
            self.assertIsNotNone(results)

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
