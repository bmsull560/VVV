from ..core.agent_base import BaseAgent, AgentResult, AgentStatus
from typing import Dict, Any
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class DatabaseConnectorAgent(BaseAgent):
    """An agent for managing database connections, pooling, and failover."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)
        self.engine = None
        self._initialize_engine()

    def _initialize_engine(self):
        """Initializes the SQLAlchemy engine from config."""
        db_config = self.config.get('database')
        if not db_config or not db_config.get('url'):
            logger.warning("Database URL not configured for this agent.")
            return

        try:
            # In a production setup, you would configure pooling options here
            # e.g., pool_size, max_overflow, pool_timeout, etc.
            self.engine = create_engine(db_config['url'])
            logger.info("Database engine initialized.")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database engine: {e}")
            self.engine = None

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Executes a database operation, such as testing the connection or running a query."""
        action = inputs.get('action', 'test_connection')

        if not self.engine:
            return AgentResult(status=AgentStatus.FAILED, data={"error": "Database engine not initialized."}, execution_time_ms=0)

        if action == 'test_connection':
            return self._test_connection()
        elif action == 'run_query':
            return self._run_query(inputs)
        else:
            return AgentResult(status=AgentStatus.FAILED, data={"error": f"Unsupported action: {action}"}, execution_time_ms=0)

    def _test_connection(self) -> AgentResult:
        """Tests the database connection."""
        try:
            with self.engine.connect() as connection:
                logger.info("Database connection successful.")
                return AgentResult(status=AgentStatus.COMPLETED, data={"message": "Connection successful"}, execution_time_ms=100)
        except SQLAlchemyError as e:
            logger.error(f"Database connection failed: {e}")
            return AgentResult(status=AgentStatus.FAILED, data={"error": str(e)}, execution_time_ms=100)

    def _run_query(self, inputs: Dict[str, Any]) -> AgentResult:
        """Runs a given SQL query."""
        query = inputs.get('query')
        if not query:
            return AgentResult(status=AgentStatus.FAILED, data={"error": "Query not provided"}, execution_time_ms=0)

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                # Note: This is a simplified result handling. A real implementation
                # would need to handle different query types (SELECT, INSERT, etc.)
                # and serialize the results properly.
                data = [row._asdict() for row in result]
                return AgentResult(status=AgentStatus.COMPLETED, data={"result": data}, execution_time_ms=200)
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            return AgentResult(status=AgentStatus.FAILED, data={"error": str(e)}, execution_time_ms=200)
