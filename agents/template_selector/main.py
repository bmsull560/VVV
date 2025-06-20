"""
Template Selector Agent

This agent analyzes user inputs and business context to select the most appropriate
business case template from available options. It considers industry, use case,
complexity, and stakeholder requirements to make optimal template recommendations.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from enum import Enum

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class BusinessCaseTemplate(Enum):
    """Available business case templates with their characteristics."""
    STANDARD_ROI = "standard_roi"
    COST_REDUCTION = "cost_reduction"
    REVENUE_GROWTH = "revenue_growth"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    COMPLIANCE_SECURITY = "compliance_security"
    INNOVATION_STRATEGIC = "innovation_strategic"
    INFRASTRUCTURE_UPGRADE = "infrastructure_upgrade"

class IndustryType(Enum):
    """Industry classifications for template selection."""
    HEALTHCARE = "healthcare"
    FINANCIAL_SERVICES = "financial_services"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    EDUCATION = "education"
    GOVERNMENT = "government"
    TELECOMMUNICATIONS = "telecommunications"
    ENERGY = "energy"
    GENERIC = "generic"

class TemplateSelectorAgent(BaseAgent):
    """
    Selects the most appropriate business case template based on user inputs,
    industry context, and business objectives.
    """

    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        # Set up validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['business_objective', 'industry'],
                'field_types': {
                    'business_objective': 'string',
                    'industry': 'string',
                    'stakeholder_types': 'array',
                    'complexity_level': 'string',
                    'budget_range': 'string',
                    'timeline': 'string',
                    'primary_value_drivers': 'array'
                },
                'field_constraints': {
                    'complexity_level': {'allowed_values': ['low', 'medium', 'high']},
                    'budget_range': {'allowed_values': ['small', 'medium', 'large', 'enterprise']},
                    'timeline': {'allowed_values': ['immediate', 'short_term', 'medium_term', 'long_term']}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Template scoring weights for different criteria
        self.scoring_weights = {
            'industry_match': 0.25,
            'objective_alignment': 0.30,
            'stakeholder_fit': 0.20,
            'complexity_match': 0.15,
            'value_driver_alignment': 0.10
        }
        
        # Template characteristics database
        self.template_database = self._initialize_template_database()

    def _initialize_template_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the template database with characteristics and scoring criteria."""
        return {
            BusinessCaseTemplate.STANDARD_ROI.value: {
                'name': 'Standard ROI Business Case',
                'description': 'Comprehensive ROI analysis with financial projections',
                'industries': [IndustryType.GENERIC.value, IndustryType.TECHNOLOGY.value, IndustryType.MANUFACTURING.value],
                'objectives': ['cost_reduction', 'productivity_improvement', 'efficiency_gains'],
                'stakeholders': ['financial_buyer', 'executive', 'operations'],
                'complexity': ['medium', 'high'],
                'value_drivers': ['cost_savings', 'productivity', 'automation', 'efficiency'],
                'timeline': ['medium_term', 'long_term'],
                'budget_range': ['medium', 'large', 'enterprise'],
                'sections': ['executive_summary', 'problem_statement', 'solution_overview', 'financial_analysis', 'implementation_plan', 'risk_assessment']
            },
            BusinessCaseTemplate.COST_REDUCTION.value: {
                'name': 'Cost Reduction Focused Business Case',
                'description': 'Targeted cost reduction and operational savings analysis',
                'industries': [IndustryType.MANUFACTURING.value, IndustryType.RETAIL.value, IndustryType.FINANCIAL_SERVICES.value],
                'objectives': ['cost_reduction', 'operational_efficiency', 'waste_elimination'],
                'stakeholders': ['financial_buyer', 'operations', 'procurement'],
                'complexity': ['low', 'medium'],
                'value_drivers': ['cost_savings', 'waste_reduction', 'process_optimization'],
                'timeline': ['immediate', 'short_term'],
                'budget_range': ['small', 'medium'],
                'sections': ['executive_summary', 'current_costs', 'cost_reduction_opportunities', 'savings_analysis', 'implementation_roadmap']
            },
            BusinessCaseTemplate.REVENUE_GROWTH.value: {
                'name': 'Revenue Growth Business Case',
                'description': 'Revenue enhancement and market expansion focus',
                'industries': [IndustryType.RETAIL.value, IndustryType.TECHNOLOGY.value, IndustryType.TELECOMMUNICATIONS.value],
                'objectives': ['revenue_growth', 'market_expansion', 'customer_acquisition'],
                'stakeholders': ['executive', 'sales', 'marketing'],
                'complexity': ['medium', 'high'],
                'value_drivers': ['revenue_increase', 'customer_growth', 'market_share'],
                'timeline': ['short_term', 'medium_term'],
                'budget_range': ['medium', 'large'],
                'sections': ['executive_summary', 'market_opportunity', 'revenue_projections', 'customer_analysis', 'competitive_advantage']
            },
            BusinessCaseTemplate.DIGITAL_TRANSFORMATION.value: {
                'name': 'Digital Transformation Business Case',
                'description': 'Comprehensive digital modernization and technology adoption',
                'industries': [IndustryType.FINANCIAL_SERVICES.value, IndustryType.HEALTHCARE.value, IndustryType.GOVERNMENT.value],
                'objectives': ['digital_transformation', 'modernization', 'technology_adoption'],
                'stakeholders': ['executive', 'technical_buyer', 'operations'],
                'complexity': ['high'],
                'value_drivers': ['automation', 'efficiency', 'innovation', 'customer_experience'],
                'timeline': ['medium_term', 'long_term'],
                'budget_range': ['large', 'enterprise'],
                'sections': ['executive_summary', 'current_state_assessment', 'transformation_roadmap', 'technology_benefits', 'change_management', 'roi_analysis']
            },
            BusinessCaseTemplate.OPERATIONAL_EFFICIENCY.value: {
                'name': 'Operational Efficiency Business Case',
                'description': 'Process optimization and operational improvement focus',
                'industries': [IndustryType.MANUFACTURING.value, IndustryType.HEALTHCARE.value, IndustryType.EDUCATION.value],
                'objectives': ['operational_efficiency', 'process_improvement', 'quality_enhancement'],
                'stakeholders': ['operations', 'quality', 'process_owners'],
                'complexity': ['low', 'medium'],
                'value_drivers': ['efficiency', 'quality', 'throughput', 'error_reduction'],
                'timeline': ['immediate', 'short_term', 'medium_term'],
                'budget_range': ['small', 'medium'],
                'sections': ['executive_summary', 'process_analysis', 'efficiency_opportunities', 'quality_improvements', 'implementation_plan']
            },
            BusinessCaseTemplate.COMPLIANCE_SECURITY.value: {
                'name': 'Compliance & Security Business Case',
                'description': 'Risk mitigation, compliance, and security enhancement',
                'industries': [IndustryType.FINANCIAL_SERVICES.value, IndustryType.HEALTHCARE.value, IndustryType.GOVERNMENT.value],
                'objectives': ['compliance', 'security_enhancement', 'risk_mitigation'],
                'stakeholders': ['compliance', 'security', 'risk_management', 'executive'],
                'complexity': ['medium', 'high'],
                'value_drivers': ['risk_reduction', 'compliance_value', 'security_improvement'],
                'timeline': ['immediate', 'short_term'],
                'budget_range': ['medium', 'large'],
                'sections': ['executive_summary', 'compliance_requirements', 'risk_assessment', 'security_benefits', 'regulatory_alignment']
            },
            BusinessCaseTemplate.INNOVATION_STRATEGIC.value: {
                'name': 'Innovation & Strategic Initiative Business Case',
                'description': 'Strategic innovation projects and competitive advantage',
                'industries': [IndustryType.TECHNOLOGY.value, IndustryType.TELECOMMUNICATIONS.value, IndustryType.ENERGY.value],
                'objectives': ['innovation', 'strategic_advantage', 'market_leadership'],
                'stakeholders': ['executive', 'innovation', 'strategy'],
                'complexity': ['high'],
                'value_drivers': ['innovation_value', 'competitive_advantage', 'strategic_positioning'],
                'timeline': ['long_term'],
                'budget_range': ['large', 'enterprise'],
                'sections': ['executive_summary', 'strategic_context', 'innovation_opportunity', 'competitive_analysis', 'strategic_value']
            },
            BusinessCaseTemplate.INFRASTRUCTURE_UPGRADE.value: {
                'name': 'Infrastructure Upgrade Business Case',
                'description': 'Infrastructure modernization and capacity enhancement',
                'industries': [IndustryType.TELECOMMUNICATIONS.value, IndustryType.ENERGY.value, IndustryType.GOVERNMENT.value],
                'objectives': ['infrastructure_upgrade', 'capacity_enhancement', 'reliability_improvement'],
                'stakeholders': ['technical_buyer', 'operations', 'infrastructure'],
                'complexity': ['medium', 'high'],
                'value_drivers': ['reliability', 'capacity', 'performance', 'maintenance_reduction'],
                'timeline': ['medium_term', 'long_term'],
                'budget_range': ['large', 'enterprise'],
                'sections': ['executive_summary', 'infrastructure_assessment', 'upgrade_requirements', 'capacity_analysis', 'reliability_benefits']
            }
        }

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Perform template selector-specific validations."""
        errors = []
        
        # Validate industry
        industry = inputs.get('industry', '').lower()
        valid_industries = [industry.value for industry in IndustryType]
        if industry and industry not in valid_industries:
            errors.append(f"Invalid industry '{industry}'. Must be one of: {', '.join(valid_industries)}")
        
        # Validate business objective
        business_objective = inputs.get('business_objective', '').lower()
        valid_objectives = ['cost_reduction', 'revenue_growth', 'operational_efficiency', 'digital_transformation', 
                          'compliance', 'security_enhancement', 'innovation', 'infrastructure_upgrade', 
                          'productivity_improvement', 'market_expansion', 'customer_acquisition']
        if business_objective and business_objective not in valid_objectives:
            errors.append(f"Invalid business objective '{business_objective}'. Must be one of: {', '.join(valid_objectives)}")
        
        # Validate stakeholder types if provided
        stakeholder_types = inputs.get('stakeholder_types', [])
        if stakeholder_types:
            valid_stakeholders = ['executive', 'financial_buyer', 'technical_buyer', 'operations', 'compliance', 
                                'security', 'sales', 'marketing', 'procurement', 'quality', 'innovation']
            for stakeholder in stakeholder_types:
                if stakeholder not in valid_stakeholders:
                    errors.append(f"Invalid stakeholder type '{stakeholder}'. Must be one of: {', '.join(valid_stakeholders)}")
        
        return errors

    def _calculate_template_score(self, template_key: str, inputs: Dict[str, Any]) -> float:
        """Calculate a scoring for how well a template matches the given inputs."""
        template = self.template_database[template_key]
        total_score = 0.0
        
        # Industry match scoring
        industry = inputs.get('industry', '').lower()
        if industry in template['industries'] or IndustryType.GENERIC.value in template['industries']:
            industry_score = 1.0
        else:
            industry_score = 0.5 if industry != '' else 0.0
        total_score += industry_score * self.scoring_weights['industry_match']
        
        # Objective alignment scoring
        business_objective = inputs.get('business_objective', '').lower()
        if business_objective in template['objectives']:
            objective_score = 1.0
        else:
            objective_score = 0.3 if business_objective != '' else 0.0
        total_score += objective_score * self.scoring_weights['objective_alignment']
        
        # Stakeholder fit scoring
        stakeholder_types = inputs.get('stakeholder_types', [])
        if stakeholder_types:
            matching_stakeholders = len(set(stakeholder_types) & set(template['stakeholders']))
            stakeholder_score = matching_stakeholders / len(template['stakeholders'])
        else:
            stakeholder_score = 0.5  # Neutral score if no stakeholders specified
        total_score += stakeholder_score * self.scoring_weights['stakeholder_fit']
        
        # Complexity and timeline considerations
        complexity = inputs.get('complexity_level', '')
        timeline = inputs.get('timeline', '')
        if complexity and timeline:
            complexity_score = 1.0 if complexity in template['complexity'] else 0.5
            timeline_score = 1.0 if timeline in template['timeline'] else 0.5
            total_score += complexity_score * self.scoring_weights['complexity_match']
            total_score += timeline_score * self.scoring_weights['complexity_match']
        
        # Value driver alignment scoring
        primary_value_drivers = inputs.get('primary_value_drivers', [])
        if primary_value_drivers:
            matching_drivers = len(set(primary_value_drivers) & set(template['value_drivers']))
            driver_score = matching_drivers / len(template['value_drivers'])
        else:
            driver_score = 0.5  # Neutral score if no drivers specified
        total_score += driver_score * self.scoring_weights['value_driver_alignment']
        
        return total_score

    def _get_template_recommendations(self, inputs: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
        """Get ranked template recommendations based on input analysis."""
        template_scores = []
        
        for template_key in self.template_database:
            score = self._calculate_template_score(template_key, inputs)
            template = self.template_database[template_key]
            
            template_scores.append({
                'template_id': template_key,
                'template_name': template['name'],
                'description': template['description'],
                'score': round(score, 3),
                'sections': template['sections'],
                'recommended_for': {
                    'industries': template['industries'],
                    'stakeholders': template['stakeholders'],
                    'complexity': template['complexity']
                }
            })
        
        # Sort by score (descending) and return top N
        template_scores.sort(key=lambda x: x['score'], reverse=True)
        return template_scores[:top_n]

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Analyze inputs and select the most appropriate business case template.
        
        Args:
            inputs: Dictionary containing:
                - business_objective: Primary business objective
                - industry: Industry classification
                - stakeholder_types: List of stakeholder types involved
                - complexity_level: Project complexity (low/medium/high)
                - budget_range: Budget classification (small/medium/large/enterprise)
                - timeline: Project timeline (immediate/short_term/medium_term/long_term)
                - primary_value_drivers: List of primary value drivers
        
        Returns:
            AgentResult with selected template and alternatives
        """
        start_time = time.monotonic()
        
        # Use centralized validation
        validation_result = await self.validate_inputs(inputs)
        if not validation_result.is_valid:
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": validation_result.errors[0] if validation_result.errors else "Input validation failed"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
        
        try:
            # Get template recommendations
            recommendations = self._get_template_recommendations(inputs)
            
            if not recommendations:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": "No suitable templates found for the given criteria"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Select the top-scoring template
            selected_template = recommendations[0]
            alternative_templates = recommendations[1:] if len(recommendations) > 1 else []
            
            result_data = {
                'selected_template': {
                    'template_id': selected_template['template_id'],
                    'template_name': selected_template['template_name'],
                    'description': selected_template['description'],
                    'confidence_score': selected_template['score'],
                    'sections': selected_template['sections'],
                    'recommended_for': selected_template['recommended_for']
                },
                'alternative_templates': alternative_templates,
                'selection_criteria': {
                    'business_objective': inputs.get('business_objective'),
                    'industry': inputs.get('industry'),
                    'stakeholder_types': inputs.get('stakeholder_types', []),
                    'complexity_level': inputs.get('complexity_level'),
                    'budget_range': inputs.get('budget_range'),
                    'timeline': inputs.get('timeline')
                },
                'template_rationale': self._generate_selection_rationale(selected_template, inputs)
            }
            
            # Store selection in MCP for workflow coordination
            await self.mcp_client.store_memory(
                "working",
                "template_selection",
                {
                    "selected_template_id": selected_template['template_id'],
                    "selection_criteria": result_data['selection_criteria'],
                    "confidence_score": selected_template['score']
                },
                ["template_selection", "workflow_step"]
            )
            
            logger.info(f"Template selection complete. Selected: {selected_template['template_name']} (score: {selected_template['score']})")
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Template selection failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Template selection failed: {str(e)}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )

    def _generate_selection_rationale(self, selected_template: Dict[str, Any], inputs: Dict[str, Any]) -> str:
        """Generate human-readable rationale for template selection."""
        rationale_parts = []
        
        # Industry alignment
        industry = inputs.get('industry', '').lower()
        if industry:
            rationale_parts.append(f"Selected for {industry} industry alignment")
        
        # Objective match
        business_objective = inputs.get('business_objective', '').lower()
        if business_objective:
            rationale_parts.append(f"Optimized for {business_objective} objectives")
        
        # Stakeholder focus
        stakeholder_types = inputs.get('stakeholder_types', [])
        if stakeholder_types:
            rationale_parts.append(f"Designed for {', '.join(stakeholder_types)} stakeholders")
        
        # Complexity and timeline considerations
        complexity = inputs.get('complexity_level', '')
        timeline = inputs.get('timeline', '')
        if complexity and timeline:
            rationale_parts.append(f"Suitable for {complexity} complexity projects with {timeline} timeline")
        
        rationale = ". ".join(rationale_parts) if rationale_parts else "Selected based on general best practices"
        return f"{rationale}. Confidence score: {selected_template['score']:.1%}"
