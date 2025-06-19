import unittest
import os
import asyncio
from agents.core.mcp_client import MCPClient
from memory.core import MemoryManager
from memory.types import KnowledgeEntity, MemoryTier
from datetime import datetime, timezone

class TestAgentMemoryIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mm = MemoryManager()
        self.mm.initialize()
        self.mcp = MCPClient(self.mm)

    @unittest.skipIf(not os.getenv('TEST_POSTGRES_DSN'), "PostgreSQL DSN not set, skipping integration test.")
    async def test_agent_store_and_search_knowledge(self):
        entity = KnowledgeEntity(
            id="agent-know-1",
            content="AI agent integration test.",
            content_type="text",
            creator_id="agent",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            sensitivity=None,
            tier=MemoryTier.SEMANTIC
        )
        # Create and store the knowledge entity
        knowledge_id = await self.mcp.store_knowledge(
            title="AI Agent Integration Test",
            content="This is a test of the AI agent's ability to store knowledge.",
            content_type="text/plain",
            source="integration_test"
        )
        results = await self.mcp.semantic_search("integration test", limit=1)
        self.assertTrue(any("integration test" in r.content or "AI agent" in r.content for r in results))

if __name__ == "__main__":
    unittest.main()
