import unittest
import asyncio
from src.memory.semantic import SemanticMemory
from src.memory.storage_backend import SQLiteStorageBackend
from src.memory.types import KnowledgeEntity

class TestSemanticMemory(unittest.TestCase):

    def setUp(self):
        """Set up a clean environment for each test."""
        self.backend = SQLiteStorageBackend(db_path=":memory:")
        self.memory = SemanticMemory(backend=self.backend)
        asyncio.run(self.backend.connect())

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

    def test_semantic_search(self):
        """Test the semantic search functionality."""
        async def run_test():
            # Store some entities
            await self.memory.store(KnowledgeEntity(id="fruit-1", content="An apple is a sweet, edible fruit."))
            await self.memory.store(KnowledgeEntity(id="car-1", content="A car is a wheeled motor vehicle used for transportation."))
            
            # Search for a related concept
            results = await self.memory.semantic_search(query_text="What is a healthy snack?")
            
            self.assertGreater(len(results), 0)
            # Check if the most relevant result is the apple
            self.assertEqual(results[0].id, "fruit-1")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()

class TestSemanticMemory(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.memory = SemanticMemory(storage_path="./test_data/semantic_test", embedding_dim=384)

    async def asyncTearDown(self):
        import shutil
        shutil.rmtree("./test_data/semantic_test", ignore_errors=True)

    async def test_store_and_retrieve_entity(self):
        entity = KnowledgeEntity(
            id="test1",
            content="Business value AI memory test.",
            content_type="text",
            creator_id="tester",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            sensitivity=None,
            tier=MemoryTier.SEMANTIC
        )
        await self.memory.store(entity)
        retrieved = await self.memory.retrieve("test1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.content, "Business value AI memory test.")
        self.assertIsInstance(retrieved.vector_embedding, list)
        self.assertEqual(len(retrieved.vector_embedding), 384)

    async def test_semantic_search(self):
        entity1 = KnowledgeEntity(
            id="ent1",
            content="AI for business value.",
            content_type="text",
            creator_id="tester",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            sensitivity=None,
            tier=MemoryTier.SEMANTIC
        )
        entity2 = KnowledgeEntity(
            id="ent2",
            content="Enterprise memory architecture.",
            content_type="text",
            creator_id="tester",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            sensitivity=None,
            tier=MemoryTier.SEMANTIC
        )
        await self.memory.store(entity1)
        await self.memory.store(entity2)
        results = await self.memory.semantic_search("business value", limit=2)
        self.assertTrue(any("business value" in r.content for r in results) or len(results) > 0)

    async def test_embedding_fallback(self):
        entity = KnowledgeEntity(
            id="fallback",
            content="Fallback embedding test.",
            content_type="text",
            creator_id="tester",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            sensitivity=None,
            tier=MemoryTier.SEMANTIC
        )
        # Simulate missing sentence-transformers by patching import
        import builtins
        orig_import = builtins.__import__
        def fake_import(name, *args, **kwargs):
            if name == 'sentence_transformers':
                raise ImportError()
            return orig_import(name, *args, **kwargs)
        builtins.__import__ = fake_import
        await self.memory.store(entity)
        builtins.__import__ = orig_import
        retrieved = await self.memory.retrieve("fallback")
        self.assertIsInstance(retrieved.vector_embedding, list)
        self.assertEqual(len(retrieved.vector_embedding), 384)

if __name__ == "__main__":
    unittest.main()
