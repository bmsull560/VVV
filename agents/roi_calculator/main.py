import logging
from typing import Dict, Any, List
import time

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class ROICalculatorAgent(BaseAgent):
    """Calculates ROI and other financial metrics based on structured value driver inputs."""

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)
        # Map driver names to their calculation methods
        self.calculation_functions = {
            "Reduce Manual Labor": self._calculate_manual_labor_savings,
            "Lower Operational Overhead": self._calculate_overhead_reduction,
            "Accelerate Task Completion": self._calculate_task_completion_gains,
            "Improve Security Posture": self._calculate_security_improvement_value,
            "Ensure Regulatory Compliance": self._calculate_compliance_value,
            "Increase Lead Conversion": self._calculate_lead_conversion_gain,
        }

    def _get_metric_value(self, metrics: List[Dict], name: str) -> float:
        """Safely retrieves a metric's value by name."""
        for metric in metrics:
            if metric['name'] == name:
                return float(metric.get('value', metric.get('default_value')))
        return 0.0

    def _calculate_manual_labor_savings(self, metrics: List[Dict]) -> float:
        hours_saved_per_week = self._get_metric_value(metrics, 'Hours saved per week')
        hourly_rate = self._get_metric_value(metrics, 'Average hourly rate')
        return hours_saved_per_week * hourly_rate * 52  # 52 weeks per year

    def _calculate_overhead_reduction(self, metrics: List[Dict]) -> float:
        monthly_reduction = self._get_metric_value(metrics, 'Monthly overhead reduction')
        return monthly_reduction * 12

    def _calculate_task_completion_gains(self, metrics: List[Dict]) -> float:
        time_saved_per_task = self._get_metric_value(metrics, 'Time saved per task (minutes)')
        tasks_per_week = self._get_metric_value(metrics, 'Tasks per week')
        # Assuming the value of time is equivalent to a standard hourly rate (needs refinement)
        implicit_hourly_rate = 50  # Placeholder value
        return (time_saved_per_task / 60) * tasks_per_week * implicit_hourly_rate * 52

    def _calculate_security_improvement_value(self, metrics: List[Dict]) -> float:
        breach_cost = self._get_metric_value(metrics, 'Estimated cost of a breach')
        likelihood_reduction = self._get_metric_value(metrics, 'Likelihood reduction (%)')
        return breach_cost * (likelihood_reduction / 100)

    def _calculate_compliance_value(self, metrics: List[Dict]) -> float:
        return self._get_metric_value(metrics, 'Potential fine amount')

    def _calculate_lead_conversion_gain(self, metrics: List[Dict]) -> float:
        additional_leads = self._get_metric_value(metrics, 'Additional leads per month')
        conversion_increase = self._get_metric_value(metrics, 'Conversion rate increase (%)')
        deal_size = self._get_metric_value(metrics, 'Average deal size')
        return additional_leads * (conversion_increase / 100) * deal_size * 12

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
        total_annual_gain = 0
        gain_breakdown = []

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
            total_annual_gain += pillar_gain

        if total_investment <= 0:
            error_message = "Investment must be positive."
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(status=AgentStatus.FAILED, data={"error": error_message}, execution_time_ms=execution_time_ms)

        net_gain = total_annual_gain - total_investment
        roi_percentage = (net_gain / total_investment) * 100 if total_investment else 0
        # Payback in months
        payback_period_months = (total_investment / (total_annual_gain / 12)) if total_annual_gain > 0 else float('inf')

        result_data = {
            'total_annual_gain': round(total_annual_gain, 2),
            'total_investment': round(total_investment, 2),
            'net_gain': round(net_gain, 2),
            'roi_percentage': round(roi_percentage, 2),
            'payback_period_months': round(payback_period_months, 1),
            'gain_breakdown': gain_breakdown
        }

        logger.info(f"ROI calculation complete. ROI: {result_data['roi_percentage']}%" )
        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=result_data,
            execution_time_ms=execution_time_ms
        )
