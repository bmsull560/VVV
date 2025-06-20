"""
Template Selector Agent Example

This module demonstrates how to implement a Template Selector Agent
that suggests relevant business case templates based on industry input
as part of the business case creation workflow.
"""

import logging
import time
from typing import Dict, Any, List, Optional
import re

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class TemplateSelectorAgent(BaseAgent):
    """
    Agent that suggests relevant business case templates based on industry input.
    
    This agent demonstrates the use of the centralized input validation system
    and integration with the business case creation workflow.
    """

    def __init__(self, agent_id: str, mcp_client: Any, config: Dict[str, Any]):
        """
        Initialize the Template Selector Agent with validation rules.
        
        Args:
            agent_id: Unique identifier for this agent
            mcp_client: MCP client instance for memory access
            config: Configuration dictionary
        """
        # Define validation rules in config
        if 'input_validation' not in config:
            config['input_validation'] = {
                # Fields that must be present
                'required_fields': ['industry'],
                
                # Type checking for fields
                'field_types': {
                    'industry': 'string',
                    'company_size': 'string',
                    'project_name': 'string',
                    'client_name': 'string'
                },
                
                # Constraints for fields
                'field_constraints': {
                    'industry': {
                        'min_length': 2,
                        'max_length': 100
                    },
                    'company_size': {
                        'enum': ['small', 'medium', 'enterprise']
                    }
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Load template data from MCP or use defaults
        self._templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """
        Load template data from MCP or use defaults.
        
        In a real implementation, this would load from the MCP client.
        
        Returns:
            Dict containing template definitions
        """
        # This is a simplified example - in production, templates would be loaded from MCP
        return {
            "healthcare": [
                {
                    "id": "healthcare_roi_template_001",
                    "name": "Healthcare Cost Reduction ROI Template",
                    "description": "Focuses on operational efficiency and cost reduction in healthcare settings",
                    "recommended_for": ["hospital", "clinic", "healthcare provider"],
                    "sections": ["Executive Summary", "Current State Analysis", "Solution Overview", 
                                "Cost Reduction Analysis", "Implementation Timeline", "ROI Calculation"]
                },
                {
                    "id": "healthcare_patient_outcomes_002",
                    "name": "Patient Outcomes Improvement Template",
                    "description": "Emphasizes improvements in patient care quality and outcomes",
                    "recommended_for": ["hospital", "healthcare provider", "medical practice"],
                    "sections": ["Executive Summary", "Current Patient Metrics", "Solution Overview", 
                                "Outcome Improvements", "Implementation Plan", "ROI and Value Analysis"]
                }
            ],
            "manufacturing": [
                {
                    "id": "manufacturing_efficiency_001",
                    "name": "Manufacturing Efficiency Template",
                    "description": "Focuses on production efficiency and waste reduction",
                    "recommended_for": ["manufacturer", "production facility"],
                    "sections": ["Executive Summary", "Current Production Analysis", "Solution Overview", 
                                "Efficiency Gains", "Implementation Timeline", "ROI Calculation"]
                },
                {
                    "id": "manufacturing_quality_002",
                    "name": "Quality Improvement Template",
                    "description": "Emphasizes quality control and defect reduction",
                    "recommended_for": ["manufacturer", "production facility"],
                    "sections": ["Executive Summary", "Current Quality Metrics", "Solution Overview", 
                                "Quality Improvements", "Implementation Plan", "ROI and Value Analysis"]
                }
            ],
            "finance": [
                {
                    "id": "finance_risk_001",
                    "name": "Financial Risk Mitigation Template",
                    "description": "Focuses on risk reduction and compliance",
                    "recommended_for": ["bank", "financial institution", "insurance"],
                    "sections": ["Executive Summary", "Risk Assessment", "Solution Overview", 
                                "Risk Mitigation Strategy", "Implementation Timeline", "ROI Calculation"]
                }
            ],
            "default": [
                {
                    "id": "general_roi_001",
                    "name": "General ROI Analysis Template",
                    "description": "General purpose ROI analysis for any industry",
                    "recommended_for": ["any"],
                    "sections": ["Executive Summary", "Current State", "Solution Overview", 
                                "Value Analysis", "Implementation Plan", "ROI Calculation"]
                }
            ]
        }
    
    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Perform template selector-specific validations.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            List[str]: List of error messages (empty if all validations pass)
        """
        errors = []
        
        # Check that industry is not just whitespace
        industry = inputs.get('industry', '')
        if isinstance(industry, str) and industry.strip() == '':
            errors.append("Industry must not be empty or whitespace")
        
        # Normalize company_size if present
        if 'company_size' in inputs and isinstance(inputs['company_size'], str):
            size = inputs['company_size'].lower()
            if size in ['small', 'small business', 'smb']:
                inputs['company_size'] = 'small'
            elif size in ['medium', 'mid-market', 'mid market', 'midsize']:
                inputs['company_size'] = 'medium'
            elif size in ['large', 'enterprise', 'corporation']:
                inputs['company_size'] = 'enterprise'
            else:
                errors.append(f"Unrecognized company size: {inputs['company_size']}")
        
        return errors
    
    async def _find_matching_templates(self, industry: str, company_size: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find templates that match the given industry and company size.
        
        Args:
            industry: Industry name to match
            company_size: Optional company size to further filter templates
            
        Returns:
            List of matching template dictionaries
        """
        # Normalize industry name for matching
        industry_lower = industry.lower()
        
        # Find exact industry match first
        matching_templates = self._templates.get(industry_lower, [])
        
        # If no exact match, try to find partial matches
        if not matching_templates:
            for ind, templates in self._templates.items():
                if ind != 'default' and (ind in industry_lower or industry_lower in ind):
                    matching_templates.extend(templates)
        
        # If still no matches, use default templates
        if not matching_templates:
            matching_templates = self._templates.get('default', [])
        
        # Filter by company size if provided
        if company_size and matching_templates:
            # This is a simplified example - in production, we would have more sophisticated matching logic
            # For now, we'll just prioritize templates that might be more relevant for the company size
            if company_size == 'enterprise':
                # Move more comprehensive templates to the front
                matching_templates.sort(key=lambda t: len(t.get('sections', [])), reverse=True)
            elif company_size == 'small':
                # Move simpler templates to the front
                matching_templates.sort(key=lambda t: len(t.get('sections', [])))
        
        return matching_templates
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute the template selection logic after validation.
        
        Args:
            inputs: Dictionary of validated input values
            
        Returns:
            AgentResult: Result of the agent execution with suggested templates
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
        industry = inputs['industry']
        company_size = inputs.get('company_size')
        project_name = inputs.get('project_name', '')
        client_name = inputs.get('client_name', '')
        
        # Find matching templates
        matching_templates = await self._find_matching_templates(industry, company_size)
        
        # Log the result
        logger.info(f"Found {len(matching_templates)} matching templates for industry '{industry}'")
        
        # Prepare result data
        result_data = {
            "suggested_templates": matching_templates,
            "industry": industry,
            "company_size": company_size,
            "match_count": len(matching_templates),
            "project_name": project_name,
            "client_name": client_name
        }
        
        # Return successful result
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=result_data,
            execution_time_ms=int((time.monotonic() - start_time) * 1000)
        )
