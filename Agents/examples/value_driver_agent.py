"""
Value Driver Agent Example

This module demonstrates how to implement a Value Driver Agent
that suggests specific metrics based on selected value drivers
as part of the business case creation workflow.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from decimal import Decimal

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class ValueDriverAgent(BaseAgent):
    """
    Agent that suggests metrics based on selected value drivers.
    
    This agent demonstrates the use of the centralized input validation system
    and integration with the business case creation workflow.
    """

    def __init__(self, agent_id: str, mcp_client: Any, config: Dict[str, Any]):
        """
        Initialize the Value Driver Agent with validation rules.
        
        Args:
            agent_id: Unique identifier for this agent
            mcp_client: MCP client instance for memory access
            config: Configuration dictionary
        """
        # Define validation rules in config
        if 'input_validation' not in config:
            config['input_validation'] = {
                # Fields that must be present
                'required_fields': ['selected_drivers'],
                
                # Type checking for fields
                'field_types': {
                    'selected_drivers': 'array',
                    'industry': 'string',
                    'company_size': 'string'
                },
                
                # Constraints for fields
                'field_constraints': {
                    'selected_drivers': {
                        'min_items': 1,
                        'item_type': 'string'
                    }
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Load metric definitions from MCP or use defaults
        self._metrics_by_driver = self._load_metrics_by_driver()
    
    def _load_metrics_by_driver(self) -> Dict[str, Any]:
        """
        Load metric definitions from MCP or use defaults.
        
        In a real implementation, this would load from the MCP client.
        
        Returns:
            Dict containing metric definitions by driver type
        """
        # This is a simplified example - in production, metrics would be loaded from MCP
        return {
            "cost_reduction": {
                "base_metrics": [
                    {
                        "id": "current_operational_cost",
                        "name": "Current Operational Cost",
                        "description": "The current annual operational cost in the target area",
                        "type": "number",
                        "unit": "currency",
                        "required": True
                    },
                    {
                        "id": "expected_cost_reduction_percentage",
                        "name": "Expected Cost Reduction Percentage",
                        "description": "The expected percentage reduction in operational costs",
                        "type": "number",
                        "unit": "percentage",
                        "min": 0,
                        "max": 100,
                        "required": True
                    }
                ],
                "industry_specific": {
                    "healthcare": [
                        {
                            "id": "current_readmission_rate",
                            "name": "Current Readmission Rate",
                            "description": "The current patient readmission rate",
                            "type": "number",
                            "unit": "percentage",
                            "min": 0,
                            "max": 100
                        },
                        {
                            "id": "expected_readmission_reduction",
                            "name": "Expected Readmission Reduction",
                            "description": "The expected reduction in readmission rate",
                            "type": "number",
                            "unit": "percentage",
                            "min": 0,
                            "max": 100
                        }
                    ],
                    "manufacturing": [
                        {
                            "id": "current_defect_rate",
                            "name": "Current Defect Rate",
                            "description": "The current manufacturing defect rate",
                            "type": "number",
                            "unit": "percentage",
                            "min": 0,
                            "max": 100
                        },
                        {
                            "id": "expected_defect_reduction",
                            "name": "Expected Defect Reduction",
                            "description": "The expected reduction in defect rate",
                            "type": "number",
                            "unit": "percentage",
                            "min": 0,
                            "max": 100
                        }
                    ]
                }
            },
            "revenue_growth": {
                "base_metrics": [
                    {
                        "id": "current_annual_revenue",
                        "name": "Current Annual Revenue",
                        "description": "The current annual revenue in the target area",
                        "type": "number",
                        "unit": "currency",
                        "required": True
                    },
                    {
                        "id": "expected_revenue_growth_percentage",
                        "name": "Expected Revenue Growth Percentage",
                        "description": "The expected percentage increase in revenue",
                        "type": "number",
                        "unit": "percentage",
                        "min": 0,
                        "required": True
                    }
                ],
                "industry_specific": {
                    "retail": [
                        {
                            "id": "current_customer_acquisition_cost",
                            "name": "Current Customer Acquisition Cost",
                            "description": "The current cost to acquire a new customer",
                            "type": "number",
                            "unit": "currency"
                        },
                        {
                            "id": "expected_cac_reduction",
                            "name": "Expected CAC Reduction",
                            "description": "The expected reduction in customer acquisition cost",
                            "type": "number",
                            "unit": "percentage",
                            "min": 0,
                            "max": 100
                        }
                    ]
                }
            },
            "productivity_gains": {
                "base_metrics": [
                    {
                        "id": "current_process_time",
                        "name": "Current Process Time",
                        "description": "The current time required to complete the process",
                        "type": "number",
                        "unit": "hours",
                        "required": True
                    },
                    {
                        "id": "expected_time_savings_percentage",
                        "name": "Expected Time Savings Percentage",
                        "description": "The expected percentage reduction in process time",
                        "type": "number",
                        "unit": "percentage",
                        "min": 0,
                        "max": 100,
                        "required": True
                    },
                    {
                        "id": "affected_employee_count",
                        "name": "Affected Employee Count",
                        "description": "The number of employees affected by the process",
                        "type": "integer",
                        "min": 1,
                        "required": True
                    },
                    {
                        "id": "average_hourly_rate",
                        "name": "Average Hourly Rate",
                        "description": "The average hourly rate of affected employees",
                        "type": "number",
                        "unit": "currency",
                        "min": 0,
                        "required": True
                    }
                ]
            },
            "risk_mitigation": {
                "base_metrics": [
                    {
                        "id": "current_annual_risk_cost",
                        "name": "Current Annual Risk Cost",
                        "description": "The current estimated annual cost of the risk",
                        "type": "number",
                        "unit": "currency",
                        "required": True
                    },
                    {
                        "id": "risk_probability_percentage",
                        "name": "Risk Probability Percentage",
                        "description": "The probability of the risk occurring",
                        "type": "number",
                        "unit": "percentage",
                        "min": 0,
                        "max": 100,
                        "required": True
                    },
                    {
                        "id": "expected_risk_reduction_percentage",
                        "name": "Expected Risk Reduction Percentage",
                        "description": "The expected percentage reduction in risk probability",
                        "type": "number",
                        "unit": "percentage",
                        "min": 0,
                        "max": 100,
                        "required": True
                    }
                ],
                "industry_specific": {
                    "finance": [
                        {
                            "id": "current_compliance_violation_rate",
                            "name": "Current Compliance Violation Rate",
                            "description": "The current rate of compliance violations",
                            "type": "number",
                            "unit": "percentage",
                            "min": 0,
                            "max": 100
                        },
                        {
                            "id": "average_violation_cost",
                            "name": "Average Violation Cost",
                            "description": "The average cost per compliance violation",
                            "type": "number",
                            "unit": "currency",
                            "min": 0
                        }
                    ]
                }
            }
        }
    
    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Perform value driver-specific validations.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            List[str]: List of error messages (empty if all validations pass)
        """
        errors = []
        
        # Validate that selected drivers are recognized
        valid_drivers = ["cost_reduction", "revenue_growth", "productivity_gains", "risk_mitigation"]
        selected_drivers = inputs.get('selected_drivers', [])
        
        if isinstance(selected_drivers, list):
            for driver in selected_drivers:
                if driver not in valid_drivers:
                    errors.append(f"Unrecognized driver type: {driver}. Valid types are: {', '.join(valid_drivers)}")
        
        return errors
    
    async def _get_suggested_metrics(self, selected_drivers: List[str], industry: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get suggested metrics for the selected value drivers.
        
        Args:
            selected_drivers: List of selected value driver types
            industry: Optional industry to get industry-specific metrics
            
        Returns:
            Dictionary mapping driver types to lists of suggested metrics
        """
        suggested_metrics = {}
        
        for driver in selected_drivers:
            if driver in self._metrics_by_driver:
                driver_metrics = []
                
                # Add base metrics for this driver
                driver_metrics.extend(self._metrics_by_driver[driver].get('base_metrics', []))
                
                # Add industry-specific metrics if applicable
                if industry and industry.lower() in self._metrics_by_driver[driver].get('industry_specific', {}):
                    driver_metrics.extend(
                        self._metrics_by_driver[driver]['industry_specific'][industry.lower()]
                    )
                
                suggested_metrics[driver] = driver_metrics
        
        return suggested_metrics
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute the value driver metric suggestion logic after validation.
        
        Args:
            inputs: Dictionary of validated input values
            
        Returns:
            AgentResult: Result of the agent execution with suggested metrics
        """
        start_time = time.monotonic()
        
        # Use centralized validation
        validation_result = await self.validate_inputs(inputs)
        if not validation_result.is_valid:
            return AgentResult(
                status=AgentStatus.FAILED, 
                data={"error": validation_result.errors}, 
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
        
        # Extract validated inputs
        selected_drivers = inputs['selected_drivers']
        industry = inputs.get('industry')
        
        # Get suggested metrics for the selected drivers
        suggested_metrics = await self._get_suggested_metrics(selected_drivers, industry)
        
        # Log the result
        logger.info(f"Suggested metrics for {len(selected_drivers)} drivers")
        
        # Calculate total number of suggested metrics
        total_metric_count = sum(len(metrics) for metrics in suggested_metrics.values())
        
        # Prepare result data
        result_data = {
            "suggested_metrics": suggested_metrics,
            "selected_drivers": selected_drivers,
            "industry": industry,
            "total_metric_count": total_metric_count
        }
        
        # Return successful result
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=result_data,
            execution_time_ms=int((time.monotonic() - start_time) * 1000)
        )
