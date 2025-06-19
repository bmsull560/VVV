import unittest
import asyncio
from unittest.mock import patch, MagicMock
from agents.database_connector.main import DatabaseConnectorAgent
from agents.core.agent_base import AgentStatus
from sqlalchemy.exc import SQLAlchemyError

class TestDatabaseConnectorAgent(unittest.TestCase):

    @patch('agents.database_connector.main.create_engine')
    def test_initialization_success(self, mock_create_engine):
        """Test successful initialization of the database engine."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        config = {'database': {'url': 'postgresql://user:pass@host/db'}}
        agent = DatabaseConnectorAgent(agent_id="test-db-agent", mcp_client=None, config=config)

        self.assertIsNotNone(agent.engine)
        mock_create_engine.assert_called_once_with('postgresql://user:pass@host/db')

    def test_initialization_no_config(self):
        """Test initialization when no database config is provided."""
        agent = DatabaseConnectorAgent(agent_id="test-db-agent", mcp_client=None, config={})
        self.assertIsNone(agent.engine)

    @patch('agents.database_connector.main.create_engine')
    def test_connection_success(self, mock_create_engine):
        """Test a successful database connection test."""
        async def run_test():
            mock_engine = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = MagicMock()
            mock_create_engine.return_value = mock_engine

            config = {'database': {'url': 'postgresql://user:pass@host/db'}}
            agent = DatabaseConnectorAgent(agent_id="test-db-agent", mcp_client=None, config=config)

            result = await agent.execute({'action': 'test_connection'})

            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertEqual(result.data['message'], 'Connection successful')
        
        asyncio.run(run_test())

    @patch('agents.database_connector.main.create_engine')
    def test_connection_failure(self, mock_create_engine):
        """Test a failed database connection test."""
        async def run_test():
            mock_engine = MagicMock()
            mock_engine.connect.side_effect = SQLAlchemyError("Connection failed")
            mock_create_engine.return_value = mock_engine

            config = {'database': {'url': 'postgresql://user:pass@host/db'}}
            agent = DatabaseConnectorAgent(agent_id="test-db-agent", mcp_client=None, config=config)

            result = await agent.execute({'action': 'test_connection'})

            self.assertEqual(result.status, AgentStatus.FAILED)
            self.assertIn('Connection failed', result.data['error'])

        asyncio.run(run_test())

    @patch('agents.database_connector.main.create_engine')
    def test_run_query_success(self, mock_create_engine):
        """Test successfully running a query."""
        async def run_test():
            mock_connection = MagicMock()
            mock_result = MagicMock()
            mock_result.__iter__.return_value = [MagicMock(_asdict=lambda: {'id': 1})]
            mock_connection.execute.return_value = mock_result
            
            mock_engine = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            mock_create_engine.return_value = mock_engine

            config = {'database': {'url': 'postgresql://user:pass@host/db'}}
            agent = DatabaseConnectorAgent(agent_id="test-db-agent", mcp_client=None, config=config)

            result = await agent.execute({'action': 'run_query', 'query': 'SELECT 1'})

            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertEqual(result.data['result'], [{'id': 1}])
        
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()

