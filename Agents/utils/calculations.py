import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def get_metric_value(metrics: List[Dict], name: str) -> float:
    """Safely retrieves a metric's value by name."""
    for metric in metrics:
        if metric['name'] == name:
            return float(metric.get('value', metric.get('default_value')))
    return 0.0

def calculate_manual_labor_savings(metrics: List[Dict]) -> float:
    """Calculate annual savings from reduced manual labor."""
    hours_saved_per_week = get_metric_value(metrics, 'Hours saved per week')
    hourly_rate = get_metric_value(metrics, 'Average hourly rate')
    return hours_saved_per_week * hourly_rate * 52  # 52 weeks per year

def calculate_overhead_reduction(metrics: List[Dict]) -> float:
    """Calculate annual savings from reduced operational overhead."""
    monthly_reduction = get_metric_value(metrics, 'Monthly overhead reduction')
    return monthly_reduction * 12

def calculate_task_completion_gains(metrics: List[Dict]) -> float:
    """Calculate annual gains from accelerated task completion."""
    time_saved_per_task = get_metric_value(metrics, 'Time saved per task (minutes)')
    tasks_per_week = get_metric_value(metrics, 'Tasks per week')
    # Assuming the value of time is equivalent to a standard hourly rate (needs refinement)
    implicit_hourly_rate = 50  # Placeholder value
    return (time_saved_per_task / 60) * tasks_per_week * implicit_hourly_rate * 52

def calculate_security_improvement_value(metrics: List[Dict]) -> float:
    """Calculate value from improved security posture."""
    breach_cost = get_metric_value(metrics, 'Estimated cost of a breach')
    likelihood_reduction = get_metric_value(metrics, 'Likelihood reduction (%)')
    return breach_cost * (likelihood_reduction / 100)

def calculate_compliance_value(metrics: List[Dict]) -> float:
    """Calculate value from ensuring regulatory compliance."""
    return get_metric_value(metrics, 'Potential fine amount')

def calculate_lead_conversion_gain(metrics: List[Dict]) -> float:
    """Calculate annual gains from increased lead conversion."""
    additional_leads = get_metric_value(metrics, 'Additional leads per month')
    conversion_increase = get_metric_value(metrics, 'Conversion rate increase (%)')
    deal_size = get_metric_value(metrics, 'Average deal size')
    return additional_leads * (conversion_increase / 100) * deal_size * 12

def calculate_total_annual_gain(drivers_data: List[Dict], calculation_functions: Dict[str, Any]) -> float:
    """Calculate total annual gain from all drivers."""
    total_annual_gain = 0
    for pillar in drivers_data:
        for driver in pillar.get('tier_2_drivers', []):
            driver_name = driver['name']
            if driver_name in calculation_functions:
                metrics = driver['tier_3_metrics']
                driver_gain = calculation_functions[driver_name](metrics)
                total_annual_gain += driver_gain
    return total_annual_gain

def calculate_roi_metrics(total_annual_gain: float, total_investment: float) -> Dict[str, Any]:
    """Calculate ROI metrics based on annual gain and investment."""
    net_gain = total_annual_gain - total_investment
    roi_percentage = (net_gain / total_investment) * 100 if total_investment else 0
    payback_period_months = (total_investment / (total_annual_gain / 12)) if total_annual_gain > 0 else float('inf')

    return {
        'total_annual_gain': round(total_annual_gain, 2),
        'total_investment': round(total_investment, 2),
        'net_gain': round(net_gain, 2),
        'roi_percentage': round(roi_percentage, 2),
        'payback_period_months': round(payback_period_months, 1),
    }

def get_calculation_functions() -> Dict[str, Any]:
    """Return a dictionary mapping driver names to their calculation functions."""
    return {
        "Reduce Manual Labor": calculate_manual_labor_savings,
        "Lower Operational Overhead": calculate_overhead_reduction,
        "Accelerate Task Completion": calculate_task_completion_gains,
        "Improve Security Posture": calculate_security_improvement_value,
        "Ensure Regulatory Compliance": calculate_compliance_value,
        "Increase Lead Conversion": calculate_lead_conversion_gain,
    }
