import logging
import copy
from typing import Dict, Any, List
import time

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.utils.calculations import (
    get_calculation_functions,
    calculate_total_annual_gain,
    calculate_roi_metrics
)

logger = logging.getLogger(__name__)

class SensitivityAnalysisAgent(BaseAgent):
    """Performs what-if analysis on financial models by varying driver metrics."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)
        # Use shared calculation functions from utils
        self.calculation_functions = get_calculation_functions()

    # Calculation methods have been moved to agents.utils.calculations

    def _run_full_calculation(self, investment: float, drivers: List[Dict]) -> Dict[str, Any]:
        """Runs a full ROI calculation based on a given set of drivers."""
        # Calculate total annual gain using shared utility function
        total_annual_gain = calculate_total_annual_gain(drivers, self.calculation_functions)
        
        # Calculate ROI metrics using shared utility function
        roi_metrics = calculate_roi_metrics(total_annual_gain, investment)
        
        # Return only the metrics needed for sensitivity analysis
        return {
            'roi_percentage': roi_metrics['roi_percentage'],
            'net_gain': roi_metrics['net_gain'],
            'payback_period_months': roi_metrics['payback_period_months']
        }

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        start_time = time.monotonic()
        """
        Runs what-if scenarios by varying individual Tier 3 metrics.

        Args:
            inputs: A dictionary containing:
                'drivers': The base value driver data from ValueDriverAgent.
                'investment': The base investment cost.
                'variations': A list of variations to test.
        """
        base_drivers = inputs.get('drivers')
        investment_input = inputs.get('investment')
        variations = inputs.get('variations') # This can be None if not provided

        if base_drivers is None:
            error_message = "Required input 'drivers' is missing or null."
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_message}, execution_time_ms=execution_time_ms)

        if investment_input is None:
            error_message = "Required input 'investment' is missing or null."
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_message}, execution_time_ms=execution_time_ms)
        
        try:
            base_investment = float(investment_input)
        except (ValueError, TypeError):
            error_message = f"Invalid investment value: '{investment_input}'. Must be a number."
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_message}, execution_time_ms=execution_time_ms)

        if base_investment <= 0:
            error_message = "Investment must be positive for sensitivity analysis."
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_message}, execution_time_ms=execution_time_ms)

        # If variations is None (not provided), default to an empty list to run 0 scenarios.
        if variations is None:
            logger.info("Input 'variations' not provided or is null. Running 0 sensitivity scenarios.")
            variations = []
        
        if not isinstance(variations, list):
            error_message = f"Input 'variations' must be a list, got {type(variations)}."
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_message}, execution_time_ms=execution_time_ms)
        scenario_results = []

        for variation in variations:
            metric_to_change = variation['tier_3_metric_name']
            driver_to_change = variation['tier_2_driver_name']

            for p_change in variation['percentage_changes']:
                # Create a deep copy to avoid modifying the base data
                scenario_drivers = copy.deepcopy(base_drivers)
                
                # Apply the variation
                for pillar in scenario_drivers:
                    for driver in pillar.get('tier_2_drivers', []):
                        if driver['name'] == driver_to_change:
                            for metric in driver['tier_3_metrics']:
                                if metric['name'] == metric_to_change:
                                    original_value = float(metric.get('value', metric.get('default_value')))
                                    metric['value'] = original_value * (1 + p_change / 100)
                
                # Recalculate financial outcomes for this scenario
                result = self._run_full_calculation(base_investment, scenario_drivers)
                scenario_results.append({
                    'metric_changed': metric_to_change,
                    'percentage_change': p_change,
                    'result': result
                })

        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        return AgentResult(status=AgentStatus.COMPLETED, data={"scenarios": scenario_results}, execution_time_ms=execution_time_ms)
