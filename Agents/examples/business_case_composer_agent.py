"""
Business Case Composer Agent Example

This module demonstrates how to implement a Business Case Composer Agent
that orchestrates the assembly of a complete business case by integrating
data from multiple sources and agents in the business case creation workflow.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from decimal import Decimal
import json

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class BusinessCaseComposerAgent(BaseAgent):
    """
    Agent that orchestrates the assembly of a complete business case.
    
    This agent demonstrates the use of the centralized input validation system
    and integration of data from multiple sources to create a comprehensive
    business case document.
    """

    def __init__(self, agent_id: str, mcp_client: Any, config: Dict[str, Any]):
        """
        Initialize the Business Case Composer Agent with validation rules.
        
        Args:
            agent_id: Unique identifier for this agent
            mcp_client: MCP client instance for memory access
            config: Configuration dictionary
        """
        # Define validation rules in config
        if 'input_validation' not in config:
            config['input_validation'] = {
                # Fields that must be present
                'required_fields': ['project_name', 'client_name', 'industry', 'value_drivers'],
                
                # Type checking for fields
                'field_types': {
                    'project_name': 'string',
                    'client_name': 'string',
                    'industry': 'string',
                    'value_drivers': 'array',
                    'stakeholder_persona': 'string',
                    'template_id': 'string',
                    'metrics_data': 'object',
                    'investment_amount': 'number'
                },
                
                # Constraints for fields
                'field_constraints': {
                    'project_name': {
                        'min_length': 3,
                        'max_length': 100
                    },
                    'client_name': {
                        'min_length': 2,
                        'max_length': 100
                    },
                    'value_drivers': {
                        'min_items': 1,
                        'item_type': 'string'
                    }
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
    
    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Perform business case composer-specific validations.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            List[str]: List of error messages (empty if all validations pass)
        """
        errors = []
        
        # Validate value drivers
        valid_drivers = ["cost_reduction", "revenue_growth", "productivity_gains", "risk_mitigation"]
        value_drivers = inputs.get('value_drivers', [])
        
        if isinstance(value_drivers, list):
            for driver in value_drivers:
                if driver not in valid_drivers:
                    errors.append(f"Unrecognized value driver: {driver}. Valid drivers are: {', '.join(valid_drivers)}")
        
        # Validate metrics data if provided
        metrics_data = inputs.get('metrics_data', {})
        if metrics_data:
            # Check that metrics data contains entries for each selected value driver
            for driver in value_drivers:
                if driver not in metrics_data:
                    errors.append(f"Missing metrics data for value driver: {driver}")
        
        # Convert investment amount to float if it's a string number
        if 'investment_amount' in inputs and isinstance(inputs['investment_amount'], str):
            try:
                inputs['investment_amount'] = float(inputs['investment_amount'])
            except (ValueError, TypeError):
                errors.append(f"Invalid investment amount: '{inputs['investment_amount']}'. Must be a number.")
        
        return errors
    
    async def _retrieve_workflow_context(self) -> Dict[str, Any]:
        """
        Retrieve the current workflow context from MCP.
        
        Returns:
            Dictionary containing workflow context data
        """
        # In a real implementation, this would use the MCP client to retrieve workflow context
        # For this example, we'll return a simplified context
        return {
            "workflow_id": "sample_workflow_123",
            "user_id": "sample_user",
            "customer_id": "sample_customer",
            "workflow_start_time": time.time() - 3600,  # 1 hour ago
            "current_step": "review_and_generate"
        }
    
    async def _calculate_roi_metrics(self, value_drivers: List[str], 
                                    metrics_data: Dict[str, Any],
                                    investment_amount: float) -> Dict[str, Any]:
        """
        Calculate ROI metrics based on value driver data.
        
        Args:
            value_drivers: List of selected value drivers
            metrics_data: Dictionary containing metrics for each value driver
            investment_amount: Total investment amount
            
        Returns:
            Dictionary containing calculated ROI metrics
        """
        # In a real implementation, this would use the ROI Calculator Agent
        # For this example, we'll calculate simplified metrics
        
        total_annual_benefit = 0.0
        benefits_by_driver = {}
        
        # Calculate benefits for each value driver
        for driver in value_drivers:
            driver_data = metrics_data.get(driver, {})
            driver_benefit = 0.0
            
            if driver == "cost_reduction":
                current_cost = driver_data.get("current_operational_cost", 0)
                reduction_pct = driver_data.get("expected_cost_reduction_percentage", 0) / 100
                driver_benefit = current_cost * reduction_pct
                
            elif driver == "revenue_growth":
                current_revenue = driver_data.get("current_annual_revenue", 0)
                growth_pct = driver_data.get("expected_revenue_growth_percentage", 0) / 100
                driver_benefit = current_revenue * growth_pct
                
            elif driver == "productivity_gains":
                process_time = driver_data.get("current_process_time", 0)
                time_savings_pct = driver_data.get("expected_time_savings_percentage", 0) / 100
                employee_count = driver_data.get("affected_employee_count", 0)
                hourly_rate = driver_data.get("average_hourly_rate", 0)
                
                annual_hours_saved = process_time * time_savings_pct * employee_count * 52  # 52 weeks
                driver_benefit = annual_hours_saved * hourly_rate
                
            elif driver == "risk_mitigation":
                risk_cost = driver_data.get("current_annual_risk_cost", 0)
                risk_probability = driver_data.get("risk_probability_percentage", 0) / 100
                risk_reduction = driver_data.get("expected_risk_reduction_percentage", 0) / 100
                
                driver_benefit = risk_cost * risk_probability * risk_reduction
            
            benefits_by_driver[driver] = driver_benefit
            total_annual_benefit += driver_benefit
        
        # Calculate ROI metrics
        annual_roi_percentage = (total_annual_benefit / investment_amount) * 100 if investment_amount > 0 else 0
        three_year_roi_percentage = annual_roi_percentage * 3
        
        # Calculate payback period (in months)
        payback_period_months = (investment_amount / total_annual_benefit) * 12 if total_annual_benefit > 0 else float('inf')
        
        # Calculate NPV (simplified)
        discount_rate = 0.10  # 10% annual discount rate
        npv = -investment_amount
        for year in range(1, 4):  # 3 years
            npv += total_annual_benefit / ((1 + discount_rate) ** year)
        
        return {
            "total_annual_benefit": total_annual_benefit,
            "benefits_by_driver": benefits_by_driver,
            "annual_roi_percentage": annual_roi_percentage,
            "three_year_roi_percentage": three_year_roi_percentage,
            "payback_period_months": payback_period_months,
            "net_present_value": npv,
            "investment_amount": investment_amount
        }
    
    async def _generate_business_case_structure(self, template_id: str, 
                                              stakeholder_persona: str) -> Dict[str, Any]:
        """
        Generate the structure of the business case based on template and persona.
        
        Args:
            template_id: ID of the selected template
            stakeholder_persona: Selected stakeholder persona
            
        Returns:
            Dictionary containing business case structure
        """
        # In a real implementation, this would retrieve the template from MCP
        # For this example, we'll use a simplified structure
        
        # Base structure common to all templates
        base_structure = {
            "sections": [
                {
                    "id": "executive_summary",
                    "title": "Executive Summary",
                    "order": 1
                },
                {
                    "id": "problem_statement",
                    "title": "Problem Statement",
                    "order": 2
                },
                {
                    "id": "proposed_solution",
                    "title": "Proposed Solution",
                    "order": 3
                },
                {
                    "id": "value_analysis",
                    "title": "Value Analysis",
                    "order": 4
                },
                {
                    "id": "roi_calculation",
                    "title": "ROI Calculation",
                    "order": 5
                },
                {
                    "id": "implementation_plan",
                    "title": "Implementation Plan",
                    "order": 6
                },
                {
                    "id": "conclusion",
                    "title": "Conclusion",
                    "order": 7
                }
            ]
        }
        
        # Customize based on template ID
        if template_id.startswith("healthcare"):
            base_structure["sections"].insert(5, {
                "id": "regulatory_compliance",
                "title": "Regulatory Compliance",
                "order": 6
            })
            # Shift subsequent sections
            for i in range(5, len(base_structure["sections"])):
                base_structure["sections"][i]["order"] += 1
                
        elif template_id.startswith("finance"):
            base_structure["sections"].insert(5, {
                "id": "risk_assessment",
                "title": "Risk Assessment",
                "order": 6
            })
            # Shift subsequent sections
            for i in range(5, len(base_structure["sections"])):
                base_structure["sections"][i]["order"] += 1
        
        # Customize based on stakeholder persona
        if stakeholder_persona.lower() == "financial_buyer":
            # Emphasize financial sections
            base_structure["emphasis"] = ["roi_calculation", "value_analysis"]
            base_structure["tone"] = "analytical"
            
        elif stakeholder_persona.lower() == "technical_buyer":
            # Emphasize technical sections
            base_structure["emphasis"] = ["proposed_solution", "implementation_plan"]
            base_structure["tone"] = "technical"
            
        elif stakeholder_persona.lower() == "executive":
            # Emphasize executive summary and high-level value
            base_structure["emphasis"] = ["executive_summary", "conclusion"]
            base_structure["tone"] = "strategic"
        
        return base_structure
    
    async def _store_business_case(self, business_case_data: Dict[str, Any]) -> str:
        """
        Store the generated business case in MCP.
        
        Args:
            business_case_data: Complete business case data
            
        Returns:
            String ID of the stored business case
        """
        # In a real implementation, this would use the MCP client to store the business case
        # For this example, we'll simulate storage
        logger.info("Storing business case in MCP")
        
        # Simulate storage
        business_case_id = f"bc_{int(time.time())}"
        
        return business_case_id
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute the business case composition logic after validation.
        
        Args:
            inputs: Dictionary of validated input values
            
        Returns:
            AgentResult: Result of the agent execution with the composed business case
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
        project_name = inputs['project_name']
        client_name = inputs['client_name']
        industry = inputs['industry']
        value_drivers = inputs['value_drivers']
        stakeholder_persona = inputs.get('stakeholder_persona', 'general')
        template_id = inputs.get('template_id', 'general_roi_001')
        metrics_data = inputs.get('metrics_data', {})
        investment_amount = inputs.get('investment_amount', 0.0)
        
        # Retrieve workflow context
        workflow_context = await self._retrieve_workflow_context()
        
        # Calculate ROI metrics
        roi_metrics = await self._calculate_roi_metrics(
            value_drivers, metrics_data, investment_amount
        )
        
        # Generate business case structure
        business_case_structure = await self._generate_business_case_structure(
            template_id, stakeholder_persona
        )
        
        # Assemble the complete business case
        business_case = {
            "metadata": {
                "project_name": project_name,
                "client_name": client_name,
                "industry": industry,
                "created_at": time.time(),
                "created_by": workflow_context.get("user_id"),
                "template_id": template_id,
                "stakeholder_persona": stakeholder_persona
            },
            "structure": business_case_structure,
            "value_drivers": value_drivers,
            "roi_metrics": roi_metrics,
            "metrics_data": metrics_data,
            "workflow_id": workflow_context.get("workflow_id")
        }
        
        # Store the business case in MCP
        business_case_id = await self._store_business_case(business_case)
        
        # Prepare result data
        result_data = {
            "business_case_id": business_case_id,
            "project_name": project_name,
            "client_name": client_name,
            "roi_summary": {
                "total_annual_benefit": roi_metrics["total_annual_benefit"],
                "annual_roi_percentage": roi_metrics["annual_roi_percentage"],
                "payback_period_months": roi_metrics["payback_period_months"]
            },
            "section_count": len(business_case_structure["sections"]),
            "value_driver_count": len(value_drivers)
        }
        
        # Log success
        logger.info(f"Successfully composed business case for {client_name}: {project_name}")
        
        # Return successful result
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=result_data,
            execution_time_ms=int((time.monotonic() - start_time) * 1000)
        )
