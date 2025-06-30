"""
Intake Assistant Agent

This agent gathers initial user input via a conversational interface and extracts
key business context like company profile, pain points, and strategic goals.
"""

import logging
import time
import re
import uuid
import json
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import functools

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.memory_types import KnowledgeEntity, DataSensitivity

logger = logging.getLogger(__name__)

class ProjectType(Enum):
    """Types of projects for business intelligence categorization."""
    DIGITAL_TRANSFORMATION = "digital_transformation"
    COST_OPTIMIZATION = "cost_optimization"
    REVENUE_GROWTH = "revenue_growth"
    CUSTOMER_EXPERIENCE = "customer_experience"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    RISK_MITIGATION = "risk_mitigation"
    COMPLIANCE = "compliance"
    INNOVATION = "innovation"
    OTHER = "other"

class ProjectComplexity(Enum):
    """Complexity levels for projects."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class IntakeAssistantAgent(BaseAgent):
    """
    Production-ready agent for comprehensive project intake and business intelligence.
    
    This agent gathers initial user input, extracts key business context, and performs
    advanced analysis to provide intelligent recommendations and insights.
    """

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Enhanced validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': [
                    'project_name', 'description', 'business_objective'
                ],
                'field_types': {
                    'project_name': 'string',
                    'description': 'string',
                    'business_objective': 'string',
                    'industry': 'string',
                    'department': 'string',
                    'goals': 'array',
                    'success_criteria': 'array',
                    'stakeholders': 'array',
                    'budget_range': 'string',
                    'timeline': 'string',
                    'urgency': 'string',
                    'expected_participants': 'number',
                    'geographic_scope': 'string',
                    'regulatory_requirements': 'array'
                },
                'field_constraints': {
                    'project_name': {'min_length': 3, 'max_length': 100},
                    'description': {'min_length': 20},
                    'urgency': {'enum': ['low', 'medium', 'high', 'critical']},
                    'budget_range': {'enum': ['under_50k', '50k_to_250k', '250k_to_1m', 'over_1m']},
                    'timeline': {'enum': ['immediate', 'quarterly', 'annual', 'multi_year']}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Initialize business intelligence components
        self.industry_benchmarks = {
            'technology': {'avg_roi': 35, 'avg_timeline_months': 9, 'complexity_factor': 1.2},
            'healthcare': {'avg_roi': 28, 'avg_timeline_months': 12, 'complexity_factor': 1.5},
            'financial_services': {'avg_roi': 32, 'avg_timeline_months': 10, 'complexity_factor': 1.3},
            'manufacturing': {'avg_roi': 25, 'avg_timeline_months': 14, 'complexity_factor': 1.1},
            'retail': {'avg_roi': 30, 'avg_timeline_months': 8, 'complexity_factor': 1.0},
            'education': {'avg_roi': 22, 'avg_timeline_months': 15, 'complexity_factor': 1.2},
            'government': {'avg_roi': 18, 'avg_timeline_months': 18, 'complexity_factor': 1.4},
            'other': {'avg_roi': 25, 'avg_timeline_months': 12, 'complexity_factor': 1.2}
        }
        
        self.project_type_keywords = {
            ProjectType.DIGITAL_TRANSFORMATION: [
                'digital', 'transformation', 'modernize', 'modernization', 'platform', 'cloud', 'migration'
            ],
            ProjectType.COST_OPTIMIZATION: [
                'cost', 'saving', 'reduction', 'optimize', 'efficiency', 'budget', 'expense'
            ],
            ProjectType.REVENUE_GROWTH: [
                'revenue', 'growth', 'sales', 'market', 'expansion', 'customer acquisition', 'upsell'
            ],
            ProjectType.CUSTOMER_EXPERIENCE: [
                'customer', 'experience', 'satisfaction', 'journey', 'engagement', 'retention', 'loyalty'
            ],
            ProjectType.OPERATIONAL_EFFICIENCY: [
                'operational', 'efficiency', 'streamline', 'process', 'workflow', 'automation', 'productivity'
            ],
            ProjectType.RISK_MITIGATION: [
                'risk', 'mitigation', 'compliance', 'security', 'protection', 'resilience', 'continuity'
            ],
            ProjectType.COMPLIANCE: [
                'compliance', 'regulatory', 'regulation', 'legal', 'governance', 'audit', 'standard'
            ],
            ProjectType.INNOVATION: [
                'innovation', 'research', 'development', 'new product', 'disruptive', 'emerging', 'prototype'
            ]
        }

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for intake assistant inputs."""
        errors = []
        
        # Project name validation
        project_name = inputs.get('project_name', '')
        if len(project_name) < 5:
            errors.append("Project name must be at least 5 characters long.")
        
        # Check for existing projects with similar names
        existing_projects = await self._check_existing_projects(project_name)
        if existing_projects:
            errors.append(f"Similar project name already exists: {existing_projects[0]}")
        
        # Description validation
        description = inputs.get('description', '')
        if len(description) < 20:
            errors.append("Description must be at least 20 characters long.")
        
        # Goals validation
        goals = inputs.get('goals', [])
        if goals and not goals:
            errors.append("Goals cannot be an empty list if provided.")
        
        # Stakeholders validation
        stakeholders = inputs.get('stakeholders', [])
        if stakeholders:
            for i, stakeholder in enumerate(stakeholders):
                if not isinstance(stakeholder, dict):
                    errors.append(f"Stakeholder {i} must be an object.")
                    continue
                
                if 'name' not in stakeholder or not stakeholder['name']:
                    errors.append(f"Stakeholder {i} must have a name.")
                
                if 'role' not in stakeholder or not stakeholder['role']:
                    errors.append(f"Stakeholder {i} must have a role.")
                
                if 'influence_level' in stakeholder and stakeholder['influence_level'] not in ['low', 'medium', 'high']:
                    errors.append(f"Stakeholder {i} influence level must be 'low', 'medium', or 'high'.")
        
        return errors

    @functools.lru_cache(maxsize=32)
    async def _check_existing_projects(self, project_name: str) -> List[str]:
        """Check for existing projects with similar names."""
        logger.debug(f"search_results for '{project_name}': []")
        
        try:
            # Search for similar project names
            search_results = await self.mcp_client.search_nodes(project_name)
            
            # Extract project names from search results
            existing_names = []
            for result in search_results:
                if isinstance(result, dict) and 'name' in result:
                    existing_names.append(result['name'])
                elif hasattr(result, 'name'):
                    existing_names.append(result.name)
            
            logger.debug(f"existing_project_names: {existing_names}")
            return existing_names
        except Exception as e:
            logger.error(f"Error checking existing projects: {e}")
            return []

    def _classify_project_type(self, inputs: Dict[str, Any]) -> ProjectType:
        """Classify the project type based on input text."""
        # Combine relevant text fields for analysis
        text = ' '.join([
            inputs.get('project_name', ''),
            inputs.get('description', ''),
            inputs.get('business_objective', ''),
            ' '.join(inputs.get('goals', [])),
            ' '.join(inputs.get('success_criteria', []))
        ]).lower()
        
        # Count keyword matches for each project type
        type_scores = {}
        for project_type, keywords in self.project_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            type_scores[project_type] = score
        
        # Return the project type with the highest score, or OTHER if no clear match
        if not type_scores:
            return ProjectType.OTHER
            
        max_score = max(type_scores.values())
        if max_score == 0:
            return ProjectType.OTHER
            
        # Get all types with the max score
        max_types = [pt for pt, score in type_scores.items() if score == max_score]
        return max_types[0]  # Return the first one if there are ties

    def _assess_project_complexity(self, inputs: Dict[str, Any]) -> Tuple[ProjectComplexity, float]:
        """Assess project complexity and return a complexity score."""
        # Base complexity factors
        factors = {
            'stakeholder_count': len(inputs.get('stakeholders', [])) * 0.2,
            'goal_count': len(inputs.get('goals', [])) * 0.15,
            'timeline': {
                'immediate': 0.5,
                'quarterly': 1.0,
                'annual': 1.5,
                'multi_year': 2.0
            }.get(inputs.get('timeline', 'quarterly'), 1.0),
            'budget': {
                'under_50k': 0.7,
                '50k_to_250k': 1.0,
                '250k_to_1m': 1.5,
                'over_1m': 2.0
            }.get(inputs.get('budget_range', '50k_to_250k'), 1.0),
            'urgency': {
                'low': 0.7,
                'medium': 1.0,
                'high': 1.3,
                'critical': 1.6
            }.get(inputs.get('urgency', 'medium'), 1.0),
            'participants': min(inputs.get('expected_participants', 5) / 10, 2.0),
            'geographic_scope': {
                'local': 0.8,
                'regional': 1.0,
                'national': 1.3,
                'global': 1.8
            }.get(inputs.get('geographic_scope', 'national'), 1.0),
            'regulatory_requirements': len(inputs.get('regulatory_requirements', [])) * 0.3
        }
        
        # Industry-specific complexity factor
        industry = inputs.get('industry', 'other').lower()
        industry_factor = self.industry_benchmarks.get(
            industry, 
            self.industry_benchmarks['other']
        )['complexity_factor']
        
        # Calculate weighted complexity score
        complexity_score = sum(factors.values()) * industry_factor
        
        # Map score to complexity level
        if complexity_score < 5:
            return ProjectComplexity.LOW, complexity_score
        elif complexity_score < 8:
            return ProjectComplexity.MEDIUM, complexity_score
        elif complexity_score < 12:
            return ProjectComplexity.HIGH, complexity_score
        else:
            return ProjectComplexity.VERY_HIGH, complexity_score

    def _analyze_industry_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze industry-specific context and benchmarks."""
        industry = inputs.get('industry', 'other').lower()
        benchmarks = self.industry_benchmarks.get(
            industry, 
            self.industry_benchmarks['other']
        )
        
        # Adjust benchmarks based on project type
        project_type = self._classify_project_type(inputs)
        type_adjustments = {
            ProjectType.DIGITAL_TRANSFORMATION: {'roi': 1.2, 'timeline': 1.3},
            ProjectType.COST_OPTIMIZATION: {'roi': 1.1, 'timeline': 0.9},
            ProjectType.REVENUE_GROWTH: {'roi': 1.3, 'timeline': 1.0},
            ProjectType.CUSTOMER_EXPERIENCE: {'roi': 1.1, 'timeline': 1.1},
            ProjectType.OPERATIONAL_EFFICIENCY: {'roi': 1.0, 'timeline': 0.9},
            ProjectType.RISK_MITIGATION: {'roi': 0.8, 'timeline': 1.2},
            ProjectType.COMPLIANCE: {'roi': 0.7, 'timeline': 1.3},
            ProjectType.INNOVATION: {'roi': 1.4, 'timeline': 1.4},
            ProjectType.OTHER: {'roi': 1.0, 'timeline': 1.0}
        }
        
        adjustment = type_adjustments.get(project_type, {'roi': 1.0, 'timeline': 1.0})
        
        return {
            'industry': industry,
            'project_type': project_type.value,
            'avg_roi_percentage': benchmarks['avg_roi'] * adjustment['roi'],
            'avg_timeline_months': benchmarks['avg_timeline_months'] * adjustment['timeline'],
            'complexity_factor': benchmarks['complexity_factor'],
            'industry_specific_factors': self._get_industry_specific_factors(industry)
        }

    def _get_industry_specific_factors(self, industry: str) -> Dict[str, Any]:
        """Get industry-specific factors for business intelligence."""
        industry_factors = {
            'technology': {
                'innovation_focus': True,
                'technical_debt_consideration': True,
                'rapid_change_environment': True,
                'talent_competition': True,
                'regulatory_complexity': 'low'
            },
            'healthcare': {
                'innovation_focus': False,
                'technical_debt_consideration': False,
                'rapid_change_environment': False,
                'talent_competition': True,
                'regulatory_complexity': 'high'
            },
            'financial_services': {
                'innovation_focus': True,
                'technical_debt_consideration': True,
                'rapid_change_environment': False,
                'talent_competition': True,
                'regulatory_complexity': 'high'
            },
            'manufacturing': {
                'innovation_focus': False,
                'technical_debt_consideration': True,
                'rapid_change_environment': False,
                'talent_competition': False,
                'regulatory_complexity': 'medium'
            },
            'retail': {
                'innovation_focus': True,
                'technical_debt_consideration': False,
                'rapid_change_environment': True,
                'talent_competition': False,
                'regulatory_complexity': 'low'
            },
            'education': {
                'innovation_focus': False,
                'technical_debt_consideration': False,
                'rapid_change_environment': False,
                'talent_competition': False,
                'regulatory_complexity': 'medium'
            },
            'government': {
                'innovation_focus': False,
                'technical_debt_consideration': True,
                'rapid_change_environment': False,
                'talent_competition': False,
                'regulatory_complexity': 'high'
            }
        }
        
        return industry_factors.get(industry, {
            'innovation_focus': False,
            'technical_debt_consideration': False,
            'rapid_change_environment': False,
            'talent_competition': False,
            'regulatory_complexity': 'medium'
        })

    def _assess_intake_quality(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality and completeness of the intake information."""
        # Define required and optional fields with weights
        field_weights = {
            # Required fields
            'project_name': {'required': True, 'weight': 1.0},
            'description': {'required': True, 'weight': 1.0},
            'business_objective': {'required': True, 'weight': 1.0},
            # Important fields
            'industry': {'required': False, 'weight': 0.8},
            'department': {'required': False, 'weight': 0.7},
            'goals': {'required': False, 'weight': 0.9},
            'success_criteria': {'required': False, 'weight': 0.9},
            'stakeholders': {'required': False, 'weight': 0.8},
            # Helpful fields
            'budget_range': {'required': False, 'weight': 0.6},
            'timeline': {'required': False, 'weight': 0.6},
            'urgency': {'required': False, 'weight': 0.5},
            'expected_participants': {'required': False, 'weight': 0.4},
            'geographic_scope': {'required': False, 'weight': 0.3},
            'regulatory_requirements': {'required': False, 'weight': 0.5}
        }
        
        # Calculate completeness score
        total_weight = sum(field['weight'] for field in field_weights.values())
        weighted_score = 0
        
        for field, config in field_weights.items():
            if field in inputs and inputs[field]:
                # Check array fields for meaningful content
                if isinstance(inputs[field], list):
                    if len(inputs[field]) > 0:
                        weighted_score += config['weight']
                # Check string fields for meaningful content
                elif isinstance(inputs[field], str):
                    if len(inputs[field]) > 3:
                        weighted_score += config['weight']
                # Other field types
                else:
                    weighted_score += config['weight']
        
        completeness_score = weighted_score / total_weight
        
        # Assess quality of key fields
        quality_scores = {}
        
        # Description quality
        description = inputs.get('description', '')
        if description:
            word_count = len(description.split())
            quality_scores['description'] = min(1.0, word_count / 50)
        else:
            quality_scores['description'] = 0.0
        
        # Goals quality
        goals = inputs.get('goals', [])
        if goals:
            avg_goal_length = sum(len(str(goal).split()) for goal in goals) / len(goals)
            quality_scores['goals'] = min(1.0, avg_goal_length / 5)
        else:
            quality_scores['goals'] = 0.0
        
        # Stakeholders quality
        stakeholders = inputs.get('stakeholders', [])
        if stakeholders:
            stakeholder_completeness = sum(
                1 for s in stakeholders 
                if isinstance(s, dict) and 'name' in s and 'role' in s
            ) / len(stakeholders)
            quality_scores['stakeholders'] = stakeholder_completeness
        else:
            quality_scores['stakeholders'] = 0.0
        
        # Calculate overall quality score
        quality_weight = 0.7  # Weight for quality vs. completeness
        overall_score = (completeness_score * (1 - quality_weight) + 
                        (sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0) * quality_weight)
        
        return {
            'completeness_score': completeness_score,
            'quality_scores': quality_scores,
            'overall_score': overall_score,
            'assessment': self._get_quality_assessment(overall_score)
        }

    def _get_quality_assessment(self, score: float) -> str:
        """Get a qualitative assessment based on the quality score."""
        if score >= 0.9:
            return "Excellent - Very comprehensive project intake with detailed information."
        elif score >= 0.75:
            return "Good - Solid project intake with most key information provided."
        elif score >= 0.6:
            return "Adequate - Basic project information provided, but could benefit from more details."
        elif score >= 0.4:
            return "Minimal - Limited project information, additional details recommended."
        else:
            return "Insufficient - Critical information missing, requires significant additional input."

    def _generate_recommendations(self, inputs: Dict[str, Any], 
                                business_intelligence: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent recommendations based on project analysis."""
        recommendations = []
        
        # Project type-specific recommendations
        project_type = business_intelligence.get('project_type', 'other')
        complexity = business_intelligence.get('complexity', {}).get('level', 'medium')
        
        # Recommendation: Value Driver Focus
        if project_type == 'cost_optimization':
            recommendations.append({
                'type': 'value_driver_focus',
                'title': 'Focus on Cost Reduction Value Drivers',
                'description': 'Prioritize quantifying operational cost savings, resource optimization, and efficiency gains.',
                'priority': 'high'
            })
        elif project_type == 'revenue_growth':
            recommendations.append({
                'type': 'value_driver_focus',
                'title': 'Focus on Revenue Enhancement Value Drivers',
                'description': 'Prioritize quantifying revenue uplift, market expansion, and customer acquisition benefits.',
                'priority': 'high'
            })
        elif project_type == 'operational_efficiency':
            recommendations.append({
                'type': 'value_driver_focus',
                'title': 'Focus on Productivity Value Drivers',
                'description': 'Prioritize quantifying time savings, process improvements, and resource utilization.',
                'priority': 'high'
            })
        
        # Recommendation: Stakeholder Engagement
        stakeholders = inputs.get('stakeholders', [])
        if not any(s.get('role') == 'sponsor' for s in stakeholders if isinstance(s, dict)):
            recommendations.append({
                'type': 'stakeholder_engagement',
                'title': 'Identify Executive Sponsor',
                'description': 'Add a project sponsor with executive authority to ensure project success.',
                'priority': 'high'
            })
        
        # Recommendation: Risk Assessment
        if complexity in ['high', 'very_high']:
            recommendations.append({
                'type': 'risk_assessment',
                'title': 'Conduct Detailed Risk Assessment',
                'description': 'This project has high complexity. A comprehensive risk assessment is recommended.',
                'priority': 'high'
            })
        
        # Recommendation: Success Metrics
        if not inputs.get('success_criteria'):
            recommendations.append({
                'type': 'success_metrics',
                'title': 'Define Clear Success Metrics',
                'description': 'Add specific, measurable success criteria to enable proper ROI tracking.',
                'priority': 'medium'
            })
        
        # Recommendation: Budget Confidence
        budget_confidence = business_intelligence.get('budget_confidence', {}).get('level', 'medium')
        if budget_confidence == 'low':
            recommendations.append({
                'type': 'budget_refinement',
                'title': 'Refine Budget Estimates',
                'description': 'Current budget estimates have low confidence. Consider a more detailed cost analysis.',
                'priority': 'medium'
            })
        
        # Add general recommendations if list is empty
        if not recommendations:
            recommendations.append({
                'type': 'general',
                'title': 'Proceed with Standard Analysis',
                'description': 'Project intake is complete. Proceed with standard value driver analysis.',
                'priority': 'medium'
            })
        
        return recommendations

    def _assess_budget_confidence(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Assess confidence level in budget estimates."""
        budget_range = inputs.get('budget_range', '')
        has_detailed_goals = bool(inputs.get('goals', []))
        has_timeline = bool(inputs.get('timeline', ''))
        has_stakeholders = len(inputs.get('stakeholders', [])) > 0
        
        # Calculate confidence score
        confidence_factors = [
            0.6 if budget_range else 0.0,  # Having any budget range gives base confidence
            0.2 if has_detailed_goals else 0.0,
            0.1 if has_timeline else 0.0,
            0.1 if has_stakeholders else 0.0
        ]
        
        confidence_score = sum(confidence_factors)
        
        # Determine confidence level
        if confidence_score >= 0.8:
            confidence_level = 'high'
        elif confidence_score >= 0.5:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'
        
        return {
            'score': confidence_score,
            'level': confidence_level,
            'factors': {
                'has_budget_range': bool(budget_range),
                'has_detailed_goals': has_detailed_goals,
                'has_timeline': has_timeline,
                'has_stakeholders': has_stakeholders
            }
        }

    def _structure_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Structure and normalize input data."""
        structured_data = {}
        
        # Copy simple string fields directly
        string_fields = ['project_name', 'description', 'business_objective', 
                        'industry', 'department', 'budget_range', 'timeline', 
                        'urgency', 'geographic_scope']
        
        for field in string_fields:
            if field in inputs:
                structured_data[field] = inputs[field]
        
        # Handle numeric fields
        numeric_fields = ['expected_participants']
        for field in numeric_fields:
            if field in inputs:
                try:
                    structured_data[field] = int(inputs[field])
                except (ValueError, TypeError):
                    structured_data[field] = 0
        
        # Handle array fields, ensuring they are lists of strings
        array_fields = ['goals', 'success_criteria', 'regulatory_requirements']
        for field in array_fields:
            if field in inputs:
                if isinstance(inputs[field], list):
                    # Filter out None values and convert non-string items to strings
                    structured_data[field] = [str(item) for item in inputs[field] if item is not None]
                elif inputs[field] is not None:
                    # Convert non-list values to a single-item list
                    structured_data[field] = [str(inputs[field])]
                else:
                    structured_data[field] = []
            else:
                structured_data[field] = []
        
        # Handle stakeholder objects
        if 'stakeholders' in inputs and isinstance(inputs['stakeholders'], list):
            structured_data['stakeholders'] = []
            for stakeholder in inputs['stakeholders']:
                if isinstance(stakeholder, dict):
                    # Ensure required fields
                    if 'name' in stakeholder and 'role' in stakeholder:
                        structured_data['stakeholders'].append({
                            'name': stakeholder['name'],
                            'role': stakeholder['role'],
                            'influence_level': stakeholder.get('influence_level', 'medium')
                        })
        else:
            structured_data['stakeholders'] = []
        
        return structured_data

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Process project intake information and provide business intelligence.
        
        Args:
            inputs: Dictionary containing project details including:
                - project_name: Name of the project
                - description: Detailed project description
                - business_objective: Primary business objective
                - industry: Industry sector
                - department: Department responsible
                - goals: List of project goals
                - success_criteria: List of success criteria
                - stakeholders: List of stakeholder objects
                - budget_range: Budget range category
                - timeline: Project timeline category
                - urgency: Project urgency level
                - expected_participants: Number of expected participants
                - geographic_scope: Geographic scope of the project
                - regulatory_requirements: List of regulatory requirements
                
        Returns:
            AgentResult with project data, business intelligence, and recommendations
        """
        start_time = time.monotonic()
        
        try:
            logger.info(f"Starting project intake for agent {self.agent_id}")
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={
                        "error": "Input validation failed",
                        "details": validation_result.errors
                    },
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Structure and normalize input data
            structured_data = self._structure_data(inputs)
            
            # Check for existing projects with similar names
            existing_projects = await self._check_existing_projects(structured_data.get('project_name', ''))
            if existing_projects:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={
                        "error": f"Similar project name already exists: {existing_projects[0]}",
                        "details": f"Please choose a different project name to avoid confusion with existing project: {existing_projects[0]}"
                    },
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Generate project ID
            project_id = f"proj_{uuid.uuid4().hex[:8]}"
            
            # Perform business intelligence analysis
            project_type = self._classify_project_type(structured_data)
            complexity_level, complexity_score = self._assess_project_complexity(structured_data)
            industry_context = self._analyze_industry_context(structured_data)
            budget_confidence = self._assess_budget_confidence(structured_data)
            intake_quality = self._assess_intake_quality(structured_data)
            
            # Compile business intelligence
            business_intelligence = {
                'project_type': project_type.value,
                'complexity': {
                    'level': complexity_level.value,
                    'score': complexity_score,
                    'factors': {
                        'stakeholder_count': len(structured_data.get('stakeholders', [])),
                        'goal_count': len(structured_data.get('goals', [])),
                        'timeline': structured_data.get('timeline', 'quarterly'),
                        'budget': structured_data.get('budget_range', '50k_to_250k'),
                        'urgency': structured_data.get('urgency', 'medium')
                    }
                },
                'industry_context': industry_context,
                'budget_confidence': budget_confidence,
                'intake_quality': intake_quality
            }
            
            # Generate recommendations
            recommendations = self._generate_recommendations(structured_data, business_intelligence)
            
            # Prepare project data for storage and response
            project_data = {
                'project_id': project_id,
                'project_name': structured_data.get('project_name', ''),
                'description': structured_data.get('description', ''),
                'business_objective': structured_data.get('business_objective', ''),
                'industry': structured_data.get('industry', ''),
                'department': structured_data.get('department', ''),
                'goals': structured_data.get('goals', []),
                'success_criteria': structured_data.get('success_criteria', []),
                'stakeholders': structured_data.get('stakeholders', []),
                'budget_range': structured_data.get('budget_range', ''),
                'timeline': structured_data.get('timeline', ''),
                'urgency': structured_data.get('urgency', ''),
                'expected_participants': structured_data.get('expected_participants', 0),
                'geographic_scope': structured_data.get('geographic_scope', ''),
                'regulatory_requirements': structured_data.get('regulatory_requirements', []),
                'created_at': time.time(),
                'created_by': inputs.get('user_id', 'anonymous')
            }
            
            # Store project data in MCP memory
            try:
                logger.info("AUDIT: Attempting to create KnowledgeEntity")
                
                # Create knowledge entity
                knowledge_entity = KnowledgeEntity(
                    title=f"Project Intake: {structured_data.get('project_name', '')}",
                    content=json.dumps({
                        **project_data,
                        'business_intelligence': business_intelligence
                    }),
                    content_type="application/json",
                    source="project_intake",
                    metadata={
                        'project_id': project_id,
                        'project_type': project_type.value,
                        'industry': structured_data.get('industry', ''),
                        'complexity': complexity_level.value,
                        'created_at': time.time()
                    },
                    creator_id=inputs.get('user_id', 'system'),
                    sensitivity=DataSensitivity.INTERNAL
                )
                
                # Store in MCP memory
                await self.mcp_client.create_entities([knowledge_entity])
                
                logger.info(f"AUDIT: Successfully created KnowledgeEntity")
                logger.info(f"Successfully stored project intake for {project_id}")
                
                mcp_storage_success = True
            except Exception as e:
                logger.error(f"AUDIT: Failed to create KnowledgeEntity: {e}")
                logger.error(f"Failed to store project data in memory: {e}")
                
                mcp_storage_success = False
                
                # If storage fails but we have all the data, we can still return it
                # This allows the workflow to continue even if persistence fails
                if not project_data:
                    return AgentResult(
                        status=AgentStatus.FAILED,
                        data={
                            "error": "Failed to store project data in memory",
                            "details": str(e)
                        },
                        execution_time_ms=int((time.monotonic() - start_time) * 1000),
                        error_details=f"MCP storage failed: {e}"
                    )
            
            # Prepare response data
            response_data = {
                'project_data': project_data,
                'business_intelligence': business_intelligence,
                'recommendations': recommendations,
                'analysis_summary': self._generate_analysis_summary(project_data, business_intelligence),
                'metadata': {
                    'agent_id': self.agent_id,
                    'execution_time': time.time(),
                    'mcp_storage_success': mcp_storage_success
                }
            }
            
            # Add all fields from project_data to the top level for backward compatibility
            response_data.update(project_data)
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Project intake completed in {execution_time_ms}ms")
            
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=response_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"An error occurred during core processing for agent {self.agent_id}: {e}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={
                    "error": f"An error occurred during core processing for agent {self.agent_id}: {e}",
                    "details": str(e)
                },
                execution_time_ms=execution_time_ms,
                error_details=str(e)
            )

    def _generate_analysis_summary(self, project_data: Dict[str, Any], 
                                 business_intelligence: Dict[str, Any]) -> str:
        """Generate a concise analysis summary for the project."""
        project_name = project_data.get('project_name', 'the project')
        project_type = business_intelligence.get('project_type', 'other')
        complexity = business_intelligence.get('complexity', {}).get('level', 'medium')
        industry = project_data.get('industry', 'the industry')
        
        # Format project type for readability
        formatted_project_type = project_type.replace('_', ' ').title()
        
        # Generate summary
        summary = f"This {formatted_project_type} project in the {industry} industry has {complexity} complexity. "
        
        # Add goal summary if available
        goals = project_data.get('goals', [])
        if goals:
            if len(goals) == 1:
                summary += f"The primary goal is to {goals[0].lower()}. "
            else:
                summary += f"Key goals include {goals[0].lower()}"
                if len(goals) > 1:
                    summary += f" and {goals[1].lower()}"
                summary += ". "
        
        # Add stakeholder summary if available
        stakeholders = project_data.get('stakeholders', [])
        if stakeholders:
            sponsor_count = sum(1 for s in stakeholders if s.get('role') == 'sponsor')
            user_count = sum(1 for s in stakeholders if s.get('role') == 'user')
            
            if sponsor_count > 0:
                summary += f"The project has {sponsor_count} sponsor(s) and {user_count} end user(s). "
        
        # Add timeline and budget summary
        timeline = project_data.get('timeline', '')
        budget_range = project_data.get('budget_range', '')
        
        if timeline and budget_range:
            # Format budget range for readability
            formatted_budget = budget_range.replace('_', ' to ').replace('under ', 'under $').replace('over ', 'over $')
            summary += f"It has a {timeline} timeline with a budget of {formatted_budget}."
        
        return summary