import unittest
import asyncio
from agents.roi_calculator.main import ROICalculatorAgent
from agents.core.agent_base import AgentStatus

class TestROICalculatorAgent(unittest.TestCase):

    def setUp(self):
        """Set up the agent for testing."""
        self.agent = ROICalculatorAgent(agent_id="test-roi-agent", mcp_client=None, config={})

    def test_successful_roi_calculation(self):
        """Test a standard successful ROI calculation."""
        async def run_test():
            inputs = {'investment': 1000, 'gain': 1500}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertEqual(result.data['roi_percentage'], 50.0)

        asyncio.run(run_test())

    def test_zero_investment(self):
        """Test that an investment of zero results in a failure."""
        async def run_test():
            inputs = {'investment': 0, 'gain': 100}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.FAILED)
            self.assertEqual(result.data['error'], 'Investment must be a positive number.')

        asyncio.run(run_test())

    def test_negative_investment(self):
        """Test that a negative investment results in a failure."""
        async def run_test():
            inputs = {'investment': -100, 'gain': 100}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.FAILED)
            self.assertEqual(result.data['error'], 'Investment must be a positive number.')

        asyncio.run(run_test())

    def test_non_numeric_input(self):
        """Test that non-numeric inputs result in a failure."""
        async def run_test():
            inputs = {'investment': 'one thousand', 'gain': 1500}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.FAILED)
            self.assertIn("'investment' and 'gain' must be provided and must be numbers.", result.data['error'])

        asyncio.run(run_test())

    def test_invalid_input_type(self):
        """Test that the agent raises a TypeError for non-dictionary inputs."""
        async def run_test():
            with self.assertRaises(TypeError):
                await self.agent.execute("not a dict")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
