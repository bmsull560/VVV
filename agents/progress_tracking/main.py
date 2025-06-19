import logging
from typing import Dict, Any

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class ProgressTrackingAgent(BaseAgent):
    """Monitors and reports the progress of a business case workflow."""

    # Defines the canonical workflow steps for the interactive calculator
    WORKFLOW_STAGES = [
        "Discovery",       # Initial data intake and value driver identification
        "Quantification",  # ROI calculation
        "Analysis",        # Sensitivity analysis
        "Report",          # Final report generation
        "Completed"        # End state
    ]

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Calculates progress based on the current stage of the workflow.

        Args:
            inputs: A dictionary with a 'current_stage' key.
        """
        current_stage = inputs.get('current_stage')
        if not current_stage or current_stage not in self.WORKFLOW_STAGES:
            error_msg = f"Invalid or missing 'current_stage'. Must be one of {self.WORKFLOW_STAGES}."
            logger.error(error_msg)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_msg})

        try:
            current_index = self.WORKFLOW_STAGES.index(current_stage)
            progress_percentage = round(((current_index + 1) / len(self.WORKFLOW_STAGES)) * 100)
            
            next_stage = None
            if current_index < len(self.WORKFLOW_STAGES) - 1:
                next_stage = self.WORKFLOW_STAGES[current_index + 1]

            result_data = {
                'progress_percentage': progress_percentage,
                'current_stage': current_stage,
                'next_stage': next_stage
            }
            
            logger.info(f"Workflow progress: {progress_percentage}% at stage '{current_stage}'.")
            return AgentResult(status=AgentStatus.COMPLETED, data=result_data)

        except Exception as e:
            logger.exception(f"Error calculating progress: {e}")
            return AgentResult(status=AgentStatus.FAILED, data={"error": str(e)})
