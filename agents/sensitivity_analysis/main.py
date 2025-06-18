import logging
from typing import Dict, Any

from ..core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class SensitivityAnalysisAgent(BaseAgent):
    """Performs sensitivity analysis on financial models."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

    def _calculate_roi(self, investment: float, gain: float) -> float:
        """Helper function to calculate ROI, avoiding division by zero."""
        if investment == 0:
            return float('inf') if gain > 0 else 0
        return ((gain - investment) / investment) * 100

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Runs what-if scenarios based on input variations.

        Args:
            inputs: A dictionary containing:
                - 'base_investment': The base investment amount.
                - 'base_gain': The base gain amount.
                - 'variations': A dict where keys are 'investment' or 'gain'
                                and values are lists of percentage variations
                                (e.g., {'gain': [-0.1, 0, 0.1]}).
        """
        logger.info("Executing Sensitivity Analysis Agent...")
        
        base_investment = inputs.get('base_investment')
        base_gain = inputs.get('base_gain')
        variations = inputs.get('variations')

        if not all([isinstance(base_investment, (int, float)), 
                    isinstance(base_gain, (int, float)), 
                    isinstance(variations, dict)]):
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": "Invalid or missing inputs. Requires 'base_investment', 'base_gain', and 'variations'."}
            )

        scenario_results = []

        for variable, percentages in variations.items():
            if variable not in ['investment', 'gain']:
                logger.warning(f"Unsupported variable '{variable}' in variations. Skipping.")
                continue

            for p in percentages:
                scenario_investment = base_investment
                scenario_gain = base_gain

                if variable == 'investment':
                    scenario_investment = base_investment * (1 + p)
                elif variable == 'gain':
                    scenario_gain = base_gain * (1 + p)
                
                roi = self._calculate_roi(scenario_investment, scenario_gain)

                scenario_results.append({
                    'variable_changed': variable,
                    'percentage_change': round(p * 100, 1),
                    'roi_percentage': round(roi, 2)
                })
        
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data={"scenarios": scenario_results}
        )
