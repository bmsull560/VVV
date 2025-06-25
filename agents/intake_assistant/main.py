"""
Intake Assistant Agent

This agent serves as the primary entry point for users starting a new business case.
It gathers essential project information, validates inputs, structures data for downstream
agents, and provides intelligent guidance throughout the intake process.
"""

import logging
import time
import uuid
import statistics
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.memory_types import KnowledgeEntity
from agents.utils.validation import ValidationResult

logger = logging.getLogger(__name__)

class ProjectPhase(Enum):
    """Project development phases for lifecycle management."""
    PLANNING = "planning"
    ANALYSIS = "analysis"
    DEVELOPMENT = "development"
    IMPLEMENTATION = "implementation"
    EVALUATION = "evaluation"

class ProjectUrgency(Enum):
    """Project urgency levels for prioritization."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class StakeholderRole(Enum):
    """Stakeholder roles for project engagement."""
    SPONSOR = "sponsor"
    DECISION_MAKER = "decision_maker"
    TECHNICAL_LEAD = "technical_lead"
    BUSINESS_OWNER = "business_owner"
    END_USER = "end_user"
    FINANCIAL_APPROVER = "financial_approver"

class IntakeQuality(Enum):
    """Quality assessment levels for intake completeness."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    POOR = "poor"

class ProjectType(Enum):
    """Project type classifications for better routing."""
    COST_REDUCTION = "cost_reduction"
    REVENUE_GROWTH = "revenue_growth"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    DIGITAL_TRANSFORMATION = "digital_transformation"
    COMPLIANCE = "compliance"
    INNOVATION = "innovation"
    INFRASTRUCTURE = "infrastructure"

class IntakeAssistantAgent(BaseAgent):
    """
    Processes initial user input to structure and store comprehensive project information.
    Provides intelligent validation, guidance, and data structuring for business case development.
    """

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Set up comprehensive validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['project_name', 'description', 'business_objective'],
                'field_types': {
                    'project_name': 'string',
                    'description': 'string',
                    'business_objective': 'string',
                    'goals': 'array',
                    'stakeholders': 'array',
                    'budget_range': 'string',
                    'timeline': 'string',
                    'urgency': 'string',
                    'success_criteria': 'array',
                    'constraints': 'array',
                    'industry': 'string',
                    'department': 'string',
                    'project_phase': 'string',
                    'expected_participants': 'number',
                    'geographic_scope': 'string',
                    'regulatory_requirements': 'array'
                },
                'field_constraints': {
                    'project_name': {'min_length': 3, 'max_length': 100},
                    'description': {'min_length': 20, 'max_length': 2000},
                    'business_objective': {'min_length': 10, 'max_length': 500},
                    'budget_range': {'allowed_values': ['under_50k', '50k_to_250k', '250k_to_1m', 'over_1m', 'undefined']},
                    'timeline': {'allowed_values': ['immediate', 'quarterly', 'annual', 'multi_year', 'ongoing']},
                    'urgency': {'allowed_values': ['low', 'medium', 'high', 'critical']},
                    'project_phase': {'allowed_values': ['planning', 'analysis', 'development', 'implementation', 'evaluation']},
                    'expected_participants': {'min_value': 1, 'max_value': 10000},
                    'geographic_scope': {'allowed_values': ['local', 'regional', 'national', 'international', 'global']}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Enhanced industry classifications with business context
        self.industry_classifications = {
            'healthcare': {'risk_factor': 1.3, 'regulatory_complexity': 'high', 'typical_timeline_multiplier': 1.2},
            'financial_services': {'risk_factor': 1.4, 'regulatory_complexity': 'high', 'typical_timeline_multiplier': 1.3},
            'manufacturing': {'risk_factor': 1.1, 'regulatory_complexity': 'medium', 'typical_timeline_multiplier': 1.1},
            'retail': {'risk_factor': 0.9, 'regulatory_complexity': 'low', 'typical_timeline_multiplier': 0.9},
            'technology': {'risk_factor': 1.0, 'regulatory_complexity': 'low', 'typical_timeline_multiplier': 0.8},
            'education': {'risk_factor': 0.8, 'regulatory_complexity': 'medium', 'typical_timeline_multiplier': 1.1},
            'government': {'risk_factor': 1.2, 'regulatory_complexity': 'high', 'typical_timeline_multiplier': 1.4},
            'telecommunications': {'risk_factor': 1.1, 'regulatory_complexity': 'medium', 'typical_timeline_multiplier': 1.0},
            'energy': {'risk_factor': 1.3, 'regulatory_complexity': 'high', 'typical_timeline_multiplier': 1.2},
            'consulting': {'risk_factor': 0.9, 'regulatory_complexity': 'low', 'typical_timeline_multiplier': 0.9},
            'media': {'risk_factor': 1.0, 'regulatory_complexity': 'low', 'typical_timeline_multiplier': 0.9},
            'transportation': {'risk_factor': 1.2, 'regulatory_complexity': 'medium', 'typical_timeline_multiplier': 1.1},
            'real_estate': {'risk_factor': 1.0, 'regulatory_complexity': 'medium', 'typical_timeline_multiplier': 1.0},
            'non_profit': {'risk_factor': 0.7, 'regulatory_complexity': 'medium', 'typical_timeline_multiplier': 1.2},
            'other': {'risk_factor': 1.0, 'regulatory_complexity': 'medium', 'typical_timeline_multiplier': 1.0}
        }
        
        # Enhanced department classifications with complexity factors
        self.department_classifications = {
            'it': {'complexity_factor': 1.2, 'stakeholder_intensity': 'high'},
            'finance': {'complexity_factor': 1.3, 'stakeholder_intensity': 'high'},
            'operations': {'complexity_factor': 1.1, 'stakeholder_intensity': 'medium'},
            'sales': {'complexity_factor': 0.9, 'stakeholder_intensity': 'medium'},
            'marketing': {'complexity_factor': 0.8, 'stakeholder_intensity': 'medium'},
            'hr': {'complexity_factor': 1.0, 'stakeholder_intensity': 'high'},
            'customer_service': {'complexity_factor': 0.9, 'stakeholder_intensity': 'medium'},
            'procurement': {'complexity_factor': 1.1, 'stakeholder_intensity': 'medium'},
            'legal': {'complexity_factor': 1.4, 'stakeholder_intensity': 'high'},
            'executive': {'complexity_factor': 1.5, 'stakeholder_intensity': 'high'},
            'product': {'complexity_factor': 1.2, 'stakeholder_intensity': 'high'},
            'engineering': {'complexity_factor': 1.3, 'stakeholder_intensity': 'medium'},
            'quality': {'complexity_factor': 1.1, 'stakeholder_intensity': 'medium'},
            'security': {'complexity_factor': 1.4, 'stakeholder_intensity': 'high'},
            'compliance': {'complexity_factor': 1.3, 'stakeholder_intensity': 'high'},
            'strategy': {'complexity_factor': 1.5, 'stakeholder_intensity': 'high'},
            'other': {'complexity_factor': 1.0, 'stakeholder_intensity': 'medium'}
        }
        
        # Project type classification keywords for intelligent routing
        self.project_type_keywords = {
            ProjectType.COST_REDUCTION.value: [
                'cost', 'save', 'reduce', 'cut', 'eliminate', 'optimize', 'streamline', 'efficiency'
            ],
            ProjectType.REVENUE_GROWTH.value: [
                'revenue', 'sales', 'growth', 'expand', 'market', 'customer', 'profit', 'income'
            ],
            ProjectType.OPERATIONAL_EFFICIENCY.value: [
                'process', 'workflow', 'automation', 'productivity', 'performance', 'efficiency'
            ],
            ProjectType.DIGITAL_TRANSFORMATION.value: [
                'digital', 'technology', 'modernize', 'cloud', 'data', 'analytics', 'ai', 'machine learning'
            ],
            ProjectType.COMPLIANCE.value: [
                'compliance', 'regulatory', 'audit', 'governance', 'policy', 'standards', 'requirement'
            ],
            ProjectType.INNOVATION.value: [
                'innovation', 'new', 'research', 'development', 'breakthrough', 'competitive', 'advantage'
            ],
            ProjectType.INFRASTRUCTURE.value: [
                'infrastructure', 'system', 'platform', 'foundation', 'architecture', 'upgrade'
            ]
        }

    async def validate_inputs(self, inputs: Dict[str, Any]) -> ValidationResult:
        """Performs comprehensive validation of inputs using both base and custom rules."""
        # Perform base validation inherited from AgentBase
        base_validation_result = await super().validate_inputs(inputs)

        # Perform custom validations specific to IntakeAssistantAgent
        custom_errors = await self._custom_validations(inputs)

        # Combine results
        combined_errors = []
        if not base_validation_result.is_valid:
            combined_errors.extend(base_validation_result.errors)
        combined_errors.extend(custom_errors)

        return ValidationResult(is_valid=not combined_errors, errors=combined_errors)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Processes the project intake, validates, classifies, and stores data."""
        start_time = time.time()
        project_id = inputs.get('project_id', str(uuid.uuid4()))
        logger.info(f"[{self.agent_id}] Starting project intake for project_id: {project_id}")

        try:
            # 1. Input Validation
            validation_result = await self.validate_inputs(inputs)
            logger.debug(f"[{self.agent_id}] Input validation result: {validation_result.is_valid}, Errors: {validation_result.errors}")
            if not validation_result.is_valid:
                logger.warning(f"[{self.agent_id}] Input validation failed for project {project_id}: {validation_result.errors}")
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={'error': 'Input validation failed', 'details': validation_result.errors},
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            # 2. Check for existing similar projects
            project_name = inputs.get('project_name', '')
            logger.debug(f"[{self.agent_id}] Project name before check: '{project_name}'")
            if project_name:
                existing_projects = await self._check_existing_projects(project_name)
                if existing_projects:
                    logger.warning(f"[{self.agent_id}] Similar projects found for {project_id}: {existing_projects}")
                    return AgentResult(
                        status=AgentStatus.FAILED,
                        data={'error': 'Similar project name already exists', 'details': f"Found existing projects: {', '.join(existing_projects)}. Please choose a unique project name or update the existing one."},
                        execution_time_ms=int((time.time() - start_time) * 1000)
                    )

            # 2. Data Structuring and Normalization
            structured_data = self._structure_data(inputs)
            logger.info(f"[{self.agent_id}] Structured data for project {project_id}")

            # 3. Classification and Analysis
            logger.info(f"[{self.agent_id}] Starting classification for project {project_id}")
            try:
                classification_results = self._classify_project(structured_data)
                logger.info(f"[{self.agent_id}] Finished classification for project {project_id}: {classification_results}")
            except Exception as e:
                logger.error(f"[{self.agent_id}] Classification error for project {project_id}: {e}")
                classification_results = []
            
            # 4. Generate Recommendations and Analysis Summary
            recommendations = self._generate_recommendations(structured_data, classification_results)
            analysis_summary = self._generate_analysis_summary(structured_data, classification_results, recommendations)
            logger.info(f"[{self.agent_id}] Generated recommendations and analysis summary for project {project_id}")

            # 5. Store Data in Memory (MCP)
            mcp_storage_success = await self._store_in_mcp(project_id, structured_data, classification_results, analysis_summary, recommendations)
            logger.info(f"[{self.agent_id}] MCP storage success for project {project_id}: {mcp_storage_success}")

            # 6. Construct AgentResult
            result_data = {
                'project_id': project_id,
                'project_data': structured_data,
                'classification': classification_results,
                'recommendations': recommendations,
                'analysis_summary': analysis_summary,
                'metadata': {
                    'mcp_storage_success': mcp_storage_success
                }
            }
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            error_message = f"An unexpected error occurred during core processing for agent {self.agent_id}: {e}"
            logger.exception(error_message)
            return AgentResult(
                status=AgentStatus.FAILED,
                data={'error': error_message, 'details': str(e)},
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        errors = []
        stakeholders = inputs.get('stakeholders', [])

        # Example: Validate 'project_name' length
        project_name = inputs.get('project_name')
        if project_name and len(project_name) < 5:
            errors.append("Project name must be at least 5 characters long.")

        # Example: Validate 'description' content
        description = inputs.get('description')
        if description and "test" in description.lower():
            errors.append("Description cannot contain the word 'test'.")

        # Example: Validate 'goals' is not empty if provided
        goals = inputs.get('goals')
        if isinstance(goals, list) and not goals:
            errors.append("Goals cannot be an empty list if provided.")

        # Example: Validate 'budget_range' against allowed values
        if goals:
            for i, goal in enumerate(goals):
                if isinstance(goal, str):
                    goal_text = goal.strip()
                    if len(goal_text) < 10:
                        errors.append(f"Goal {i} must be at least 10 characters long for meaningful analysis")
                    elif not any(char.isupper() for char in goal_text):
                        errors.append(f"Goal {i} should include proper capitalization for professional presentation")
        
        # Enhanced success criteria validation
        success_criteria = inputs.get('success_criteria', [])
        if success_criteria:
            measurable_criteria = 0
            for i, criterion in enumerate(success_criteria):
                if isinstance(criterion, str):
                    criterion_text = criterion.strip()
                    if len(criterion_text) < 5:
                        errors.append(f"Success criterion {i} must be at least 5 characters long")
                    else:
                        # Check for measurable indicators
                        measurable_keywords = ['%', 'percent', 'reduce', 'increase', 'save', 'improve', 'achieve', 'target']
                        if any(keyword in criterion_text.lower() for keyword in measurable_keywords):
                            measurable_criteria += 1
            
            if len(success_criteria) > 2 and measurable_criteria == 0:
                errors.append("Consider including at least one measurable success criterion (with percentages, targets, or specific metrics)")
        
        # Business objective quality validation
        business_objective = inputs.get('business_objective', '').strip()
        if business_objective:
            if len(business_objective.split()) < 5:
                errors.append("Business objective should be at least 5 words for comprehensive analysis")
            
            # Check for actionable language
            actionable_keywords = ['improve', 'reduce', 'increase', 'achieve', 'implement', 'enhance', 'optimize', 'streamline']
            if not any(keyword in business_objective.lower() for keyword in actionable_keywords):
                errors.append("Business objective should include actionable language (improve, reduce, increase, achieve, etc.)")
        
        # Budget and timeline consistency validation
        budget_range = inputs.get('budget_range')
        timeline = inputs.get('timeline')
        urgency = inputs.get('urgency')
        
        if budget_range == 'over_1m' and timeline == 'immediate':
            errors.append("Large budget projects (>$1M) typically require longer timelines than 'immediate'")
        
        if urgency == 'critical' and timeline == 'multi_year':
            errors.append("Critical urgency projects typically shouldn't have multi-year timelines")
        
        # Expected participants validation
        expected_participants = inputs.get('expected_participants')
        if expected_participants is not None:
            if expected_participants < 1:
                errors.append("Expected participants must be at least 1")
            elif expected_participants > len(stakeholders) * 10 and len(stakeholders) > 0:
                errors.append("Expected participants seems unusually high compared to identified stakeholders. Please verify.")
        
        return errors

    async def _check_existing_projects(self, project_name: str) -> List[str]:
        """Check if a project with a similar name already exists in MCP memory using mcp2_search_nodes."""
        try:
            # Use mcp2_search_nodes to search for entities that match the project name
            # The query will search across entity names, types, and observation content.
            logger.debug(f"Searching MCP for existing projects with query: '{project_name}'")
            search_results = await self.mcp_client.search_nodes(query=project_name)

            existing_project_names = []
            for result in search_results:
                # The search_nodes tool returns a list of nodes, where each node is a dictionary.
                # We need to inspect the 'name' and 'observations' fields for project names.
                node_name = result.get('name', '').lower()
                node_observations = result.get('observations', [])
                
                # Check if the node name itself contains the project name
                if project_name.lower() in node_name:
                    existing_project_names.append(result.get('name'))
                    logger.debug(f"Found existing project by node name: {result.get('name')}")
                    continue # Move to the next result once found in name

                # Check if any observation contains the project name
                for obs in node_observations:
                    if isinstance(obs, str) and project_name.lower() in obs.lower():
                        # If the observation contains the project name, we can consider the node's name as a match
                        existing_project_names.append(result.get('name'))
                        logger.debug(f"Found existing project by observation content: {result.get('name')}")
                        break # Break from inner loop, move to next search result

            # Filter out duplicates and None values
            return list(set([name for name in existing_project_names if name is not None]))

        except Exception as e:
            logger.error(f"Error checking existing projects in MCP with query '{project_name}': {e}", exc_info=True)
            # Return empty list on error to avoid blocking validation, but log the error.
            return []

    def _classify_project_type(self, inputs: Dict[str, Any]) -> List[str]:
        """Classify project type based on business objective and description."""
        classification_scores = {}
        
        # Combine text fields for analysis
        text_to_analyze = ' '.join([
            inputs.get('business_objective', ''),
            inputs.get('description', ''),
            ' '.join(inputs.get('goals', []))
        ]).lower()
        
        # Score each project type based on keyword matches
        for project_type, keywords in self.project_type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_to_analyze:
                    score += 1
            
            if score > 0:
                classification_scores[project_type] = score / len(keywords)
        
        # Sort by score and return top classifications
        sorted_types = sorted(classification_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return types that score above 0.1 threshold
        return [ptype for ptype, score in sorted_types if score > 0.1]

    def _assess_intake_quality(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality and completeness of the intake information."""
        quality_factors = {
            'completeness_score': 0,
            'detail_quality_score': 0,
            'stakeholder_coverage_score': 0,
            'goal_clarity_score': 0,
            'overall_quality': IntakeQuality.POOR.value
        }
        
        # Calculate completeness score (percentage of fields provided)
        total_possible_fields = 13  # Number of main fields
        provided_fields = sum(1 for field in ['project_name', 'description', 'business_objective', 
                                             'goals', 'stakeholders', 'budget_range', 'timeline', 
                                             'urgency', 'success_criteria', 'constraints', 'industry', 
                                             'department', 'project_phase'] 
                             if inputs.get(field))
        quality_factors['completeness_score'] = (provided_fields / total_possible_fields) * 100
        
        # Assess detail quality
        detail_score = 0
        description = inputs.get('description', '')
        if len(description) > 100:
            detail_score += 25
        if len(description) > 300:
            detail_score += 25
        
        business_objective = inputs.get('business_objective', '')
        if len(business_objective) > 50:
            detail_score += 25
        if any(keyword in business_objective.lower() for keyword in ['improve', 'reduce', 'increase', 'achieve']):
            detail_score += 25
        
        quality_factors['detail_quality_score'] = detail_score
        
        # Assess stakeholder coverage
        stakeholders = inputs.get('stakeholders', [])
        stakeholder_score = min(100, len(stakeholders) * 20)  # Cap at 100%
        
        # Bonus for key roles
        roles = [s.get('role') for s in stakeholders if isinstance(s, dict)]
        if 'sponsor' in roles or 'decision_maker' in roles:
            stakeholder_score += 10
        if 'financial_approver' in roles:
            stakeholder_score += 10
        
        quality_factors['stakeholder_coverage_score'] = min(100, stakeholder_score)
        
        # Assess goal clarity
        goals = inputs.get('goals', [])
        goal_score = 0
        if goals:
            avg_goal_length = sum(len(str(goal)) for goal in goals) / len(goals)
            if avg_goal_length > 20:
                goal_score = 50
            if avg_goal_length > 50:
                goal_score = 100
        
        quality_factors['goal_clarity_score'] = goal_score
        
        # Calculate overall quality
        overall_score = (
            quality_factors['completeness_score'] * 0.3 +
            quality_factors['detail_quality_score'] * 0.25 +
            quality_factors['stakeholder_coverage_score'] * 0.25 +
            quality_factors['goal_clarity_score'] * 0.2
        )
        
        if overall_score >= 80:
            quality_factors['overall_quality'] = IntakeQuality.EXCELLENT.value
        elif overall_score >= 65:
            quality_factors['overall_quality'] = IntakeQuality.GOOD.value
        elif overall_score >= 45:
            quality_factors['overall_quality'] = IntakeQuality.ADEQUATE.value
        else:
            quality_factors['overall_quality'] = IntakeQuality.POOR.value
        
        quality_factors['overall_score'] = round(overall_score, 1)
        
        return quality_factors

    def _generate_enhanced_recommendations(self, inputs: Dict[str, Any], project_types: List[str], 
                                         quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced intelligent recommendations based on comprehensive analysis."""
        recommendations = {
            'template_suggestions': [],
            'stakeholder_suggestions': [],
            'timeline_recommendations': [],
            'risk_considerations': [],
            'next_steps': [],
            'agent_workflow_suggestions': [],
            'quality_improvement_suggestions': []
        }
        
        # Enhanced template suggestions based on project types
        template_mapping = {
            ProjectType.COST_REDUCTION.value: ['cost_reduction', 'operational_efficiency'],
            ProjectType.REVENUE_GROWTH.value: ['revenue_growth', 'market_expansion'],
            ProjectType.OPERATIONAL_EFFICIENCY.value: ['operational_efficiency', 'process_improvement'],
            ProjectType.DIGITAL_TRANSFORMATION.value: ['digital_transformation', 'technology_upgrade'],
            ProjectType.COMPLIANCE.value: ['compliance', 'governance'],
            ProjectType.INNOVATION.value: ['innovation', 'research_development'],
            ProjectType.INFRASTRUCTURE.value: ['infrastructure', 'system_upgrade']
        }
        
        for project_type in project_types:
            if project_type in template_mapping:
                recommendations['template_suggestions'].extend(template_mapping[project_type])
        
        # Default to standard ROI if no specific match
        if not recommendations['template_suggestions']:
            recommendations['template_suggestions'] = ['standard_roi', 'business_case_basic']
        
        # Remove duplicates and limit to 3
        recommendations['template_suggestions'] = list(set(recommendations['template_suggestions']))[:3]
        
        # Enhanced stakeholder suggestions
        existing_stakeholders = {s.get('role') for s in inputs.get('stakeholders', []) if isinstance(s, dict)}
        
        if 'financial_approver' not in existing_stakeholders:
            recommendations['stakeholder_suggestions'].append('Add a financial approver for budget approval and ROI validation')
        
        if 'technical_lead' not in existing_stakeholders and ProjectType.DIGITAL_TRANSFORMATION.value in project_types:
            recommendations['stakeholder_suggestions'].append('Include a technical lead for technology-related initiatives')
        
        if 'end_user' not in existing_stakeholders:
            recommendations['stakeholder_suggestions'].append('Consider adding end-user representatives for requirements validation')
        
        if len(existing_stakeholders) < 3:
            recommendations['stakeholder_suggestions'].append('Consider expanding stakeholder representation for comprehensive input')
        
        # Industry and department-specific recommendations
        industry = inputs.get('industry', '').lower()
        department = inputs.get('department', '').lower()
        
        if industry in self.industry_classifications:
            industry_data = self.industry_classifications[industry]
            if industry_data['regulatory_complexity'] == 'high':
                recommendations['risk_considerations'].append(f'{industry.title()} industry requires careful regulatory compliance planning')
            
            if industry_data['risk_factor'] > 1.2:
                recommendations['risk_considerations'].append(f'High-risk industry requires enhanced risk mitigation strategies')
        
        if department in self.department_classifications:
            dept_data = self.department_classifications[department]
            if dept_data['stakeholder_intensity'] == 'high':
                recommendations['stakeholder_suggestions'].append(f'{department.title()} projects typically require extensive stakeholder coordination')
        
        # Timeline recommendations based on complexity and urgency
        urgency = inputs.get('urgency', 'medium')
        budget_range = inputs.get('budget_range', 'undefined')
        timeline = inputs.get('timeline', 'quarterly')
        
        if urgency == 'critical' and budget_range in ['250k_to_1m', 'over_1m']:
            recommendations['timeline_recommendations'].append('Critical high-budget projects need accelerated decision-making processes')
        elif urgency == 'low' and timeline == 'immediate':
            recommendations['timeline_recommendations'].append('Low urgency projects can benefit from thorough planning phases')
        
        if budget_range == 'over_1m':
            recommendations['timeline_recommendations'].append('Large budget projects typically require extended approval cycles')
        
        # Agent workflow suggestions based on project characteristics
        recommended_agents = ['value_driver']
        
        if ProjectType.COST_REDUCTION.value in project_types:
            recommended_agents.extend(['cost_reduction', 'efficiency_analysis'])
        if ProjectType.REVENUE_GROWTH.value in project_types:
            recommended_agents.extend(['revenue_calculator', 'market_analysis'])
        if budget_range in ['250k_to_1m', 'over_1m']:
            recommended_agents.append('risk_mitigation')
        if len(inputs.get('stakeholders', [])) > 5:
            recommended_agents.append('collaboration_coordinator')
        
        recommendations['agent_workflow_suggestions'] = list(set(recommended_agents))
        
        # Quality improvement suggestions
        if quality_assessment['overall_quality'] in [IntakeQuality.POOR.value, IntakeQuality.ADEQUATE.value]:
            if quality_assessment['detail_quality_score'] < 50:
                recommendations['quality_improvement_suggestions'].append('Expand project description with more specific details')
            if quality_assessment['stakeholder_coverage_score'] < 50:
                recommendations['quality_improvement_suggestions'].append('Identify additional key stakeholders and their roles')
            if quality_assessment['goal_clarity_score'] < 50:
                recommendations['quality_improvement_suggestions'].append('Define more specific and measurable project goals')
        
        # Standard next steps
        recommendations['next_steps'] = [
            'Review and validate all project information',
            'Confirm stakeholder availability and engagement',
            'Proceed to template selection for business case development',
            'Begin detailed value driver analysis'
        ]
        
        return recommendations

    def _calculate_enhanced_project_complexity(self, inputs: Dict[str, Any], project_types: List[str]) -> Dict[str, Any]:
        """Calculate enhanced project complexity with industry and project type factors."""
        complexity_factors = {
            'stakeholder_complexity': 0,
            'goal_complexity': 0,
            'budget_complexity': 0,
            'timeline_complexity': 0,
            'urgency_complexity': 0,
            'industry_complexity': 0,
            'department_complexity': 0,
            'project_type_complexity': 0,
            'regulatory_complexity': 0
        }
        
        # Enhanced stakeholder complexity analysis
        stakeholders = inputs.get('stakeholders', [])
        stakeholder_count = len(stakeholders)
        
        if stakeholder_count <= 2:
            complexity_factors['stakeholder_complexity'] = 1
        elif stakeholder_count <= 5:
            complexity_factors['stakeholder_complexity'] = 2
        elif stakeholder_count <= 10:
            complexity_factors['stakeholder_complexity'] = 3
        else:
            complexity_factors['stakeholder_complexity'] = 4
        
        # Add complexity for stakeholder role diversity
        unique_roles = set(s.get('role') for s in stakeholders if isinstance(s, dict))
        if len(unique_roles) > 4:
            complexity_factors['stakeholder_complexity'] += 1
        
        # Enhanced goal complexity
        goals = inputs.get('goals', [])
        goal_count = len(goals)
        avg_goal_length = sum(len(str(goal)) for goal in goals) / max(1, goal_count)
        
        if goal_count <= 2:
            complexity_factors['goal_complexity'] = 1
        elif goal_count <= 5:
            complexity_factors['goal_complexity'] = 2
        else:
            complexity_factors['goal_complexity'] = 3
        
        # Add complexity for detailed goals
        if avg_goal_length > 100:
            complexity_factors['goal_complexity'] += 1
        
        # Enhanced budget complexity
        budget_range = inputs.get('budget_range', 'undefined')
        budget_complexity_map = {
            'under_50k': 1,
            '50k_to_250k': 2,
            '250k_to_1m': 3,
            'over_1m': 4,
            'undefined': 2
        }
        complexity_factors['budget_complexity'] = budget_complexity_map.get(budget_range, 2)
        
        # Enhanced timeline complexity
        timeline = inputs.get('timeline', 'quarterly')
        timeline_complexity_map = {
            'immediate': 4,
            'quarterly': 2,
            'annual': 3,
            'multi_year': 4,
            'ongoing': 3
        }
        complexity_factors['timeline_complexity'] = timeline_complexity_map.get(timeline, 2)
        
        # Enhanced urgency complexity
        urgency = inputs.get('urgency', 'medium')
        urgency_complexity_map = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }
        complexity_factors['urgency_complexity'] = urgency_complexity_map.get(urgency, 2)
        
        # Industry complexity factor
        industry = inputs.get('industry', '').lower()
        if industry in self.industry_classifications:
            industry_data = self.industry_classifications[industry]
            risk_factor = industry_data['risk_factor']
            
            if risk_factor <= 0.8:
                complexity_factors['industry_complexity'] = 1
            elif risk_factor <= 1.0:
                complexity_factors['industry_complexity'] = 2
            elif risk_factor <= 1.2:
                complexity_factors['industry_complexity'] = 3
            else:
                complexity_factors['industry_complexity'] = 4
                
            # Add regulatory complexity
            reg_complexity = industry_data['regulatory_complexity']
            if reg_complexity == 'high':
                complexity_factors['regulatory_complexity'] = 3
            elif reg_complexity == 'medium':
                complexity_factors['regulatory_complexity'] = 2
            else:
                complexity_factors['regulatory_complexity'] = 1
        else:
            complexity_factors['industry_complexity'] = 2
            complexity_factors['regulatory_complexity'] = 2
        
        # Department complexity factor
        department = inputs.get('department', '').lower()
        if department in self.department_classifications:
            dept_data = self.department_classifications[department]
            dept_complexity = dept_data['complexity_factor']
            
            if dept_complexity <= 0.9:
                complexity_factors['department_complexity'] = 1
            elif dept_complexity <= 1.1:
                complexity_factors['department_complexity'] = 2
            elif dept_complexity <= 1.3:
                complexity_factors['department_complexity'] = 3
            else:
                complexity_factors['department_complexity'] = 4
        else:
            complexity_factors['department_complexity'] = 2
        
        # Project type complexity
        type_complexity_map = {
            ProjectType.COST_REDUCTION.value: 2,
            ProjectType.REVENUE_GROWTH.value: 3,
            ProjectType.OPERATIONAL_EFFICIENCY.value: 2,
            ProjectType.DIGITAL_TRANSFORMATION.value: 4,
            ProjectType.COMPLIANCE.value: 3,
            ProjectType.INNOVATION.value: 4,
            ProjectType.INFRASTRUCTURE.value: 3
        }
        
        if project_types:
            max_type_complexity = max(type_complexity_map.get(ptype, 2) for ptype in project_types)
            complexity_factors['project_type_complexity'] = max_type_complexity
        else:
            complexity_factors['project_type_complexity'] = 2
        
        # Calculate weighted overall score
        weights = {
            'stakeholder_complexity': 0.15,
            'goal_complexity': 0.10,
            'budget_complexity': 0.15,
            'timeline_complexity': 0.15,
            'urgency_complexity': 0.10,
            'industry_complexity': 0.15,
            'department_complexity': 0.10,
            'project_type_complexity': 0.15,
            'regulatory_complexity': 0.15
        }
        
        overall_score = sum(complexity_factors[factor] * weights[factor] for factor in complexity_factors)
        
        # Determine complexity level
        if overall_score <= 1.5:
            complexity_level = 'low'
        elif overall_score <= 2.5:
            complexity_level = 'medium'
        elif overall_score <= 3.5:
            complexity_level = 'high'
        else:
            complexity_level = 'very_high'
        
        return {
            'overall_score': round(overall_score, 2),
            'complexity_level': complexity_level,
            'complexity_factors': complexity_factors,
            'risk_indicators': [factor for factor, score in complexity_factors.items() if score >= 3],
            'complexity_summary': f"Overall complexity is {complexity_level} (score: {overall_score:.1f}/4.0)"
        }

    def _generate_industry_intelligence(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate industry-specific intelligence and insights."""
        industry = inputs.get('industry', '').lower()
        
        intelligence = {
            'risk_factor': 1.0,
            'regulatory_complexity': 'medium',
            'typical_timeline_multiplier': 1.0,
            'industry_insights': [],
            'regulatory_considerations': [],
            'success_factors': []
        }
        
        if industry in self.industry_classifications:
            industry_data = self.industry_classifications[industry]
            intelligence.update(industry_data)
            
            # Industry-specific insights
            industry_insights_map = {
                'healthcare': [
                    'HIPAA compliance required for patient data',
                    'FDA approval may be needed for medical devices',
                    'Clinical validation often extends timelines'
                ],
                'financial_services': [
                    'SOX compliance critical for financial reporting',
                    'Regulatory approval processes can be lengthy',
                    'Data security and privacy are paramount'
                ],
                'manufacturing': [
                    'Safety protocols must be rigorously followed',
                    'Supply chain disruptions can impact timelines',
                    'Quality standards certification may be required'
                ],
                'technology': [
                    'Rapid technology evolution requires agile approaches',
                    'Scalability considerations are critical',
                    'Security and privacy by design essential'
                ],
                'government': [
                    'Procurement processes can be complex and lengthy',
                    'Public transparency requirements must be met',
                    'Budget approval cycles may impact timing'
                ]
            }
            
            intelligence['industry_insights'] = industry_insights_map.get(industry, [
                'Industry-specific regulations may apply',
                'Market conditions should be monitored',
                'Competitive landscape analysis recommended'
            ])
            
            # Regulatory considerations
            if intelligence['regulatory_complexity'] == 'high':
                intelligence['regulatory_considerations'] = [
                    'Early regulatory consultation recommended',
                    'Compliance documentation must be comprehensive',
                    'Regular compliance audits may be required',
                    'Legal review essential for all major decisions'
                ]
            elif intelligence['regulatory_complexity'] == 'medium':
                intelligence['regulatory_considerations'] = [
                    'Standard compliance frameworks should be followed',
                    'Industry best practices must be observed',
                    'Periodic compliance reviews recommended'
                ]
            else:
                intelligence['regulatory_considerations'] = [
                    'Basic regulatory compliance sufficient',
                    'Standard business practices apply'
                ]
        
        return intelligence

    def _assess_budget_confidence(self, inputs: Dict[str, Any]) -> str:
        """Assess confidence level in budget estimates."""
        budget_range = inputs.get('budget_range', 'undefined')
        
        if budget_range == 'undefined':
            return 'very_low'
        
        # Check for detailed financial planning indicators
        financial_indicators = 0
        
        if inputs.get('success_criteria'):
            # Look for quantified success criteria
            for criterion in inputs.get('success_criteria', []):
                if any(indicator in str(criterion).lower() for indicator in ['%', 'dollar', '$', 'cost', 'save']):
                    financial_indicators += 1
        
        if inputs.get('constraints'):
            # Look for budget-related constraints
            for constraint in inputs.get('constraints', []):
                if any(indicator in str(constraint).lower() for indicator in ['budget', 'cost', 'funding', 'financial']):
                    financial_indicators += 1
        
        # Check stakeholder financial expertise
        stakeholders = inputs.get('stakeholders', [])
        has_financial_approver = any(s.get('role') == 'financial_approver' for s in stakeholders if isinstance(s, dict))
        
        if has_financial_approver:
            financial_indicators += 2
        
        # Determine confidence based on indicators
        if financial_indicators >= 4:
            return 'high'
        elif financial_indicators >= 2:
            return 'medium'
        elif financial_indicators >= 1:
            return 'low'
        else:
            return 'very_low'

    def _estimate_budget_midpoint(self, budget_range: str) -> int:
        """Estimate budget midpoint for planning purposes."""
        budget_estimates = {
            'under_50k': 25000,
            '50k_to_250k': 150000,
            '250k_to_1m': 625000,
            'over_1m': 2000000,
            'undefined': 0
        }
        
        return budget_estimates.get(budget_range, 0)

    def _identify_initial_risk_factors(self, inputs: Dict[str, Any], complexity_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify initial risk factors based on intake information."""
        risk_factors = []
        
        # High complexity risks
        if complexity_analysis['complexity_level'] in ['high', 'very_high']:
            risk_factors.append({
                'type': 'complexity',
                'description': f"High project complexity ({complexity_analysis['complexity_level']}) increases delivery risk",
                'impact': 'medium',
                'likelihood': 'high'
            })
        
        # Stakeholder risks
        stakeholders = inputs.get('stakeholders', [])
        if len(stakeholders) > 8:
            risk_factors.append({
                'type': 'stakeholder',
                'description': 'Large stakeholder group may create coordination challenges',
                'impact': 'medium',
                'likelihood': 'medium'
            })
        elif len(stakeholders) < 2:
            risk_factors.append({
                'type': 'stakeholder',
                'description': 'Limited stakeholder engagement may affect project success',
                'impact': 'medium',
                'likelihood': 'high'
            })
        
        # Budget risks
        budget_range = inputs.get('budget_range', 'undefined')
        if budget_range == 'undefined':
            risk_factors.append({
                'type': 'financial',
                'description': 'Undefined budget creates planning and approval risks',
                'impact': 'high',
                'likelihood': 'high'
            })
        elif budget_range == 'over_1m':
            risk_factors.append({
                'type': 'financial',
                'description': 'Large budget projects face increased scrutiny and approval complexity',
                'impact': 'medium',
                'likelihood': 'medium'
            })
        
        # Timeline risks
        timeline = inputs.get('timeline', 'quarterly')
        urgency = inputs.get('urgency', 'medium')
        
        if timeline == 'immediate' and urgency != 'critical':
            risk_factors.append({
                'type': 'timeline',
                'description': 'Immediate timeline without critical urgency may indicate unclear priorities',
                'impact': 'low',
                'likelihood': 'medium'
            })
        elif urgency == 'critical' and timeline in ['annual', 'multi_year']:
            risk_factors.append({
                'type': 'timeline',
                'description': 'Critical urgency with extended timeline creates conflicting expectations',
                'impact': 'medium',
                'likelihood': 'high'
            })
        
        # Industry-specific risks
        industry = inputs.get('industry', '').lower()
        if industry in self.industry_classifications:
            industry_data = self.industry_classifications[industry]
            if industry_data['risk_factor'] > 1.2:
                risk_factors.append({
                    'type': 'regulatory',
                    'description': f'High-risk industry ({industry}) requires enhanced compliance and risk management',
                    'impact': 'high',
                    'likelihood': 'medium'
                })
        
        return risk_factors

    def _calculate_project_readiness_score(self, quality_assessment: Dict[str, Any], complexity_analysis: Dict[str, Any]) -> float:
        """Calculate overall project readiness score."""
        # Base score from quality assessment
        quality_score = quality_assessment['overall_score']
        
        # Adjust for complexity (higher complexity reduces readiness)
        complexity_penalty = {
            'low': 0,
            'medium': 10,
            'high': 20,
            'very_high': 30
        }
        
        complexity_level = complexity_analysis['complexity_level']
        adjusted_score = quality_score - complexity_penalty.get(complexity_level, 10)
        
        # Ensure score is between 0 and 100
        readiness_score = max(0, min(100, adjusted_score))
        
        return round(readiness_score, 1)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Process initial user input to structure and store comprehensive project information.
        
        Enhanced with business intelligence, quality assessment, and production-ready features.
        
        Args:
            inputs: Dictionary containing project information fields
        
        Returns:
            AgentResult with structured project data, recommendations, and analysis
        """
        start_time = time.monotonic()
        execution_time_ms = 0 # Initialize to 0

        try:
            logger.info(f"Starting enhanced intake processing for agent {self.agent_id} with inputs: {inputs.keys()}")
            
            # Perform comprehensive input validation
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                logger.warning(f"Input validation failed for agent {self.agent_id}: {validation_result.errors}")
                execution_time_ms = int((time.monotonic() - start_time) * 1000)
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={'error': 'Input validation failed', 'details': validation_result.errors},
                    execution_time_ms=execution_time_ms,
                    error_details=f"Input validation failed: {validation_result.errors}"
                )
            
            try:
                # Generate unique project ID with timestamp for better tracking
                project_name_for_id = inputs.get('project_name', 'unknown_project').replace(' ', '_').lower()
                project_id = f"proj_{project_name_for_id}_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
                logger.debug(f"Generated project ID: {project_id}")

                # Enhanced business intelligence analysis
                project_types = self._classify_project_type(inputs)
                logger.debug(f"Classified project types: {project_types}")

                quality_assessment = self._assess_intake_quality(inputs)
                logger.debug(f"Assessed intake quality: {quality_assessment}")
                
                # Calculate enhanced project complexity with industry factors
                complexity_analysis = self._calculate_enhanced_project_complexity(inputs, project_types)
                logger.debug(f"Calculated complexity analysis: {complexity_analysis}")
                
                # Generate comprehensive recommendations
                recommendations = self._generate_enhanced_recommendations(inputs, project_types, quality_assessment)
                logger.debug(f"Generated recommendations: {recommendations}")
                
                # Industry and department intelligence
                industry_intelligence = self._generate_industry_intelligence(inputs)
                logger.debug(f"Generated industry intelligence: {industry_intelligence}")

                # Identify initial risk factors
                risk_factors = self._identify_initial_risk_factors(inputs, complexity_analysis)
                logger.debug(f"Identified initial risk factors: {risk_factors}")

                # Calculate project readiness score
                readiness_score = self._calculate_project_readiness_score(quality_assessment, complexity_analysis)
                logger.debug(f"Calculated project readiness score: {readiness_score}")
                
                # Structure comprehensive project data with business intelligence
                project_data = {
                    'project_id': project_id,
                    'basic_info': {
                        'project_name': inputs.get('project_name', ''),
                        'description': inputs.get('description', ''),
                        'business_objective': inputs.get('business_objective', ''),
                        'industry': inputs.get('industry', ''),
                        'department': inputs.get('department', ''),
                        'created_timestamp': datetime.now().isoformat(),
                        'project_phase': inputs.get('project_phase', ProjectPhase.PLANNING.value)
                    },
                    'business_context': {
                        'project_types': project_types,
                        'primary_classification': project_types[0] if project_types else 'unclassified',
                        'goals': inputs.get('goals', []),
                        'success_criteria': inputs.get('success_criteria', []),
                        'constraints': inputs.get('constraints', []),
                        'expected_participants': inputs.get('expected_participants', 0),
                        'geographic_scope': inputs.get('geographic_scope', 'local'),
                        'regulatory_requirements': inputs.get('regulatory_requirements', [])
                    },
                    'stakeholders': inputs.get('stakeholders', []),
                    'financial_scope': {
                        'budget_range': inputs.get('budget_range', 'undefined'),
                        'timeline': inputs.get('timeline', 'quarterly'),
                        'urgency': inputs.get('urgency', ProjectUrgency.MEDIUM.value),
                        'budget_confidence': self._assess_budget_confidence(inputs),
                        'estimated_budget_midpoint': self._estimate_budget_midpoint(inputs.get('budget_range'))
                    },
                    'analysis_results': {
                        'quality_assessment': quality_assessment,
                        'complexity_analysis': complexity_analysis,
                        'industry_intelligence': industry_intelligence,
                        'risk_factors': risk_factors,
                        'readiness_score': readiness_score
                    }
                }
                logger.debug(f"Structured project data for {project_id}")
                
                # Create enhanced knowledge entity for MCP memory storage
                knowledge_entity = KnowledgeEntity(
                    id=f"intake_{project_id}",
                    title=f"Project Intake: {inputs.get('project_name', 'Unknown')}",
                    content={
                        'project_data': project_data,
                        'input_validation': {
                            'validation_passed': True,
                            'validation_timestamp': datetime.now().isoformat(),
                            'quality_score': quality_assessment['overall_score']
                        },
                        'business_intelligence': {
                            'primary_project_type': project_types[0] if project_types else 'unclassified',
                            'complexity_score': complexity_analysis['overall_score'],
                            'industry_risk_factor': industry_intelligence.get('risk_factor', 1.0),
                            'recommended_next_agents': recommendations['agent_workflow_suggestions']
                        }
                    },
                    metadata={
                        'agent_id': self.agent_id,
                        'created_at': datetime.now().isoformat(),
                        'project_id': project_id,
                        'industry': inputs.get('industry', 'unknown'),
                        'department': inputs.get('department', 'unknown'),
                        'urgency_level': inputs.get('urgency', 'medium'),
                        'budget_range': inputs.get('budget_range', 'undefined'),
                        'stakeholder_count': len(inputs.get('stakeholders', [])),
                        'intake_quality': quality_assessment['overall_quality']
                    }
                )
                
                # Store in MCP episodic memory
                try:
                    # Audit log before writing to memory
                    logger.info(f"AUDIT: Attempting to create KnowledgeEntity for project {project_id} in MCP. Entity ID: {knowledge_entity.id}")
                    await self.mcp_client.create_entities([knowledge_entity])
                    logger.info(f"Successfully stored project intake for {project_id} in MCP. Entity ID: {knowledge_entity.id}")
                    # Audit log after successful write
                    logger.info(f"AUDIT: Successfully created KnowledgeEntity. Entity ID: {knowledge_entity.id}")
                except Exception as mem_e:
                    logger.error(f"Failed to store knowledge entity for {project_id} in MCP: {mem_e}", exc_info=True)
                    # Audit log for failed write
                    logger.critical(f"AUDIT: Failed to create KnowledgeEntity. Entity ID: {knowledge_entity.id}. Error: {mem_e}")
                    execution_time_ms = int((time.monotonic() - start_time) * 1000)
                    return AgentResult(
                        status=AgentStatus.FAILED,
                        data={'error': 'Failed to store project data in memory', 'details': str(mem_e)},
                        execution_time_ms=execution_time_ms,
                        error_details=f"MCP storage failed: {str(mem_e)}"
                    )

                # Store working memory for workflow coordination
                working_memory = {
                    'current_project_id': project_id,
                    'last_agent': 'intake_assistant',
                    'workflow_state': 'intake_complete',
                    'recommended_next_steps': recommendations['next_steps'],
                    'recommended_agents': recommendations['agent_workflow_suggestions'],
                    'complexity_level': complexity_analysis['complexity_level'],
                    'quality_level': quality_assessment['overall_quality']
                }
                logger.debug(f"Prepared working memory for {project_id}")
                
                execution_time_ms = int((time.monotonic() - start_time) * 1000)
                
                # Structure comprehensive response data
                response_data = {
                    'project_data': project_data,
                    'recommendations': recommendations,
                    'analysis_summary': {
                        'intake_quality': quality_assessment['overall_quality'],
                        'quality_score': quality_assessment['overall_score'],
                        'project_complexity': complexity_analysis['complexity_level'],
                        'complexity_score': complexity_analysis['overall_score'],
                        'primary_project_type': project_types[0] if project_types else 'unclassified',
                        'identified_project_types': project_types,
                        'readiness_score': project_data['analysis_results']['readiness_score']
                    },
                    'next_steps': recommendations['next_steps'],
                    'working_memory': working_memory,
                    'metadata': {
                        'processing_time_ms': execution_time_ms,
                        'agent_version': '2.0',
                        'validation_passed': True,
                        'mcp_storage_success': True # This will be true if the try block above succeeded
                    }
                }
                
                logger.info(f"Enhanced intake processing completed successfully in {execution_time_ms}ms for project {project_id}")
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data=response_data,
                    execution_time_ms=execution_time_ms
                )
            
            except Exception as e:
                execution_time_ms = int((time.monotonic() - start_time) * 1000)
                error_msg = f"An error occurred during core processing for agent {self.agent_id}: {e}"
                logger.error(error_msg, exc_info=True)
                
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={'error': error_msg, 'execution_time_ms': execution_time_ms},
                    execution_time_ms=execution_time_ms,
                    error_details=error_msg
                )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            error_msg = f"An unexpected error occurred during intake processing for agent {self.agent_id}: {e}"
            logger.critical(error_msg, exc_info=True)
            
            return AgentResult(
                status=AgentStatus.FAILED,
                data={'error': error_msg, 'execution_time_ms': execution_time_ms},
                execution_time_ms=execution_time_ms,
                error_details=error_msg
            )
