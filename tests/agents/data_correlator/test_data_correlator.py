import unittest
import asyncio
from agents.data_correlator.main import DataCorrelatorAgent
from agents.core.agent_base import AgentStatus

class TestDataCorrelatorAgent(unittest.TestCase):

    def setUp(self):
        """Set up the agent for testing."""
        self.agent = DataCorrelatorAgent(agent_id="test-correlator-agent", mcp_client=None, config={})

    def test_positive_correlation(self):
        """Test a strong positive correlation."""
        async def run_test():
            inputs = {'dataset1': [1, 2, 3, 4, 5], 'dataset2': [2, 3, 4, 5, 6]}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertAlmostEqual(result.data['correlation_coefficient'], 1.0, places=4)

        asyncio.run(run_test())

    def test_negative_correlation(self):
        """Test a strong negative correlation."""
        async def run_test():
            inputs = {'dataset1': [1, 2, 3, 4, 5], 'dataset2': [5, 4, 3, 2, 1]}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertAlmostEqual(result.data['correlation_coefficient'], -1.0, places=4)

        asyncio.run(run_test())

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        async def run_test():
            inputs = {'dataset1': [1, 2, 3, 4, 5], 'dataset2': [1, -1, 1, -1, 1]}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertAlmostEqual(result.data['correlation_coefficient'], 0.0, places=4)

        asyncio.run(run_test())

    def test_mismatched_lengths(self):
        """Test that datasets with mismatched lengths fail."""
        async def run_test():
            inputs = {'dataset1': [1, 2, 3], 'dataset2': [1, 2]}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.FAILED)
            self.assertEqual(result.data['error'], 'Datasets must be of equal length.')

        asyncio.run(run_test())

    def test_empty_datasets(self):
        """Test that empty datasets fail."""
        async def run_test():
            inputs = {'dataset1': [], 'dataset2': []}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.FAILED)
            self.assertEqual(result.data['error'], 'Datasets cannot be empty.')

        asyncio.run(run_test())

    def test_non_numeric_data(self):
        """Test that non-numeric data fails."""
        async def run_test():
            inputs = {'dataset1': [1, 'a', 3], 'dataset2': [1, 2, 3]}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.FAILED)
            self.assertEqual(result.data['error'], 'Datasets must contain only numerical values.')

        asyncio.run(run_test())

    def test_zero_variance(self):
        """Test that a dataset with zero variance returns a correlation of 0."""
        async def run_test():
            inputs = {'dataset1': [1, 1, 1, 1, 1], 'dataset2': [1, 2, 3, 4, 5]}
            result = await self.agent.execute(inputs)
            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertEqual(result.data['correlation_coefficient'], 0.0)

        asyncio.run(run_test())

    def test_invalid_input_type(self):
        """Test that the agent raises a TypeError for non-dictionary inputs."""
        async def run_test():
            with self.assertRaises(TypeError):
                await self.agent.execute("not a dict")

        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
