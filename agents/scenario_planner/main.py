"""
Scenario Planner Agent

This agent creates and analyzes strategic business scenarios, enabling
what-if analysis, strategic planning, and decision support for complex
business cases.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum, auto
from datetime import datetime, timezone
import statistics
import math
import random
import json
from decimal import Decimal

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.memory_types import KnowledgeEntity
from agents.utils.calculations import (
    calculate_npv, calculate_irr, calculate_payback_period, calculate_roi_percentage,
    calculate_confidence_score, calculate_risk_score, classify_risk_level
)

logger = logging.getLogger(__name__)

class ScenarioType(str, Enum):
    """Types of business scenarios."""
    BASE_CASE = "base_case"
    OPTIMISTIC = "optimistic"
    PESSIMISTIC = "pessimistic"
    CUSTOM = "custom"
    MONTE_CARLO = "monte_carlo"
    SENSITIVITY = "sensitivity"
    STRESS_TEST = "stress_test"
    WHAT_IF = "what_if"

class VariableType(str, Enum):
    """Types of scenario variables with enhanced categorization."""
    REVENUE = "revenue"
    COST = "cost"
    GROWTH_RATE = "growth_rate"
    ADOPTION_RATE = "adoption_rate"
    EFFICIENCY_GAIN = "efficiency_gain"
    RESOURCE_UTILIZATION = "resource_utilization"
    MARKET_SHARE = "market_share"
    CUSTOMER_RETENTION = "customer_retention"
    RISK_PROBABILITY = "risk_probability"
    RISK_IMPACT = "risk_impact"
    CUSTOM = "custom"
    INFLATION = "inflation"
    COMPETITIVE_PRESSURE = "competitive_pressure"
    MARKET_ENTRY = "market_entry"
    REGULATORY_CHANGE = "regulatory_change"
    TECHNOLOGY_DISRUPTION = "technology_disruption"

class ScenarioProbability(Enum):
    """Probability levels for scenarios."""
    VERY_UNLIKELY = auto()  # < 10%
    UNLIKELY = auto()       # 10-30%
    POSSIBLE = auto()       # 30-50%
    LIKELY = auto()         # 50-70%
    VERY_LIKELY = auto()    # 70-90%
    ALMOST_CERTAIN = auto() # > 90%

class RecommendationType(Enum):
    """Types of strategic recommendations."""
    STRATEGIC_PIVOT = auto()
    RISK_MITIGATION = auto()
    OPPORTUNITY_LEVERAGE = auto()
    CONTINGENCY_PLAN = auto()
    RESOURCE_ALLOCATION = auto()
    TIMING_ADJUSTMENT = auto()

class ScenarioPlannerAgent(BaseAgent):
    """
    Production-ready agent for creating and analyzing strategic business scenarios,
    enabling what-if analysis, strategic planning, and decision support.
    """

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Enhanced validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': [
                    'scenario_type', 'base_case'
                ],
                'field_types': {
                    'scenario_type': 'string',
                    'base_case': 'object',
                    'variables': 'array',
                    'monte_carlo_iterations': 'integer',
                    'sensitivity_range': 'number',
                    'sensitivity_steps': 'integer',
                    'custom_scenarios': 'array',
                    'optimization_target': 'string',
                    'constraints': 'object',
                    'time_horizon': 'integer',
                    'discount_rate': 'number'
                },
                'field_constraints': {
                    'scenario_type': {'enum': [t.value for t in ScenarioType]},
                    'monte_carlo_iterations': {'min': 10, 'max': 10000},
                    'sensitivity_range': {'min': 0.01, 'max': 1.0},
                    'sensitivity_steps': {'min': 3, 'max': 20},
                    'time_horizon': {'min': 1, 'max': 20},
                    'discount_rate': {'min': 0.0, 'max': 0.5}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Initialize scenario planner configuration
        self.default_monte_carlo_iterations = config.get('default_monte_carlo_iterations', 1000)
        self.default_sensitivity_range = config.get('default_sensitivity_range', 0.2)
        self.default_sensitivity_steps = config.get('default_sensitivity_steps', 5)
        self.default_time_horizon = config.get('default_time_horizon', 5)
        self.default_discount_rate = config.get('default_discount_rate', 0.1)
        self.confidence_threshold = config.get('confidence_threshold', 0.8)
        self.risk_tolerance = config.get('risk_tolerance', 'medium')
        self.probability_thresholds = config.get('probability_thresholds', {
            'very_unlikely': 0.1,
            'unlikely': 0.3,
            'possible': 0.5,
            'likely': 0.7,
            'very_likely': 0.9,
            'almost_certain': 0.95
        })
        self.dependency_matrix = {}  # Will store variable interdependencies

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for scenario planner inputs."""
        errors = []
        
        # Validate base case structure
        base_case = inputs.get('base_case', {})
        if not isinstance(base_case, dict):
            errors.append("Base case must be an object")
        else:
            required_base_fields = ['investment', 'annual_benefit']
            for field in required_base_fields:
                if field not in base_case:
                    errors.append(f"Base case missing required field: {field}")
                elif not isinstance(base_case[field], (int, float)):
                    errors.append(f"Base case field '{field}' must be numeric")
        
        # Validate variables if provided
        variables = inputs.get('variables', [])
        if variables and not isinstance(variables, list):
            errors.append("Variables must be an array")
        else:
            for i, variable in enumerate(variables):
                if not isinstance(variable, dict):
                    errors.append(f"Variable {i} must be an object")
                    continue
                
                required_var_fields = ['name', 'type', 'base_value']
                for field in required_var_fields:
                    if field not in variable:
                        errors.append(f"Variable {i} missing required field: {field}")
                
                if 'type' in variable and variable['type'] not in [t.value for t in VariableType]:
                    errors.append(f"Variable {i} has invalid type: {variable['type']}")
                
                if 'base_value' in variable and not isinstance(variable['base_value'], (int, float)):
                    errors.append(f"Variable {i} base_value must be numeric")
                
                if 'range' in variable:
                    if not isinstance(variable['range'], dict):
                        errors.append(f"Variable {i} range must be an object")
                    elif 'min' not in variable['range'] or 'max' not in variable['range']:
                        errors.append(f"Variable {i} range must include min and max values")
        
        # Validate custom scenarios if provided
        custom_scenarios = inputs.get('custom_scenarios', [])
        if custom_scenarios and not isinstance(custom_scenarios, list):
            errors.append("Custom scenarios must be an array")
        else:
            for i, scenario in enumerate(custom_scenarios):
                if not isinstance(scenario, dict):
                    errors.append(f"Custom scenario {i} must be an object")
                    continue
                
                if 'name' not in scenario:
                    errors.append(f"Custom scenario {i} missing required field: name")
                
                if 'variables' in scenario and not isinstance(scenario['variables'], dict):
                    errors.append(f"Custom scenario {i} variables must be an object")
        
        # Validate scenario type specific requirements
        scenario_type = inputs.get('scenario_type')
        
        if scenario_type == ScenarioType.MONTE_CARLO.value:
            if 'variables' not in inputs or not inputs['variables']:
                errors.append("Monte Carlo simulation requires at least one variable")

            for variable in variables:
                if 'distribution' not in variable:
                    errors.append(f"Variable '{variable.get('name', 'unknown')}' missing required field for Monte Carlo: distribution")
        
        elif scenario_type == ScenarioType.SENSITIVITY.value:
            if 'variables' not in inputs or not inputs['variables']:
                errors.append("Sensitivity analysis requires at least one variable")
        
        elif scenario_type == ScenarioType.WHAT_IF.value:
            if 'custom_scenarios' not in inputs or not inputs['custom_scenarios']:
                errors.append("What-if analysis requires at least one custom scenario")

        # Validate dependency matrix if provided
        if 'dependency_matrix' in inputs:
            dependency_matrix = inputs['dependency_matrix']
            if not isinstance(dependency_matrix, dict):
                errors.append("Dependency matrix must be an object")
            else:
                for var_name, dependencies in dependency_matrix.items():
                    if not isinstance(dependencies, dict):
                        errors.append(f"Dependencies for variable '{var_name}' must be an object")
        
        return errors

    def _create_base_scenario(self, base_case: Dict[str, Any]) -> Dict[str, Any]:
        """Create the base scenario from input data."""
        # Extract base case parameters
        investment = base_case.get('investment', 0)
        annual_benefit = base_case.get('annual_benefit', 0)
        time_horizon = base_case.get('time_horizon', self.default_time_horizon)
        discount_rate = base_case.get('discount_rate', self.default_discount_rate)
        
        # Calculate financial metrics
        total_benefit = annual_benefit * time_horizon
        net_benefit = total_benefit - investment
        roi_percentage = calculate_roi_percentage(annual_benefit, investment, time_horizon)
        payback_period = calculate_payback_period(annual_benefit, investment)
        
        # Calculate NPV
        npv = calculate_npv(annual_benefit, investment, time_horizon, discount_rate)
        
        # Calculate IRR (simplified approximation)
        irr = calculate_irr(annual_benefit, investment, time_horizon)
        
        # Create base scenario
        base_scenario = {
            'name': 'Base Case',
            'type': ScenarioType.BASE_CASE.value,
            'inputs': {
                'investment': investment,
                'annual_benefit': annual_benefit,
                'time_horizon': time_horizon,
                'discount_rate': discount_rate
            },
            'outputs': {
                'total_benefit': total_benefit,
                'net_benefit': net_benefit,
                'roi_percentage': round(roi_percentage, 2),
                'payback_period': payback_period,
                'npv': round(npv, 2),
                'irr': round(irr * 100, 2)  # Convert to percentage
            },
            'confidence': 1.0,
            'risk_level': 'medium'
        }
        
        return base_scenario

    def _create_optimistic_scenario(self, base_scenario: Dict[str, Any], variables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create an optimistic scenario based on the base scenario."""
        # Start with a copy of the base scenario
        optimistic_scenario = {
            'name': 'Optimistic Case',
            'type': ScenarioType.OPTIMISTIC.value,
            'inputs': base_scenario['inputs'].copy(),
            'confidence': 0.7,
            'risk_level': 'low'
        }
        
        # Apply optimistic adjustments
        if variables:
            # Use variable-specific adjustments
            adjusted_values = {}
            for variable in variables:
                var_name = variable['name']
                var_type = variable['type']
                base_value = variable['base_value']
                adjustment_factor = 1.0
                
                # Calculate optimistic value based on variable type
                if var_type == VariableType.REVENUE.value:
                    # Increase revenue by 20%
                    adjustment_factor = 1.2
                elif var_type == VariableType.COST.value:
                    # Decrease cost by 15%
                    adjustment_factor = 0.85
                elif var_type == VariableType.GROWTH_RATE.value:
                    # Increase growth rate by 30%
                    adjustment_factor = 1.3
                elif var_type == VariableType.ADOPTION_RATE.value:
                    # Increase adoption rate by 25%
                    adjustment_factor = 1.25
                    base_value = min(base_value * adjustment_factor, 1.0)
                elif var_type == VariableType.EFFICIENCY_GAIN.value:
                    # Increase efficiency gain by 25%
                    adjustment_factor = 1.25
                elif var_type == VariableType.INFLATION.value:
                    # Decrease inflation by 20% (favorable)
                    adjustment_factor = 0.8
                elif var_type == VariableType.COMPETITIVE_PRESSURE.value:
                    # Decrease competitive pressure by 30% (favorable)
                    adjustment_factor = 0.7
                elif var_type == VariableType.MARKET_ENTRY.value:
                    # Increase market entry success by 25%
                    adjustment_factor = 1.25
                elif var_type == VariableType.REGULATORY_CHANGE.value:
                    # Decrease regulatory burden by 15% (favorable)
                    adjustment_factor = 0.85
                elif var_type == VariableType.TECHNOLOGY_DISRUPTION.value:
                    # Increase positive technology impact by 30%
                    adjustment_factor = 1.3
                else:
                    # Default 20% improvement
                    adjustment_factor = 1.2
                
                optimistic_value = base_value * adjustment_factor
                adjusted_values[var_name] = optimistic_value
                
                # Apply to inputs
                if var_name in optimistic_scenario['inputs']:
                    optimistic_scenario['inputs'][var_name] = optimistic_value
            
            # Apply variable dependencies if defined
            if hasattr(self, 'dependency_matrix') and self.dependency_matrix:
                self._apply_dependencies(optimistic_scenario['inputs'], adjusted_values)
        else:
            # Use default optimistic adjustments
            optimistic_scenario['inputs']['annual_benefit'] = base_scenario['inputs']['annual_benefit'] * 1.2
            optimistic_scenario['inputs']['investment'] = base_scenario['inputs']['investment'] * 0.9
        
        # Recalculate outputs
        investment = optimistic_scenario['inputs']['investment']
        annual_benefit = optimistic_scenario['inputs']['annual_benefit']
        time_horizon = optimistic_scenario['inputs']['time_horizon']
        discount_rate = optimistic_scenario['inputs']['discount_rate']
        
        total_benefit = annual_benefit * time_horizon
        net_benefit = total_benefit - investment
        roi_percentage = (net_benefit / investment * 100) if investment > 0 else 0
        payback_period = investment / annual_benefit if annual_benefit > 0 else float('inf')
        
        # Calculate NPV
        npv = -investment
        for year in range(1, time_horizon + 1):
            npv += annual_benefit / ((1 + discount_rate) ** year)
        
        # Calculate IRR (simplified approximation)
        irr = (annual_benefit / investment) - 1 if investment > 0 else 0
        
        optimistic_scenario['outputs'] = {
            'total_benefit': total_benefit,
            'net_benefit': net_benefit,
            'roi_percentage': roi_percentage,
            'payback_period': payback_period,
            'npv': npv,
            'irr': irr
        }
        
        return optimistic_scenario

    def _create_pessimistic_scenario(self, base_scenario: Dict[str, Any], variables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a pessimistic scenario based on the base scenario."""
        # Start with a copy of the base scenario
        pessimistic_scenario = {
            'name': 'Pessimistic Case',
            'type': ScenarioType.PESSIMISTIC.value,
            'inputs': base_scenario['inputs'].copy(),
            'confidence': 0.7,
            'risk_level': 'high'
        }
        
        # Apply pessimistic adjustments
        if variables:
            # Use variable-specific adjustments
            adjusted_values = {}
            for variable in variables:
                var_name = variable['name']
                var_type = variable['type']
                base_value = variable['base_value']
                adjustment_factor = 1.0
                
                # Calculate pessimistic value based on variable type
                if var_type == VariableType.REVENUE.value:
                    # Decrease revenue by 15%
                    adjustment_factor = 0.85
                elif var_type == VariableType.COST.value:
                    # Increase cost by 20%
                    adjustment_factor = 1.2
                elif var_type == VariableType.GROWTH_RATE.value:
                    # Decrease growth rate by 25%
                    adjustment_factor = 0.75
                elif var_type == VariableType.ADOPTION_RATE.value:
                    # Decrease adoption rate by 20%
                    adjustment_factor = 0.8
                elif var_type == VariableType.EFFICIENCY_GAIN.value:
                    # Decrease efficiency gain by 20%
                    adjustment_factor = 0.8
                elif var_type == VariableType.INFLATION.value:
                    # Increase inflation by 30% (unfavorable)
                    adjustment_factor = 1.3
                elif var_type == VariableType.COMPETITIVE_PRESSURE.value:
                    # Increase competitive pressure by 40% (unfavorable)
                    adjustment_factor = 1.4
                elif var_type == VariableType.MARKET_ENTRY.value:
                    # Decrease market entry success by 25%
                    adjustment_factor = 0.75
                elif var_type == VariableType.REGULATORY_CHANGE.value:
                    # Increase regulatory burden by 25% (unfavorable)
                    adjustment_factor = 1.25
                elif var_type == VariableType.TECHNOLOGY_DISRUPTION.value:
                    # Decrease positive technology impact by 20%
                    adjustment_factor = 0.8
                else:
                    # Default 15% deterioration
                    adjustment_factor = 0.85
                
                pessimistic_value = base_value * adjustment_factor
                adjusted_values[var_name] = pessimistic_value
                
                # Apply to inputs
                if var_name in pessimistic_scenario['inputs']:
                    pessimistic_scenario['inputs'][var_name] = pessimistic_value
            
            # Apply variable dependencies if defined
            if hasattr(self, 'dependency_matrix') and self.dependency_matrix:
                self._apply_dependencies(pessimistic_scenario['inputs'], adjusted_values)
        else:
            # Use default pessimistic adjustments
            pessimistic_scenario['inputs']['annual_benefit'] = base_scenario['inputs']['annual_benefit'] * 0.8
            pessimistic_scenario['inputs']['investment'] = base_scenario['inputs']['investment'] * 1.15
        
        # Recalculate outputs
        investment = pessimistic_scenario['inputs']['investment']
        annual_benefit = pessimistic_scenario['inputs']['annual_benefit']
        time_horizon = pessimistic_scenario['inputs']['time_horizon']
        discount_rate = pessimistic_scenario['inputs']['discount_rate']
        
        total_benefit = annual_benefit * time_horizon
        net_benefit = total_benefit - investment
        roi_percentage = (net_benefit / investment * 100) if investment > 0 else 0
        payback_period = investment / annual_benefit if annual_benefit > 0 else float('inf')
        
        # Calculate NPV
        npv = -investment
        for year in range(1, time_horizon + 1):
            npv += annual_benefit / ((1 + discount_rate) ** year)
        
        # Calculate IRR (simplified approximation)
        irr = (annual_benefit / investment) - 1 if investment > 0 else 0
        
        pessimistic_scenario['outputs'] = {
            'total_benefit': total_benefit,
            'net_benefit': net_benefit,
            'roi_percentage': roi_percentage,
            'payback_period': payback_period,
            'npv': npv,
            'irr': irr
        }
        
        return pessimistic_scenario

    def _create_custom_scenario(self, base_scenario: Dict[str, Any], scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom scenario based on the base scenario and custom configuration."""
        # Start with a copy of the base scenario
        custom_scenario = {
            'name': scenario_config.get('name', 'Custom Scenario'),
            'type': ScenarioType.CUSTOM.value,
            'inputs': base_scenario['inputs'].copy(),
            'confidence': scenario_config.get('confidence', 0.5),
            'risk_level': scenario_config.get('risk_level', 'medium')
        }
        
        # Apply custom variable values
        custom_variables = scenario_config.get('variables', {})
        for var_name, var_value in custom_variables.items():
            custom_scenario['inputs'][var_name] = var_value
        
        # Apply variable dependencies if defined
        if hasattr(self, 'dependency_matrix') and self.dependency_matrix:
            self._apply_dependencies(custom_scenario['inputs'], custom_variables)
        
        # Recalculate outputs
        investment = custom_scenario['inputs']['investment']
        annual_benefit = custom_scenario['inputs']['annual_benefit']
        time_horizon = custom_scenario['inputs']['time_horizon']
        discount_rate = custom_scenario['inputs']['discount_rate']
        
        total_benefit = annual_benefit * time_horizon
        net_benefit = total_benefit - investment
        roi_percentage = (net_benefit / investment * 100) if investment > 0 else 0
        payback_period = investment / annual_benefit if annual_benefit > 0 else float('inf')
        
        # Calculate NPV
        npv = -investment
        for year in range(1, time_horizon + 1):
            npv += annual_benefit / ((1 + discount_rate) ** year)
        
        # Calculate IRR (simplified approximation)
        irr = (annual_benefit / investment) - 1 if investment > 0 else 0
        
        custom_scenario['outputs'] = {
            'total_benefit': total_benefit,
            'net_benefit': net_benefit,
            'roi_percentage': roi_percentage,
            'payback_period': payback_period,
            'npv': npv,
            'irr': irr
        }
        
        return custom_scenario

    def _run_monte_carlo_simulation(self, base_scenario: Dict[str, Any], variables: List[Dict[str, Any]], iterations: int) -> Dict[str, Any]:
        """Run a Monte Carlo simulation based on the base scenario and variables."""
        # Initialize results storage
        results = {
            'name': 'Monte Carlo Simulation',
            'type': ScenarioType.MONTE_CARLO.value,
            'base_scenario': base_scenario,
            'iterations': iterations,
            'simulation_results': [],
            'summary': {}
        }
        
        # Run simulation iterations
        for i in range(iterations):
            # Generate random values for each variable based on its distribution
            iteration_inputs = base_scenario['inputs'].copy()
            
            for variable in variables:
                var_name = variable['name']
                base_value = variable['base_value']
                distribution = variable.get('distribution', 'normal')
                
                # Generate random value based on distribution
                if distribution == 'normal':
                    # Normal distribution with standard deviation of 10% of base value
                    std_dev = base_value * 0.1
                    random_value = random.normalvariate(base_value, std_dev)
                elif distribution == 'uniform':
                    # Uniform distribution with range of ±20% of base value
                    min_val = base_value * 0.8
                    max_val = base_value * 1.2
                    random_value = random.uniform(min_val, max_val)
                elif distribution == 'triangular':
                    # Triangular distribution with mode at base value and range of ±30%
                    min_val = base_value * 0.7
                    max_val = base_value * 1.3
                    random_value = random.triangular(min_val, max_val, base_value)
                elif distribution == 'custom':
                    # Custom distribution with specified range
                    range_min = variable.get('range', {}).get('min', base_value * 0.8)
                    range_max = variable.get('range', {}).get('max', base_value * 1.2)
                    random_value = random.uniform(range_min, range_max)
                else:
                    # Default to normal distribution
                    std_dev = base_value * 0.1
                    random_value = random.normalvariate(base_value, std_dev)
                
                # Apply to inputs
                if var_name in iteration_inputs:
                    iteration_inputs[var_name] = random_value
            
            # Calculate outputs for this iteration
            investment = iteration_inputs['investment']
            annual_benefit = iteration_inputs['annual_benefit']
            time_horizon = iteration_inputs['time_horizon']
            discount_rate = iteration_inputs['discount_rate']
            
            total_benefit = annual_benefit * time_horizon
            net_benefit = total_benefit - investment
            roi_percentage = (net_benefit / investment * 100) if investment > 0 else 0
            payback_period = investment / annual_benefit if annual_benefit > 0 else float('inf')
            
            # Calculate NPV
            npv = -investment
            for year in range(1, time_horizon + 1):
                npv += annual_benefit / ((1 + discount_rate) ** year)
            
            # Store iteration results
            results['simulation_results'].append({
                'iteration': i,
                'inputs': iteration_inputs,
                'outputs': {
                    'total_benefit': total_benefit,
                    'net_benefit': net_benefit,
                    'roi_percentage': roi_percentage,
                    'payback_period': payback_period,
                    'npv': npv
                }
            })
        
        # Calculate summary statistics
        roi_values = [result['outputs']['roi_percentage'] for result in results['simulation_results']]
        npv_values = [result['outputs']['npv'] for result in results['simulation_results']]
        payback_values = [result['outputs']['payback_period'] for result in results['simulation_results'] if result['outputs']['payback_period'] != float('inf')]
        
        # Calculate percentiles
        roi_percentiles = {
            'p10': self._percentile(roi_values, 10),
            'p25': self._percentile(roi_values, 25),
            'p50': self._percentile(roi_values, 50),
            'p75': self._percentile(roi_values, 75),
            'p90': self._percentile(roi_values, 90)
        }
        
        npv_percentiles = {
            'p10': self._percentile(npv_values, 10),
            'p25': self._percentile(npv_values, 25),
            'p50': self._percentile(npv_values, 50),
            'p75': self._percentile(npv_values, 75),
            'p90': self._percentile(npv_values, 90)
        }
        
        # Calculate probability of positive ROI and NPV
        prob_positive_roi = len([v for v in roi_values if v > 0]) / len(roi_values)
        prob_positive_npv = len([v for v in npv_values if v > 0]) / len(npv_values)
        
        # Calculate expected values
        expected_roi = statistics.mean(roi_values)
        expected_npv = statistics.mean(npv_values)
        expected_payback = statistics.mean(payback_values) if payback_values else float('inf')
        
        # Store summary statistics
        results['summary'] = {
            'expected_roi': expected_roi,
            'expected_npv': expected_npv,
            'expected_payback': expected_payback,
            'roi_percentiles': roi_percentiles,
            'npv_percentiles': npv_percentiles,
            'prob_positive_roi': prob_positive_roi,
            'prob_positive_npv': prob_positive_npv,
            'roi_std_dev': statistics.stdev(roi_values) if len(roi_values) > 1 else 0,
            'npv_std_dev': statistics.stdev(npv_values) if len(npv_values) > 1 else 0
        }
        
        # Calculate risk level based on probability of positive outcomes
        if prob_positive_roi > 0.9 and prob_positive_npv > 0.9:
            results['risk_level'] = 'low'
        elif prob_positive_roi > 0.7 and prob_positive_npv > 0.7:
            results['risk_level'] = 'medium'
        else:
            results['risk_level'] = 'high'
        
        # Calculate confidence level
        results['confidence'] = (prob_positive_roi + prob_positive_npv) / 2
        
        return results

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate the specified percentile of a list of values."""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * percentile / 100
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower_index = math.floor(index)
            upper_index = math.ceil(index)
            lower_value = sorted_values[lower_index]
            upper_value = sorted_values[upper_index]
            interpolation = index - lower_index
            return lower_value + (upper_value - lower_value) * interpolation

    def _run_sensitivity_analysis(self, base_scenario: Dict[str, Any], variables: List[Dict[str, Any]], sensitivity_range: float, steps: int) -> Dict[str, Any]:
        """Run a sensitivity analysis based on the base scenario and variables."""
        # Initialize results storage
        results = {
            'name': 'Sensitivity Analysis',
            'type': ScenarioType.SENSITIVITY.value,
            'base_scenario': base_scenario,
            'sensitivity_range': sensitivity_range,
            'steps': steps,
            'variable_sensitivities': [],
            'summary': {}
        }
        
        # Calculate step size
        step_size = (2 * sensitivity_range) / (steps - 1) if steps > 1 else 0
        
        # Analyze each variable
        for variable in variables:
            var_name = variable['name']
            var_type = variable['type']
            base_value = variable['base_value']
            
            # Skip variables not in base scenario inputs
            if var_name not in base_scenario['inputs']:
                continue
            
            # Initialize variable sensitivity results
            var_sensitivity = {
                'variable': var_name,
                'type': var_type,
                'base_value': base_value,
                'steps': []
            }
            
            # Calculate values for each step
            for i in range(steps):
                # Calculate adjustment factor for this step
                adjustment = -sensitivity_range + (i * step_size)
                adjusted_value = base_value * (1 + adjustment)
                
                # Create scenario with this adjustment
                scenario_inputs = base_scenario['inputs'].copy()
                scenario_inputs[var_name] = adjusted_value
                
                # Calculate outputs for this scenario
                investment = scenario_inputs['investment']
                annual_benefit = scenario_inputs['annual_benefit']
                time_horizon = scenario_inputs['time_horizon']
                discount_rate = scenario_inputs['discount_rate']
                
                total_benefit = annual_benefit * time_horizon
                net_benefit = total_benefit - investment
                roi_percentage = (net_benefit / investment * 100) if investment > 0 else 0
                payback_period = investment / annual_benefit if annual_benefit > 0 else float('inf')
                
                # Calculate NPV
                npv = -investment
                for year in range(1, time_horizon + 1):
                    npv += annual_benefit / ((1 + discount_rate) ** year)
                
                # Store step results
                var_sensitivity['steps'].append({
                    'adjustment': adjustment,
                    'adjusted_value': adjusted_value,
                    'outputs': {
                        'total_benefit': total_benefit,
                        'net_benefit': net_benefit,
                        'roi_percentage': roi_percentage,
                        'payback_period': payback_period,
                        'npv': npv
                    }
                })
            
            # Calculate sensitivity metrics
            roi_values = [step['outputs']['roi_percentage'] for step in var_sensitivity['steps']]
            npv_values = [step['outputs']['npv'] for step in var_sensitivity['steps']]
            
            # Calculate range and variance
            roi_range = max(roi_values) - min(roi_values)
            npv_range = max(npv_values) - min(npv_values)
            
            roi_variance = statistics.variance(roi_values) if len(roi_values) > 1 else 0
            npv_variance = statistics.variance(npv_values) if len(npv_values) > 1 else 0
            
            # Calculate elasticity (percentage change in output / percentage change in input)
            max_adjustment = sensitivity_range
            max_roi_change = (max(roi_values) - base_scenario['outputs']['roi_percentage']) / base_scenario['outputs']['roi_percentage'] if base_scenario['outputs']['roi_percentage'] != 0 else 0
            max_npv_change = (max(npv_values) - base_scenario['outputs']['npv']) / base_scenario['outputs']['npv'] if base_scenario['outputs']['npv'] != 0 else 0
            
            roi_elasticity = max_roi_change / max_adjustment if max_adjustment != 0 else 0
            npv_elasticity = max_npv_change / max_adjustment if max_adjustment != 0 else 0
            
            # Store sensitivity metrics
            var_sensitivity['metrics'] = {
                'roi_range': roi_range,
                'npv_range': npv_range,
                'roi_variance': roi_variance,
                'npv_variance': npv_variance,
                'roi_elasticity': roi_elasticity,
                'npv_elasticity': npv_elasticity,
                'sensitivity_score': abs(roi_elasticity) + abs(npv_elasticity)
            }
            
            # Add to results
            results['variable_sensitivities'].append(var_sensitivity)
        
        # Calculate overall sensitivity summary
        if results['variable_sensitivities']:
            # Sort variables by sensitivity score
            results['variable_sensitivities'].sort(
                key=lambda x: x['metrics']['sensitivity_score'], 
                reverse=True
            )
            
            # Identify most sensitive variables
            most_sensitive = results['variable_sensitivities'][0]
            
            # Calculate overall metrics
            results['summary'] = {
                'most_sensitive_variable': most_sensitive['variable'],
                'most_sensitive_score': most_sensitive['metrics']['sensitivity_score'],
                'average_roi_elasticity': statistics.mean([v['metrics']['roi_elasticity'] for v in results['variable_sensitivities']]),
                'average_npv_elasticity': statistics.mean([v['metrics']['npv_elasticity'] for v in results['variable_sensitivities']]),
                'risk_level': self._calculate_risk_level([v['metrics']['sensitivity_score'] for v in results['variable_sensitivities']])
            }
        
        return results

    def _calculate_risk_level(self, sensitivity_scores: List[float]) -> str:
        """Calculate risk level based on sensitivity scores."""
        if not sensitivity_scores:
            return 'medium'
        
        max_score = max(sensitivity_scores)
        avg_score = statistics.mean(sensitivity_scores)
        
        if max_score > 2.0 or avg_score > 1.5:
            return 'high'
        elif max_score > 1.0 or avg_score > 0.8:
            return 'medium'
        else:
            return 'low'

    def _run_stress_test(self, base_scenario: Dict[str, Any], variables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a stress test based on the base scenario and variables."""
        # Initialize results storage
        results = {
            'name': 'Stress Test',
            'type': ScenarioType.STRESS_TEST.value,
            'base_scenario': base_scenario,
            'stress_scenarios': [],
            'summary': {}
        }
        
        # Define stress scenarios
        stress_scenarios = [
            {
                'name': 'Worst Case',
                'description': 'All variables at their worst case values',
                'adjustments': {}
            },
            {
                'name': 'Investment Overrun',
                'description': 'Investment costs 50% higher than expected',
                'adjustments': {'investment': 1.5}
            },
            {
                'name': 'Benefit Shortfall',
                'description': 'Benefits 40% lower than expected',
                'adjustments': {'annual_benefit': 0.6}
            },
            {
                'name': 'Delayed Benefits',
                'description': 'Benefits delayed by 1 year',
                'adjustments': {'time_horizon': lambda x: max(1, x - 1)}
            },
            {
                'name': 'High Discount Rate',
                'description': 'Discount rate doubled',
                'adjustments': {'discount_rate': lambda x: min(0.5, x * 2)}
            }
        ]
        
        # Run each stress scenario
        for scenario in stress_scenarios:
            # Create scenario inputs
            scenario_inputs = {}
            for key, value in base_scenario['inputs'].items():
                scenario_inputs[key] = value
            
            # Apply adjustments
            for var_name, adjustment in scenario['adjustments'].items():
                if var_name in scenario_inputs:
                    if callable(adjustment):
                        scenario_inputs[var_name] = adjustment(scenario_inputs[var_name])
                    else:
                        scenario_inputs[var_name] = scenario_inputs[var_name] * adjustment
            
            # For 'Worst Case', apply worst case for all variables
            if scenario['name'] == 'Worst Case':
                for variable in variables:
                    var_name = variable['name']
                    var_type = variable['type']
                    
                    if var_name in scenario_inputs:
                        # Apply worst case adjustment based on variable type
                        if var_type == VariableType.REVENUE.value:
                            # Decrease revenue by 40%
                            scenario_inputs[var_name] = scenario_inputs[var_name] * 0.6
                        elif var_type == VariableType.COST.value:
                            # Increase cost by 50%
                            scenario_inputs[var_name] = scenario_inputs[var_name] * 1.5
                        elif var_type in [VariableType.GROWTH_RATE.value, VariableType.ADOPTION_RATE.value, VariableType.EFFICIENCY_GAIN.value]:
                            # Decrease positive rates by 50%
                            scenario_inputs[var_name] = scenario_inputs[var_name] * 0.5
                        elif var_type in [VariableType.RISK_PROBABILITY.value, VariableType.RISK_IMPACT.value]:
                            # Increase risk factors by 50%
                            scenario_inputs[var_name] = min(1.0, scenario_inputs[var_name] * 1.5)
            
            # Calculate outputs for this scenario
            investment = scenario_inputs['investment']
            annual_benefit = scenario_inputs['annual_benefit']
            time_horizon = scenario_inputs['time_horizon']
            discount_rate = scenario_inputs['discount_rate']
            
            total_benefit = annual_benefit * time_horizon
            net_benefit = total_benefit - investment
            roi_percentage = (net_benefit / investment * 100) if investment > 0 else 0
            payback_period = investment / annual_benefit if annual_benefit > 0 else float('inf')
            
            # Calculate NPV
            npv = -investment
            for year in range(1, time_horizon + 1):
                npv += annual_benefit / ((1 + discount_rate) ** year)
            
            # Store scenario results
            results['stress_scenarios'].append({
                'name': scenario['name'],
                'description': scenario['description'],
                'inputs': scenario_inputs,
                'outputs': {
                    'total_benefit': total_benefit,
                    'net_benefit': net_benefit,
                    'roi_percentage': roi_percentage,
                    'payback_period': payback_period,
                    'npv': npv
                },
                'viability': roi_percentage > 0 and npv > 0
            })
        
        # Calculate summary statistics
        viable_scenarios = [s for s in results['stress_scenarios'] if s['viability']]
        viability_rate = len(viable_scenarios) / len(results['stress_scenarios'])
        
        # Calculate worst case metrics
        worst_case = next((s for s in results['stress_scenarios'] if s['name'] == 'Worst Case'), None)
        
        # Store summary
        results['summary'] = {
            'viability_rate': viability_rate,
            'worst_case_roi': worst_case['outputs']['roi_percentage'] if worst_case else None,
            'worst_case_npv': worst_case['outputs']['npv'] if worst_case else None,
            'worst_case_viable': worst_case['viability'] if worst_case else False,
            'risk_level': 'low' if viability_rate > 0.8 else 'medium' if viability_rate > 0.5 else 'high'
        }
        
        return results

    def _run_what_if_analysis(self, base_scenario: Dict[str, Any], custom_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a what-if analysis based on the base scenario and custom scenarios."""
        # Initialize results storage
        results = {
            'name': 'What-If Analysis',
            'type': ScenarioType.WHAT_IF.value,
            'base_scenario': base_scenario,
            'what_if_scenarios': [],
            'summary': {}
        }
        
        # Run each custom scenario
        for scenario_config in custom_scenarios:
            # Create custom scenario
            scenario = self._create_custom_scenario(base_scenario, scenario_config)
            
            # Add to results
            results['what_if_scenarios'].append(scenario)
        
        # Calculate summary statistics
        roi_values = [s['outputs']['roi_percentage'] for s in results['what_if_scenarios']]
        npv_values = [s['outputs']['npv'] for s in results['what_if_scenarios']]
        
        # Calculate ranges
        roi_range = max(roi_values) - min(roi_values)
        npv_range = max(npv_values) - min(npv_values)
        
        # Calculate best and worst scenarios
        best_scenario = max(results['what_if_scenarios'], key=lambda s: s['outputs']['roi_percentage'])
        worst_scenario = min(results['what_if_scenarios'], key=lambda s: s['outputs']['roi_percentage'])
        
        # Store summary
        results['summary'] = {
            'roi_range': roi_range,
            'npv_range': npv_range,
            'best_scenario': best_scenario['name'],
            'worst_scenario': worst_scenario['name'],
            'best_roi': best_scenario['outputs']['roi_percentage'],
            'worst_roi': worst_scenario['outputs']['roi_percentage'],
            'risk_level': 'low' if worst_scenario['outputs']['roi_percentage'] > 0 else 'high'
        }
        
        return results

    def _apply_dependencies(self, inputs: Dict[str, Any], adjusted_values: Dict[str, Any]) -> None:
        """Apply variable dependencies to ensure realistic scenarios."""
        if not self.dependency_matrix:
            return
        
        # Apply dependencies in multiple passes to handle chains of dependencies
        for _ in range(3):  # Limit to 3 passes to prevent infinite loops
            for var_name, dependencies in self.dependency_matrix.items():
                if var_name not in inputs:
                    continue
                
                for dep_var, relationship in dependencies.items():
                    if dep_var not in adjusted_values:
                        continue
                    
                    # Apply the relationship
                    if relationship['type'] == 'proportional':
                        # Direct proportional relationship
                        factor = relationship['factor']
                        change_pct = (adjusted_values[dep_var] / relationship['base_value']) - 1
                        inputs[var_name] = inputs[var_name] * (1 + change_pct * factor)
                    
                    elif relationship['type'] == 'inverse':
                        # Inverse relationship
                        factor = relationship['factor']
                        change_pct = (adjusted_values[dep_var] / relationship['base_value']) - 1
                        inputs[var_name] = inputs[var_name] * (1 - change_pct * factor)
                    
                    elif relationship['type'] == 'threshold':
                        # Threshold-based relationship
                        threshold = relationship['threshold']
                        if adjusted_values[dep_var] > threshold:
                            inputs[var_name] = inputs[var_name] * relationship['above_factor']
                        else:
                            inputs[var_name] = inputs[var_name] * relationship['below_factor']

    async def _retrieve_historical_scenarios(self, industry: str, scenario_type: str) -> List[Dict[str, Any]]:
        """Retrieve historical scenarios from MCP memory for reference."""
        try:
            # Search for similar scenarios in episodic memory
            query = {
                "entity_type": "scenario_analysis",
                "metadata.industry": industry,
                "metadata.scenario_type": scenario_type
            }
            
            historical_entities = await self.mcp_client.search_knowledge_graph_nodes(query, limit=5)
            
            historical_scenarios = []
            for entity in historical_entities:
                if hasattr(entity, 'data') and 'results' in entity.data:
                    historical_scenarios.append(entity.data['results'])
            
            logger.info(f"Retrieved {len(historical_scenarios)} historical scenarios for {industry}/{scenario_type}")
            return historical_scenarios
            
        except Exception as e:
            logger.warning(f"Failed to retrieve historical scenarios: {e}")
            return []

    async def _store_scenario_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Store scenario analysis results in MCP."""
        entity = KnowledgeEntity(
            entity_type="scenario_analysis",
            data={
                'scenario_analysis_id': f"scenario_{int(time.time())}",
                'scenario_type': analysis_data['type'],
                'base_scenario': analysis_data['base_scenario'],
                'results': analysis_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            metadata={
                'agent_id': self.agent_id,
                'scenario_type': analysis_data['type'],
                'timestamp': time.time()
            }
        )
        
        entities = await self.mcp_client.create_entities([entity])
        return entities.get('entity_ids', ['unknown'])[0]

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute scenario planning and analysis based on the provided inputs.
        
        Args:
            inputs: Dictionary containing:
                - scenario_type: Type of scenario analysis to perform
                - base_case: Base case data for scenario analysis
                - variables: List of variables to analyze
                - monte_carlo_iterations: Number of iterations for Monte Carlo simulation
                - sensitivity_range: Range for sensitivity analysis
                - sensitivity_steps: Number of steps for sensitivity analysis
                - custom_scenarios: List of custom scenarios for what-if analysis
                
        Returns:
            AgentResult with the scenario analysis results
        """
        start_time = time.monotonic()
        
        try:
            logger.info(f"Starting scenario analysis for agent {self.agent_id}")
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Validation failed: {validation_result.errors[0]}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Extract inputs
            scenario_type = inputs['scenario_type']
            base_case = inputs['base_case']
            variables = inputs.get('variables', [])
            monte_carlo_iterations = inputs.get('monte_carlo_iterations', self.default_monte_carlo_iterations)
            sensitivity_range = inputs.get('sensitivity_range', self.default_sensitivity_range)
            sensitivity_steps = inputs.get('sensitivity_steps', self.default_sensitivity_steps)
            custom_scenarios = inputs.get('custom_scenarios', [])
            
            # Create base scenario
            base_scenario = self._create_base_scenario(base_case)
            
            # Perform scenario analysis based on type
            if scenario_type == ScenarioType.BASE_CASE.value:
                # Just return the base scenario
                analysis_results = {
                    'type': ScenarioType.BASE_CASE.value,
                    'base_scenario': base_scenario,
                    'scenarios': [base_scenario]
                }
            
            elif scenario_type == ScenarioType.OPTIMISTIC.value:
                # Create optimistic scenario
                optimistic_scenario = self._create_optimistic_scenario(base_scenario, variables)
                
                analysis_results = {
                    'type': ScenarioType.OPTIMISTIC.value,
                    'base_scenario': base_scenario,
                    'scenarios': [base_scenario, optimistic_scenario]
                }
            
            elif scenario_type == ScenarioType.PESSIMISTIC.value:
                # Create pessimistic scenario
                pessimistic_scenario = self._create_pessimistic_scenario(base_scenario, variables)
                
                analysis_results = {
                    'type': ScenarioType.PESSIMISTIC.value,
                    'base_scenario': base_scenario,
                    'scenarios': [base_scenario, pessimistic_scenario]
                }
            
            elif scenario_type == ScenarioType.MONTE_CARLO.value:
                # Run Monte Carlo simulation
                monte_carlo_results = self._run_monte_carlo_simulation(base_scenario, variables, monte_carlo_iterations)
                
                analysis_results = {
                    'type': ScenarioType.MONTE_CARLO.value,
                    'base_scenario': base_scenario,
                    'monte_carlo_results': monte_carlo_results
                }
            
            elif scenario_type == ScenarioType.SENSITIVITY.value:
                # Run sensitivity analysis
                sensitivity_results = self._run_sensitivity_analysis(base_scenario, variables, sensitivity_range, sensitivity_steps)
                
                analysis_results = {
                    'type': ScenarioType.SENSITIVITY.value,
                    'base_scenario': base_scenario,
                    'sensitivity_results': sensitivity_results
                }
            
            elif scenario_type == ScenarioType.STRESS_TEST.value:
                # Run stress test
                stress_test_results = self._run_stress_test(base_scenario, variables)
                
                analysis_results = {
                    'type': ScenarioType.STRESS_TEST.value,
                    'base_scenario': base_scenario,
                    'stress_test_results': stress_test_results
                }
            
            elif scenario_type == ScenarioType.WHAT_IF.value:
                # Run what-if analysis
                what_if_results = self._run_what_if_analysis(base_scenario, custom_scenarios)
                
                analysis_results = {
                    'type': ScenarioType.WHAT_IF.value,
                    'base_scenario': base_scenario,
                    'what_if_results': what_if_results
                }
            
            else:
                # Create standard scenario set (base, optimistic, pessimistic)
                optimistic_scenario = self._create_optimistic_scenario(base_scenario, variables)
                pessimistic_scenario = self._create_pessimistic_scenario(base_scenario, variables)
                
                analysis_results = {
                    'type': 'standard',
                    'base_scenario': base_scenario,
                    'scenarios': [base_scenario, optimistic_scenario, pessimistic_scenario]
                }
            
            # Store analysis results in MCP
            analysis_id = await self._store_scenario_analysis(analysis_results)
            
            # Add analysis ID to results
            analysis_results['analysis_id'] = analysis_id
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Scenario analysis completed in {execution_time_ms}ms")
            
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=analysis_results,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"Scenario analysis failed: {str(e)}", exc_info=True)
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Scenario analysis failed: {str(e)}"},
                execution_time_ms=execution_time_ms
            )