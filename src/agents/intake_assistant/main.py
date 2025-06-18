import logging
from typing import Dict, Any
import uuid

from ..core.agent_base import BaseAgent, AgentResult, AgentStatus
from ...memory.types import KnowledgeEntity

logger = logging.getLogger(__name__)

class IntakeAssistantAgent(BaseAgent):
    """Processes initial user input to structure and store project information."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

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
