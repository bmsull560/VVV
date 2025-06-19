import logging
import copy
from typing import Dict, Any, List
import time

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class SensitivityAnalysisAgent(BaseAgent):
    """Performs what-if analysis on financial models by varying driver metrics."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)
        # This logic is duplicated from ROICalculatorAgent to keep the agent self-contained.
        self.calculation_functions = {
            "Reduce Manual Labor": self._calculate_manual_labor_savings,
            "Lower Operational Overhead": self._calculate_overhead_reduction,
            "Accelerate Task Completion": self._calculate_task_completion_gains,
            "Improve Security Posture": self._calculate_security_improvement_value,
            "Ensure Regulatory Compliance": self._calculate_compliance_value,
            "Increase Lead Conversion": self._calculate_lead_conversion_gain,
        }

    def _get_metric_value(self, metrics: List[Dict], name: str) -> float:
        for metric in metrics:
            if metric['name'] == name:
                return float(metric.get('value', metric.get('default_value')))
        return 0.0

    def _calculate_manual_labor_savings(self, metrics: List[Dict]) -> float:
        hours_saved = self._get_metric_value(metrics, 'Hours saved per week')
        hourly_rate = self._get_metric_value(metrics, 'Average hourly rate')
        return hours_saved * hourly_rate * 52

    def _calculate_overhead_reduction(self, metrics: List[Dict]) -> float:
        return self._get_metric_value(metrics, 'Monthly overhead reduction') * 12

    def _calculate_task_completion_gains(self, metrics: List[Dict]) -> float:
        time_saved = self._get_metric_value(metrics, 'Time saved per task (minutes)')
        tasks = self._get_metric_value(metrics, 'Tasks per week')
        return (time_saved / 60) * tasks * 50 * 52  # Placeholder rate

    def _calculate_security_improvement_value(self, metrics: List[Dict]) -> float:
        cost = self._get_metric_value(metrics, 'Estimated cost of a breach')
        reduction = self._get_metric_value(metrics, 'Likelihood reduction (%)')
        return cost * (reduction / 100)

    def _calculate_compliance_value(self, metrics: List[Dict]) -> float:
        return self._get_metric_value(metrics, 'Potential fine amount')

    def _calculate_lead_conversion_gain(self, metrics: List[Dict]) -> float:
        leads = self._get_metric_value(metrics, 'Additional leads per month')
        increase = self._get_metric_value(metrics, 'Conversion rate increase (%)')
        deal_size = self._get_metric_value(metrics, 'Average deal size')
        return leads * (increase / 100) * deal_size * 12

    def _run_full_calculation(self, investment: float, drivers: List[Dict]) -> Dict[str, Any]:
        """Runs a full ROI calculation based on a given set of drivers."""
        total_annual_gain = 0
        for pillar in drivers:
            for driver in pillar.get('tier_2_drivers', []):
                if driver['name'] in self.calculation_functions:
                    total_annual_gain += self.calculation_functions[driver['name']](driver['tier_3_metrics'])
        
        net_gain = total_annual_gain - investment
        roi = (net_gain / investment) * 100 if investment > 0 else 0
        payback = (investment / (total_annual_gain / 12)) if total_annual_gain > 0 else float('inf')

        return {
            'roi_percentage': round(roi, 2),
            'net_gain': round(net_gain, 2),
            'payback_period_months': round(payback, 1)
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
