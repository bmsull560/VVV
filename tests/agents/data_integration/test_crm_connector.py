import unittest
import asyncio
from unittest.mock import patch, MagicMock
from agents.data_integration.crm_connector import CRMConnectorAgent
from agents.core.agent_base import AgentStatus

class TestCRMConnectorAgent(unittest.TestCase):

    def setUp(self):
        """Set up a mock agent for testing."""
        self.agent = CRMConnectorAgent(agent_id="test-crm-agent", mcp_client=None, config={})

    def test_execute_non_salesforce_crm(self):
        """Test successful execution with a non-Salesforce CRM to ensure mock path works."""
        async def run_test():
            inputs = {"crm_type": "hubspot"}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertIn("message", result.data)
            self.assertEqual(result.data["queried_data"]["account_id"], "12345")
        asyncio.run(run_test())

    @patch('agents.data_integration.crm_connector.Salesforce')
    def test_salesforce_integration_success(self, mock_salesforce):
        """Test successful execution with a mocked Salesforce connection."""
        async def run_test():
            mock_sf_instance = MagicMock()
            mock_sf_instance.query.return_value = {
                'records': [{'Name': 'Test Account 1'}, {'Name': 'Test Account 2'}]
            }
            mock_salesforce.return_value = mock_sf_instance

            config = {
                'salesforce': {
                    'username': 'testuser',
                    'password': 'testpass',
                    'security_token': 'token123',
                    'instance_url': 'https://test.salesforce.com'
                }
            }
            agent = CRMConnectorAgent(agent_id="test-sf-agent", mcp_client=None, config=config)

            inputs = {"crm_type": "salesforce"}
            result = await agent.execute(inputs)

            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertEqual(result.data['accounts'], ['Test Account 1', 'Test Account 2'])

            mock_salesforce.assert_called_once_with(
                username='testuser',
                password='testpass',
                security_token='token123',
                instance_url='https://test.salesforce.com'
            )
            mock_sf_instance.query.assert_called_once_with("SELECT Name FROM Account LIMIT 5")
        asyncio.run(run_test())

    def test_execute_missing_crm_type(self):
        """Test that the agent fails if crm_type is not provided."""
        async def run_test():
            inputs = {}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.FAILED)
            self.assertEqual(result.data["error"], "crm_type is a required input")
        asyncio.run(run_test())

    def test_execute_invalid_input_type(self):
        """Test that the agent raises a TypeError for non-dictionary inputs."""
        async def run_test():
            with self.assertRaises(TypeError):
                await self.agent.execute("not_a_dict")
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()

