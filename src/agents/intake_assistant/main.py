import logging
from typing import Dict, Any
import uuid

from ..core.agent_base import BaseAgent, AgentResult, AgentStatus
from ...memory.types import KnowledgeEntity

logger = logging.getLogger(__name__)

class IntakeAssistantAgent(BaseAgent):
    """Processes initial user input to structure and store project information."""

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Takes raw user input, validates it, and stores it as a KnowledgeEntity.

        Args:
            inputs: A dictionary containing project data, expected to have keys
                    like 'project_name', 'description', and 'goals'.
        """
        if not isinstance(inputs, dict):
            raise TypeError("Input must be a dictionary")

        project_name = inputs.get('project_name')
        description = inputs.get('description')
        goals = inputs.get('goals')

        if not all([project_name, description, goals]):
            missing = [k for k, v in {'project_name': project_name, 'description': description, 'goals': goals}.items() if not v]
            error_msg = f"Missing required fields: {', '.join(missing)}"
            logger.error(error_msg)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_msg}, execution_time_ms=0)

        try:
            entity_id = f"proj_{uuid.uuid4()}"
            content = f"Project Description: {description}\nGoals: {', '.join(goals)}"

            await self.mcp_client.store_knowledge(
                title=project_name,
                content=content,
                content_type='text/plain',
                source='IntakeAssistant'
            )

            logger.info(f"Successfully created and stored knowledge for project: {project_name}")
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data={"message": "Project intake successful", "entity_id": entity_id},
                execution_time_ms=150
            )
        except Exception as e:
            logger.exception(f"Failed to store knowledge for project '{project_name}': {e}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": str(e)},
                execution_time_ms=150
            )

import os
import asyncio
from typing import Dict, Any
from src.agents.core.agent_base import LLMAgent, MCPClient, AgentResult

class IntakeAssistantAgent(LLMAgent):
    """
    An agent responsible for gathering initial user input and extracting key business context.
    """

    def __init__(self, agent_definition_path: str, mcp_client: MCPClient, config: Dict[str, Any]):
        self.definition = self._load_definition(agent_definition_path)
        agent_id = self.definition.get('agent_id', 'intake_assistant')
        super().__init__(agent_id, mcp_client, config)
        print(f"Successfully initialized agent: {self.agent_id}")

    def _load_definition(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Agent definition file not found at: {path}")
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        print(f"\nExecuting agent '{self.agent_id}' with user input...")
        # Simulate LLM call
        mock_llm_output = {
            "company_profile": {
                "company_name": "Global Tech Inc.",
                "industry": "Software as a Service (SaaS)",
                "annual_revenue_usd": 150000000,
                "employee_count": 800
            },
            "initial_pain_points": [
                "High customer churn rate",
                "Slow product development cycle",
                "Inefficient manual processes in marketing"
            ],
            "strategic_alignment": "The company aims to leverage AI to automate processes and improve customer retention, aligning perfectly with our solution's value proposition."
        }
        
        print("Agent execution complete.")
        return mock_llm_output

if __name__ == '__main__':
    # Demonstrates how to run the agent using asyncio
    import sys
    agent_yaml_path = sys.argv[1] if len(sys.argv) > 1 else "../../Agents/intake_assistant_agent.yaml"
    user_input = "Describe your company and key business challenges."
    mcp_client = MCPClient()  # Placeholder
    config = {"prompt_template": "..."}
    agent = IntakeAssistantAgent(agent_yaml_path, mcp_client, config)

    async def main():
        result = await agent.execute_with_resilience({"user_raw_input": user_input})
        print("\nAgent Result:")
        print(result)

    asyncio.run(main())

    # Relative path to the agent's YAML definition
    # This assumes you run this script from the project root directory (e.g., /home/bmsul/B2BValue)
    definition_path = os.path.join('Agents', 'intake_assistant_agent.yaml')

    try:
        # 1. Initialize the agent
        intake_agent = IntakeAssistantAgent(definition_path)

        # 2. Define a sample user input
        sample_input = "We are Global Tech Inc., an 800-person SaaS company with $150M in revenue. We're struggling with customer churn and our marketing team is bogged down by manual work. We need to innovate faster."

        # 3. Execute the agent
        structured_output = intake_agent.execute(sample_input)

        # 4. Print the results
        print("\n--- Agent Output ---")
        print(yaml.dump(structured_output, indent=2))
        print("--------------------")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure you are running this script from the root of the B2BValue project directory.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
