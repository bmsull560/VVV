import logging
from typing import Dict, Any

from ..core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class ROICalculatorAgent(BaseAgent):
    """Calculates the Return on Investment (ROI) from financial inputs."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Calculates ROI based on investment and gain.

        Args:
            inputs: A dictionary with 'investment' and 'gain' keys.
        """
        if not isinstance(inputs, dict):
            raise TypeError("Input must be a dictionary")

        try:
            investment = float(inputs.get('investment'))
            gain = float(inputs.get('gain'))
        except (TypeError, ValueError):
            error_msg = "'investment' and 'gain' must be provided and must be numbers."
            logger.error(error_msg)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_msg}, execution_time_ms=0)

        if investment <= 0:
            error_msg = "Investment must be a positive number."
            logger.error(error_msg)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_msg}, execution_time_ms=0)

        try:
            roi = ((gain - investment) / investment) * 100
            logger.info(f"Calculated ROI: {roi:.2f}% for investment {investment} and gain {gain}")
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data={'roi_percentage': round(roi, 2)},
                execution_time_ms=50
            )
        except Exception as e:
            logger.exception(f"An unexpected error occurred during ROI calculation: {e}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": str(e)},
                execution_time_ms=50
            )
