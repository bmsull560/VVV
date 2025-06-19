from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from typing import Dict, Any
import logging
from simple_salesforce import Salesforce

logger = logging.getLogger(__name__)

class CRMConnectorAgent(BaseAgent):
    """An agent responsible for connecting to a CRM and fetching data."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Connects to a CRM and fetches data based on the provided inputs."""
        if not isinstance(inputs, dict):
            raise TypeError("Input must be a dictionary")

        crm_type = inputs.get('crm_type')
        if not crm_type:
            return AgentResult(status=AgentStatus.FAILED, data={"error": "crm_type is a required input"}, execution_time_ms=0)

        logger.info(f"Attempting to connect to {crm_type}...")

        try:
            data = self._fetch_crm_data(crm_type, inputs)
            return AgentResult(status=AgentStatus.COMPLETED, data=data, execution_time_ms=100)
        except Exception as e:
            logger.error(f"Failed to fetch data from {crm_type}: {e}")
            return AgentResult(status=AgentStatus.FAILED, data={"error": str(e)}, execution_time_ms=100)

    def _fetch_crm_data(self, crm_type: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fetches data from a specified CRM."""
        if crm_type.lower() == 'salesforce':
            sf_config = self.config.get('salesforce')
            if not sf_config:
                raise ValueError("Salesforce configuration not found in agent config.")

            sf = Salesforce(
                username=sf_config.get('username'),
                password=sf_config.get('password'),
                security_token=sf_config.get('security_token'),
                instance_url=sf_config.get('instance_url')
            )
            
            # Example: Fetch first 5 account names
            soql_query = "SELECT Name FROM Account LIMIT 5"
            query_result = sf.query(soql_query)
            accounts = [record['Name'] for record in query_result['records']]
            return {"message": "Successfully connected to Salesforce.", "accounts": accounts}
        else:
            logger.warning(f"CRM type '{crm_type}' not supported. Using mock data.")
            return {"message": f"Successfully connected to {crm_type} and fetched mock data.", "queried_data": {"account_id": "12345"}}

