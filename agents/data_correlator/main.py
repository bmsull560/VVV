import logging
from typing import Dict, Any
import numpy as np

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class DataCorrelatorAgent(BaseAgent):
    """Calculates the correlation between two numerical datasets."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Calculates the Pearson correlation coefficient between two datasets.

        Args:
            inputs: A dictionary with 'dataset1' and 'dataset2' keys,
                    each containing a list of numbers.
        """
        if not isinstance(inputs, dict):
            raise TypeError("Input must be a dictionary")

        dataset1 = inputs.get('dataset1')
        dataset2 = inputs.get('dataset2')

        if not isinstance(dataset1, list) or not isinstance(dataset2, list):
            error_msg = "'dataset1' and 'dataset2' must be lists."
            logger.error(error_msg)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_msg}, execution_time_ms=0)

        if len(dataset1) != len(dataset2):
            error_msg = "Datasets must be of equal length."
            logger.error(error_msg)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_msg}, execution_time_ms=0)

        if not dataset1:
            error_msg = "Datasets cannot be empty."
            logger.error(error_msg)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_msg}, execution_time_ms=0)

        try:
            np_dataset1 = np.array(dataset1, dtype=float)
            np_dataset2 = np.array(dataset2, dtype=float)
        except (ValueError, TypeError):
            error_msg = "Datasets must contain only numerical values."
            logger.error(error_msg)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_msg}, execution_time_ms=0)

        try:
            if np.std(np_dataset1) == 0 or np.std(np_dataset2) == 0:
                # Handle case where one dataset has zero variance, correlation is undefined.
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={'correlation_coefficient': 0.0, 'message': 'One or both datasets have zero variance; correlation is 0.'},
                    execution_time_ms=75
                )

            correlation_matrix = np.corrcoef(np_dataset1, np_dataset2)
            correlation_coefficient = correlation_matrix[0, 1]

            logger.info(f"Calculated correlation coefficient: {correlation_coefficient:.4f}")
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data={'correlation_coefficient': round(correlation_coefficient, 4)},
                execution_time_ms=75
            )
        except Exception as e:
            logger.exception(f"An unexpected error occurred during correlation calculation: {e}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": str(e)},
                execution_time_ms=75
            )
