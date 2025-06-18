import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from src.agents.intake_assistant.main import IntakeAssistantAgent
from src.agents.core.agent_base import AgentStatus

class TestIntakeAssistantAgent(unittest.TestCase):

    def setUp(self):
        """Set up a mock MCPClient and the agent for testing."""
        self.mock_mcp_client = MagicMock()
        self.mock_mcp_client.store_knowledge = AsyncMock()
        self.agent = IntakeAssistantAgent(agent_id="test-intake-agent", mcp_client=self.mock_mcp_client, config={})

    def test_successful_intake(self):
        """Test the successful processing of a valid project intake."""
        async def run_test():
            inputs = {
                'project_name': 'New CRM Integration',
                'description': 'Integrating our new CRM with the sales pipeline.',
                'goals': ['Improve lead tracking', 'Automate sales reports']
            }
            result = await self.agent.execute(inputs)

            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertEqual(result.data['message'], 'Project intake successful')
            self.assertTrue(result.data['entity_id'].startswith('proj_'))

            self.mock_mcp_client.store_knowledge.assert_called_once()
            call_args = self.mock_mcp_client.store_knowledge.call_args[1]
            self.assertEqual(call_args['title'], 'New CRM Integration')
            self.assertIn('Integrating our new CRM', call_args['content'])
            self.assertIn('Improve lead tracking', call_args['content'])

        asyncio.run(run_test())

    def test_missing_fields(self):
        """Test that the agent fails if required fields are missing."""
        async def run_test():
            inputs = {'project_name': 'Incomplete Project'}
            result = await self.agent.execute(inputs)

            self.assertEqual(result.status, AgentStatus.FAILED)
            self.assertIn('Missing required fields', result.data['error'])
            self.assertIn('description', result.data['error'])
            self.assertIn('goals', result.data['error'])
            self.mock_mcp_client.store_knowledge.assert_not_called()

        asyncio.run(run_test())

    def test_invalid_input_type(self):
        """Test that the agent raises a TypeError for non-dictionary inputs."""
        async def run_test():
            with self.assertRaises(TypeError):
                await self.agent.execute("this is not a dict")
        
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
