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
        # Set up validation rules in config
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['drivers', 'investment'],
                'field_types': {
                    'drivers': 'array',
                    'investment': 'number',
                    'variations': 'array'
                },
                'field_constraints': {
                    'investment': {'min': 0.01}
                }
            }
            
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

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Perform sensitivity analysis-specific validations beyond the standard validations."""
        errors = []
        
        # Check that drivers contain the expected structure
        drivers_data = inputs.get('drivers')
        if drivers_data:
            for i, pillar in enumerate(drivers_data):
                if not isinstance(pillar, dict):
                    errors.append(f"Pillar {i} must be an object")
                    continue
                    
                if 'tier_2_drivers' not in pillar or not isinstance(pillar.get('tier_2_drivers'), list):
                    errors.append(f"Pillar {i} is missing required 'tier_2_drivers' array")
                    continue
                    
                # Check tier 2 drivers
                for j, driver in enumerate(pillar.get('tier_2_drivers', [])):
                    if not isinstance(driver, dict):
                        errors.append(f"Driver {j} in pillar {i} must be an object")
                        continue
                        
                    if 'name' not in driver:
                        errors.append(f"Driver {j} in pillar {i} is missing required 'name' field")
                        
                    if 'tier_3_metrics' not in driver or not isinstance(driver.get('tier_3_metrics'), dict):
                        errors.append(f"Driver {j} in pillar {i} is missing required 'tier_3_metrics' object")
        
        # Convert investment to float if it's a string number
        if 'investment' in inputs and isinstance(inputs['investment'], str):
            try:
                inputs['investment'] = float(inputs['investment'])
            except (ValueError, TypeError):
                errors.append(f"Invalid investment value: '{inputs['investment']}'. Must be a number.")
        
        # Validate variations structure if provided
        variations = inputs.get('variations')
        if variations is not None:
            if not isinstance(variations, list):
                errors.append(f"Input 'variations' must be a list, got {type(variations)}.")
            else:
                for i, variation in enumerate(variations):
                    if not isinstance(variation, dict):
                        errors.append(f"Variation {i} must be an object")
                        continue
                        
                    # Check required fields in each variation
                    required_fields = ['tier_3_metric_name', 'tier_2_driver_name', 'percentage_changes']
                    for field in required_fields:
                        if field not in variation:
                            errors.append(f"Variation {i} is missing required field '{field}'")
                    
                    # Check that percentage_changes is a list
                    if 'percentage_changes' in variation and not isinstance(variation['percentage_changes'], list):
                        errors.append(f"Variation {i} field 'percentage_changes' must be a list")
        
        return errors
        
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
        # Use centralized validation
        validation_result = await self.validate_inputs(inputs)
        if not validation_result.is_valid:
            return AgentResult(
                status=AgentStatus.FAILED, 
                data={"error": validation_result.errors[0] if validation_result.errors else "Input validation failed"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
            
        base_drivers = inputs.get('drivers')
        base_investment = inputs.get('investment')
        
        # If variations is None (not provided), default to an empty list to run 0 scenarios.
        variations = inputs.get('variations', [])
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
