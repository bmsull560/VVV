import logging
from typing import Dict, Any, List
import time

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.utils.calculations import (
    get_calculation_functions,
    calculate_total_annual_gain,
    calculate_roi_metrics
)

logger = logging.getLogger(__name__)

class ROICalculatorAgent(BaseAgent):
    """Calculates ROI and other financial metrics based on structured value driver inputs."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)
        # Use shared calculation functions from utils
        self.calculation_functions = get_calculation_functions()

    # Calculation methods have been moved to agents.utils.calculations

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        start_time = time.monotonic()
        """
        Calculates financial metrics from a list of value drivers and an investment amount.

        Args:
            inputs: A dictionary containing:
                'drivers': A list of value driver pillars from ValueDriverAgent.
                'investment': The total investment cost.
                'user_overrides': (Optional) A dictionary to override tier_3_metrics.
        """
        drivers_data = inputs.get('drivers')
        investment_input = inputs.get('investment')

        if drivers_data is None:
            error_message = "Required input 'drivers' is missing or null."
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_message}, execution_time_ms=execution_time_ms)

        if investment_input is None:
            # Default to 0.0, which will be caught by the 'investment must be positive' check later
            total_investment = 0.0
        else:
            try:
                total_investment = float(investment_input)
            except (ValueError, TypeError):
                error_message = f"Invalid investment value: '{investment_input}'. Must be a number."
                execution_time_ms = int((time.monotonic() - start_time) * 1000)
                return AgentResult(status=AgentStatus.FAILED, data={"error": error_message}, execution_time_ms=execution_time_ms)
        # Calculate total annual gain using shared utility function
        total_annual_gain = calculate_total_annual_gain(drivers_data, self.calculation_functions)
        gain_breakdown = []

        # Calculate gain breakdown by pillar
        for pillar in drivers_data:
            pillar_gain = 0
            for driver in pillar.get('tier_2_drivers', []):
                driver_name = driver['name']
                if driver_name in self.calculation_functions:
                    # In a real scenario, you'd merge user_overrides here
                    metrics = driver['tier_3_metrics']
                    driver_gain = self.calculation_functions[driver_name](metrics)
                    pillar_gain += driver_gain
            
            if pillar_gain > 0:
                gain_breakdown.append({
                    'pillar': pillar['pillar'],
                    'annual_gain': round(pillar_gain, 2)
                })

        if total_investment <= 0:
            error_message = "Investment must be positive."
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_message}, execution_time_ms=execution_time_ms)

        # Calculate ROI metrics using shared utility function
        roi_metrics = calculate_roi_metrics(total_annual_gain, total_investment)
        
        # Add gain breakdown to the result
        result_data = {
            **roi_metrics,
            'gain_breakdown': gain_breakdown
        }

        logger.info(f"ROI calculation complete. ROI: {result_data['roi_percentage']}%" )
        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=result_data,
            execution_time_ms=execution_time_ms
        )
