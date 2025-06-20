"""
Narrative Generator Agent Example

This module demonstrates how to implement a Narrative Generator Agent
that creates compelling business case narratives tailored to specific stakeholder personas.
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional
import re

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class NarrativeGeneratorAgent(BaseAgent):
    """
    Agent that creates compelling business case narratives tailored to specific stakeholder personas.
    
    This agent demonstrates the use of the centralized input validation system
    and generation of narrative content based on business case data and stakeholder persona.
    """

    def __init__(self, agent_id: str, mcp_client: Any, config: Dict[str, Any]):
        """
        Initialize the Narrative Generator Agent with validation rules.
        
        Args:
            agent_id: Unique identifier for this agent
            mcp_client: MCP client instance for memory access
            config: Configuration dictionary
        """
        # Define validation rules in config
        if 'input_validation' not in config:
            config['input_validation'] = {
                # Fields that must be present
                'required_fields': ['business_case_id', 'section_id', 'stakeholder_persona'],
                
                # Type checking for fields
                'field_types': {
                    'business_case_id': 'string',
                    'section_id': 'string',
                    'stakeholder_persona': 'string',
                    'tone': 'string',
                    'max_length': 'number',
                    'include_metrics': 'boolean',
                    'highlight_keywords': 'array'
                },
                
                # Constraints for fields
                'field_constraints': {
                    'section_id': {
                        'enum': [
                            'executive_summary', 
                            'problem_statement', 
                            'proposed_solution',
                            'value_analysis',
                            'roi_calculation',
                            'implementation_plan',
                            'conclusion',
                            'regulatory_compliance',
                            'risk_assessment'
                        ]
                    },
                    'stakeholder_persona': {
                        'enum': [
                            'executive', 
                            'financial_buyer', 
                            'technical_buyer',
                            'end_user',
                            'procurement',
                            'general'
                        ]
                    },
                    'tone': {
                        'enum': [
                            'formal',
                            'technical',
                            'persuasive',
                            'analytical',
                            'conversational'
                        ]
                    },
                    'max_length': {
                        'min': 100,
                        'max': 5000
                    },
                    'highlight_keywords': {
                        'item_type': 'string'
                    }
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Initialize persona profiles
        self.persona_profiles = {
            "executive": {
                "focus": "strategic impact and bottom-line results",
                "metrics_emphasis": ["roi", "payback_period", "revenue_impact"],
                "language_style": "concise, high-level, business-focused",
                "default_tone": "persuasive"
            },
            "financial_buyer": {
                "focus": "financial justification and risk assessment",
                "metrics_emphasis": ["npv", "irr", "cost_savings", "tco"],
                "language_style": "detailed, analytical, numbers-driven",
                "default_tone": "analytical"
            },
            "technical_buyer": {
                "focus": "technical implementation and integration",
                "metrics_emphasis": ["efficiency_gains", "technical_specifications", "compatibility"],
                "language_style": "precise, technical, solution-oriented",
                "default_tone": "technical"
            },
            "end_user": {
                "focus": "usability and day-to-day benefits",
                "metrics_emphasis": ["time_savings", "ease_of_use", "productivity_gains"],
                "language_style": "practical, benefit-focused, accessible",
                "default_tone": "conversational"
            },
            "procurement": {
                "focus": "vendor comparison and contractual terms",
                "metrics_emphasis": ["cost_comparison", "vendor_reliability", "contract_terms"],
                "language_style": "formal, comparative, detail-oriented",
                "default_tone": "formal"
            },
            "general": {
                "focus": "balanced view of benefits and implementation",
                "metrics_emphasis": ["roi", "implementation_timeline", "key_benefits"],
                "language_style": "balanced, comprehensive, clear",
                "default_tone": "formal"
            }
        }
    
    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Perform narrative generator-specific validations.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            List[str]: List of error messages (empty if all validations pass)
        """
        errors = []
        
        # Validate that business_case_id follows expected format
        business_case_id = inputs.get('business_case_id', '')
        if not re.match(r'^bc_\d+$', business_case_id):
            errors.append(f"Invalid business case ID format: {business_case_id}. Expected format: 'bc_' followed by numbers.")
        
        # Validate that highlight_keywords doesn't contain too many items
        highlight_keywords = inputs.get('highlight_keywords', [])
        if len(highlight_keywords) > 10:
            errors.append(f"Too many highlight keywords: {len(highlight_keywords)}. Maximum allowed: 10.")
        
        return errors
    
    async def _retrieve_business_case_data(self, business_case_id: str) -> Dict[str, Any]:
        """
        Retrieve business case data from MCP.
        
        Args:
            business_case_id: ID of the business case to retrieve
            
        Returns:
            Dictionary containing business case data
        """
        # In a real implementation, this would use the MCP client to retrieve the business case
        # For this example, we'll return a simplified business case
        logger.info(f"Retrieving business case data for {business_case_id}")
        
        # Simulate retrieval delay
        await asyncio.sleep(0.5)
        
        # Return sample business case data
        return {
            "metadata": {
                "project_name": "AI-Driven Customer Service Automation",
                "client_name": "TechCorp Industries",
                "industry": "technology",
                "created_at": time.time() - 3600,
                "template_id": "tech_roi_001",
                "stakeholder_persona": "executive"
            },
            "value_drivers": ["cost_reduction", "productivity_gains"],
            "roi_metrics": {
                "total_annual_benefit": 1250000.00,
                "annual_roi_percentage": 125.0,
                "three_year_roi_percentage": 375.0,
                "payback_period_months": 9.6,
                "net_present_value": 2750000.00,
                "investment_amount": 1000000.00
            },
            "metrics_data": {
                "cost_reduction": {
                    "current_operational_cost": 2000000.00,
                    "expected_cost_reduction_percentage": 35
                },
                "productivity_gains": {
                    "current_process_time": 45,  # minutes
                    "expected_time_savings_percentage": 65,
                    "affected_employee_count": 120,
                    "average_hourly_rate": 45.00
                }
            }
        }
    
    async def _generate_section_narrative(self, section_id: str, business_case_data: Dict[str, Any],
                                        stakeholder_persona: str, tone: str,
                                        max_length: int, include_metrics: bool,
                                        highlight_keywords: List[str]) -> str:
        """
        Generate narrative content for a specific business case section.
        
        Args:
            section_id: ID of the section to generate narrative for
            business_case_data: Business case data
            stakeholder_persona: Stakeholder persona to tailor narrative for
            tone: Tone of the narrative
            max_length: Maximum length of the narrative
            include_metrics: Whether to include metrics in the narrative
            highlight_keywords: Keywords to highlight in the narrative
            
        Returns:
            String containing the generated narrative
        """
        # In a real implementation, this would use an LLM to generate the narrative
        # For this example, we'll return template-based narratives
        
        persona_profile = self.persona_profiles.get(stakeholder_persona.lower(), self.persona_profiles["general"])
        
        # Get basic business case info
        project_name = business_case_data.get("metadata", {}).get("project_name", "the project")
        client_name = business_case_data.get("metadata", {}).get("client_name", "the client")
        industry = business_case_data.get("metadata", {}).get("industry", "the industry")
        
        # Get ROI metrics if needed
        roi_metrics = business_case_data.get("roi_metrics", {})
        annual_roi = roi_metrics.get("annual_roi_percentage", 0)
        payback_period = roi_metrics.get("payback_period_months", 0)
        total_benefit = roi_metrics.get("total_annual_benefit", 0)
        
        # Base templates for each section
        templates = {
            "executive_summary": f"This business case presents a compelling opportunity for {client_name} to implement {project_name}, which is expected to deliver significant value through {', '.join(business_case_data.get('value_drivers', []))}. With an annual ROI of {annual_roi:.1f}% and a payback period of {payback_period:.1f} months, this initiative aligns with our strategic objectives while addressing critical business challenges.",
            
            "problem_statement": f"{client_name} is currently facing challenges related to {', '.join(business_case_data.get('value_drivers', []))}. These challenges are impacting operational efficiency, cost structure, and competitive positioning in the {industry} market.",
            
            "proposed_solution": f"The proposed {project_name} solution will address these challenges through a comprehensive approach that leverages cutting-edge technology and industry best practices. This solution has been designed specifically for {client_name}'s unique requirements in the {industry} sector.",
            
            "value_analysis": f"The implementation of {project_name} is expected to deliver value across multiple dimensions. Based on our analysis, the primary value drivers include {', '.join(business_case_data.get('value_drivers', []))}, with a total annual benefit of ${total_benefit:,.2f}.",
            
            "roi_calculation": f"Our financial analysis indicates a compelling return on investment for {project_name}. With an initial investment of ${roi_metrics.get('investment_amount', 0):,.2f}, we project an annual ROI of {annual_roi:.1f}%, a three-year ROI of {roi_metrics.get('three_year_roi_percentage', 0):.1f}%, and a payback period of {payback_period:.1f} months.",
            
            "implementation_plan": f"The implementation of {project_name} will follow a structured approach designed to minimize disruption while ensuring rapid value realization. The plan includes key phases for planning, deployment, testing, training, and ongoing optimization.",
            
            "conclusion": f"In conclusion, the {project_name} initiative represents a strategic opportunity for {client_name} to address critical business challenges while delivering substantial financial returns. With an annual ROI of {annual_roi:.1f}% and alignment with key strategic objectives, we recommend proceeding with this investment.",
            
            "regulatory_compliance": f"The {project_name} solution has been designed with full consideration of the regulatory requirements applicable to {client_name} in the {industry} industry. Our approach ensures compliance with all relevant standards while maintaining operational efficiency.",
            
            "risk_assessment": f"We have conducted a comprehensive risk assessment for the {project_name} initiative. Key risks have been identified and mitigation strategies developed to ensure successful implementation and value realization."
        }
        
        # Get base narrative for the requested section
        base_narrative = templates.get(section_id, f"Content for the {section_id} section of {project_name}.")
        
        # Tailor the narrative based on persona
        if stakeholder_persona.lower() == "executive":
            base_narrative += f" From an executive perspective, this initiative will contribute directly to strategic objectives while delivering measurable bottom-line impact of ${total_benefit:,.2f} annually."
        
        elif stakeholder_persona.lower() == "financial_buyer":
            base_narrative += f" The financial analysis demonstrates a strong business case with an NPV of ${roi_metrics.get('net_present_value', 0):,.2f} and a payback period of {payback_period:.1f} months, providing a sound financial justification for this investment."
        
        elif stakeholder_persona.lower() == "technical_buyer":
            base_narrative += f" The technical implementation has been carefully designed to integrate with existing systems while providing a scalable platform for future growth and innovation."
        
        # Add metrics if requested
        if include_metrics and section_id in ["value_analysis", "roi_calculation", "executive_summary"]:
            metrics_narrative = f" Key metrics include: Annual ROI: {annual_roi:.1f}%, Payback Period: {payback_period:.1f} months, Total Annual Benefit: ${total_benefit:,.2f}."
            base_narrative += metrics_narrative
        
        # Highlight keywords if provided
        for keyword in highlight_keywords:
            if keyword.lower() in base_narrative.lower():
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                base_narrative = pattern.sub(f"**{keyword}**", base_narrative)
        
        # Ensure narrative doesn't exceed max length
        if len(base_narrative) > max_length:
            base_narrative = base_narrative[:max_length-3] + "..."
        
        return base_narrative
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute the narrative generation logic after validation.
        
        Args:
            inputs: Dictionary of validated input values
            
        Returns:
            AgentResult: Result of the agent execution with the generated narrative
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
        business_case_id = inputs['business_case_id']
        section_id = inputs['section_id']
        stakeholder_persona = inputs['stakeholder_persona']
        tone = inputs.get('tone', self.persona_profiles.get(stakeholder_persona.lower(), {}).get('default_tone', 'formal'))
        max_length = inputs.get('max_length', 2000)
        include_metrics = inputs.get('include_metrics', True)
        highlight_keywords = inputs.get('highlight_keywords', [])
        
        try:
            # Retrieve business case data
            business_case_data = await self._retrieve_business_case_data(business_case_id)
            
            # Generate narrative for the requested section
            narrative = await self._generate_section_narrative(
                section_id, 
                business_case_data,
                stakeholder_persona,
                tone,
                max_length,
                include_metrics,
                highlight_keywords
            )
            
            # Prepare result data
            result_data = {
                "narrative": narrative,
                "section_id": section_id,
                "stakeholder_persona": stakeholder_persona,
                "tone": tone,
                "character_count": len(narrative),
                "word_count": len(narrative.split())
            }
            
            # Log success
            logger.info(f"Successfully generated narrative for {section_id} section (stakeholder: {stakeholder_persona})")
            
            # Return successful result
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data,
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
            
        except Exception as e:
            logger.error(f"Error generating narrative: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Failed to generate narrative: {str(e)}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
