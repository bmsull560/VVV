import logging
import statistics
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import math

logger = logging.getLogger(__name__)

# Financial calculation constants
DEFAULT_DISCOUNT_RATE = 0.10
DEFAULT_ANALYSIS_PERIOD = 3

class ConfidenceLevel(Enum):
    """Standard confidence levels for statistical analysis"""
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"

class RiskLevel(Enum):
    """Standard risk classification levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"

def get_metric_value(metrics: List[Dict], name: str) -> float:
    """Safely retrieves a metric's value by name."""
    for metric in metrics:
        if metric['name'] == name:
            return float(metric.get('value', metric.get('default_value')))
    return 0.0

# =============================================================================
# FINANCIAL CALCULATIONS
# =============================================================================

def calculate_npv(annual_benefits: float, investment: float, 
                  years: int = DEFAULT_ANALYSIS_PERIOD, 
                  discount_rate: float = DEFAULT_DISCOUNT_RATE) -> float:
    """Calculate Net Present Value with standard discount rate"""
    if annual_benefits <= 0:
        return -investment
    
    pv_benefits = sum(annual_benefits / ((1 + discount_rate) ** year) for year in range(1, years + 1))
    return pv_benefits - investment

def calculate_irr(annual_benefits: float, investment: float, 
                  years: int = DEFAULT_ANALYSIS_PERIOD, 
                  precision: float = 0.01) -> float:
    """Calculate Internal Rate of Return using iterative approach"""
    if annual_benefits <= 0:
        return -1.0
    
    # Binary search for IRR
    low, high = 0.0, 1.0
    while high - low > precision:
        mid = (low + high) / 2
        npv = calculate_npv(annual_benefits, investment, years, mid)
        if npv > 0:
            low = mid
        else:
            high = mid
    
    return (low + high) / 2

def calculate_payback_period(annual_benefits: float, investment: float) -> float:
    """Calculate simple payback period in years"""
    if annual_benefits <= 0:
        return float('inf')
    return investment / annual_benefits

def calculate_roi_percentage(annual_benefits: float, investment: float, 
                           years: int = DEFAULT_ANALYSIS_PERIOD) -> float:
    """Calculate ROI percentage over analysis period"""
    total_benefits = annual_benefits * years
    net_gain = total_benefits - investment
    return (net_gain / investment * 100) if investment > 0 else 0.0

# =============================================================================
# STATISTICAL ANALYSIS
# =============================================================================

def calculate_confidence_score(data_quality: float, sample_size: int, 
                             variance: float = 0.1) -> float:
    """Calculate confidence score based on data quality and sample size"""
    # Base confidence from data quality (0.0 to 1.0)
    base_confidence = max(0.0, min(1.0, data_quality))
    
    # Sample size factor (logarithmic scaling)
    size_factor = min(1.0, math.log(sample_size + 1) / math.log(100))
    
    # Variance penalty (higher variance reduces confidence)
    variance_penalty = max(0.0, min(1.0, 1 - variance))
    
    # Combined confidence score
    confidence = base_confidence * 0.5 + size_factor * 0.3 + variance_penalty * 0.2
    return round(confidence, 3)

def calculate_correlation_strength(correlation: float) -> str:
    """Classify correlation strength based on coefficient"""
    abs_corr = abs(correlation)
    if abs_corr >= 0.8:
        return "Very Strong"
    elif abs_corr >= 0.6:
        return "Strong"
    elif abs_corr >= 0.4:
        return "Moderate"
    elif abs_corr >= 0.2:
        return "Weak"
    else:
        return "Very Weak"

def detect_outliers_iqr(data: List[float]) -> List[int]:
    """Detect outliers using Interquartile Range method"""
    if len(data) < 4:
        return []
    
    q1 = statistics.quantiles(data, n=4)[0]
    q3 = statistics.quantiles(data, n=4)[2]
    iqr = q3 - q1
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    return [i for i, val in enumerate(data) if val < lower_bound or val > upper_bound]

def calculate_volatility(data: List[float]) -> float:
    """Calculate coefficient of variation as volatility measure"""
    if len(data) < 2:
        return 0.0
    
    mean_val = statistics.mean(data)
    if mean_val == 0:
        return 0.0
    
    std_dev = statistics.stdev(data)
    return std_dev / abs(mean_val)

# =============================================================================
# RISK ASSESSMENT
# =============================================================================

def calculate_risk_score(probability: float, impact: float) -> float:
    """Calculate risk score as probability × impact"""
    return probability * impact

def classify_risk_level(risk_score: float, thresholds: Optional[Dict[str, float]] = None) -> RiskLevel:
    """Classify risk level based on score"""
    if thresholds is None:
        thresholds = {
            'critical': 80.0,
            'high': 60.0,
            'medium': 40.0,
            'low': 20.0
        }
    
    if risk_score >= thresholds['critical']:
        return RiskLevel.CRITICAL
    elif risk_score >= thresholds['high']:
        return RiskLevel.HIGH
    elif risk_score >= thresholds['medium']:
        return RiskLevel.MEDIUM
    elif risk_score >= thresholds['low']:
        return RiskLevel.LOW
    else:
        return RiskLevel.NEGLIGIBLE

def calculate_expected_value(scenarios: List[Dict[str, float]]) -> float:
    """Calculate expected value from probability-weighted scenarios"""
    return sum(scenario['probability'] * scenario['value'] for scenario in scenarios)

# =============================================================================
# BUSINESS INTELLIGENCE
# =============================================================================

def calculate_complexity_score(factors: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
    """Calculate weighted complexity score from multiple factors"""
    if weights is None:
        weights = {factor: 1.0 for factor in factors.keys()}
    
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    
    weighted_sum = sum(factors.get(factor, 0) * weight for factor, weight in weights.items())
    return weighted_sum / total_weight

def assess_data_quality(completeness: float, accuracy: float, consistency: float) -> float:
    """Assess overall data quality from multiple dimensions"""
    # Weighted average: completeness 40%, accuracy 40%, consistency 20%
    return (completeness * 0.4) + (accuracy * 0.4) + (consistency * 0.2)

def calculate_readiness_score(quality_score: float, complexity_score: float, 
                            complexity_penalty: float = 0.2) -> float:
    """Calculate project readiness score with complexity penalty"""
    base_score = quality_score
    penalty = complexity_penalty * (complexity_score / 10.0)  # Normalize complexity
    return max(0.0, min(1.0, base_score - penalty))

# =============================================================================
# EXISTING BUSINESS VALUE CALCULATIONS
# =============================================================================

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

def calculate_roi_metrics(total_annual_gain: float, total_investment: float, 
                         years: int = DEFAULT_ANALYSIS_PERIOD) -> Dict[str, Any]:
    """Calculate comprehensive ROI metrics based on annual gain and investment."""
    net_gain = total_annual_gain - total_investment
    roi_percentage = calculate_roi_percentage(total_annual_gain, total_investment, years)
    payback_period = calculate_payback_period(total_annual_gain, total_investment)
    npv = calculate_npv(total_annual_gain, total_investment, years)
    irr = calculate_irr(total_annual_gain, total_investment, years)

    return {
        'total_annual_gain': round(total_annual_gain, 2),
        'total_investment': round(total_investment, 2),
        'net_gain': round(net_gain, 2),
        'roi_percentage': round(roi_percentage, 2),
        'payback_period_years': round(payback_period, 1),
        'npv': round(npv, 2),
        'irr': round(irr * 100, 2),  # Convert to percentage
        'analysis_period_years': years
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

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_currency(amount: float, currency_symbol: str = "$") -> str:
    """Format amount as currency with appropriate scaling"""
    if abs(amount) >= 1_000_000:
        return f"{currency_symbol}{amount/1_000_000:.1f}M"
    elif abs(amount) >= 1_000:
        return f"{currency_symbol}{amount/1_000:.1f}K"
    else:
        return f"{currency_symbol}{amount:.0f}"

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format value as percentage"""
    return f"{value:.{decimal_places}f}%"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero"""
    return numerator / denominator if denominator != 0 else default
