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
        # Set up validation rules in config
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['drivers'],
                'field_types': {
                    'drivers': 'array',
                    'investment': 'number'
                },
                'field_constraints': {
                    'investment': {'min': 0.01}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        # Use shared calculation functions from utils
        self.calculation_functions = get_calculation_functions()

    # Calculation methods have been moved to agents.utils.calculations

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Perform ROI-specific validations beyond the standard validations."""
        errors = []
        
        # Check that drivers contain the expected structure
        drivers_data = inputs.get('drivers')
        if drivers_data:
            for i, pillar in enumerate(drivers_data):
                if not isinstance(pillar, dict):
                    errors.append(f"Pillar {i} must be an object")
                    continue
                    
                if 'pillar' not in pillar:
                    errors.append(f"Pillar {i} is missing required 'pillar' name field")
                    
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
        
        return errors
        
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
        # Use centralized validation
        validation_result = await self.validate_inputs(inputs)
        if not validation_result.is_valid:
            return AgentResult(
                status=AgentStatus.FAILED, 
                data={"error": validation_result.errors[0] if validation_result.errors else "Input validation failed"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
            
        drivers_data = inputs.get('drivers')
        total_investment = inputs.get('investment', 0.0)
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

        # Note: Investment validation is now handled by the centralized validation mechanism

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
