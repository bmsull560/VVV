"""
Intake Assistant Agent

This agent serves as the primary entry point for users starting a new business case.
It gathers essential project information, validates inputs, structures data for downstream
agents, and provides intelligent guidance throughout the intake process.
"""

import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from enum import Enum

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.types import KnowledgeEntity

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
                    'project_phase': 'string'
                },
                'field_constraints': {
                    'project_name': {'min_length': 3, 'max_length': 100},
                    'description': {'min_length': 20, 'max_length': 2000},
                    'business_objective': {'min_length': 10, 'max_length': 500},
                    'budget_range': {'allowed_values': ['under_50k', '50k_to_250k', '250k_to_1m', 'over_1m', 'undefined']},
                    'timeline': {'allowed_values': ['immediate', 'quarterly', 'annual', 'multi_year', 'ongoing']},
                    'urgency': {'allowed_values': ['low', 'medium', 'high', 'critical']},
                    'project_phase': {'allowed_values': ['planning', 'analysis', 'development', 'implementation', 'evaluation']}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Common industry classifications
        self.industry_classifications = [
            'healthcare', 'financial_services', 'manufacturing', 'retail', 'technology',
            'education', 'government', 'telecommunications', 'energy', 'consulting',
            'media', 'transportation', 'real_estate', 'non_profit', 'other'
        ]
        
        # Department classifications
        self.department_classifications = [
            'it', 'finance', 'operations', 'sales', 'marketing', 'hr', 'customer_service',
            'procurement', 'legal', 'executive', 'product', 'engineering', 'quality',
            'security', 'compliance', 'strategy', 'other'
        ]

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Perform intake-specific validations beyond standard validations."""
        errors = []
        
        # Validate project name uniqueness
        project_name = inputs.get('project_name', '').strip()
        if project_name:
            # Check for potential duplicate project names
            existing_projects = await self._check_existing_projects(project_name)
            if existing_projects:
                errors.append(f"Similar project name already exists: '{existing_projects[0]}'. Consider using a more specific name.")
        
        # Validate industry classification
        industry = inputs.get('industry', '').lower()
        if industry and industry not in self.industry_classifications:
            errors.append(f"Invalid industry '{industry}'. Must be one of: {', '.join(self.industry_classifications)}")
        
        # Validate department classification
        department = inputs.get('department', '').lower()
        if department and department not in self.department_classifications:
            errors.append(f"Invalid department '{department}'. Must be one of: {', '.join(self.department_classifications)}")
        
        # Validate stakeholders structure
        stakeholders = inputs.get('stakeholders', [])
        if stakeholders:
            for i, stakeholder in enumerate(stakeholders):
                if not isinstance(stakeholder, dict):
                    errors.append(f"Stakeholder {i} must be an object with 'name' and 'role' fields")
                    continue
                    
                if 'name' not in stakeholder or not stakeholder['name'].strip():
                    errors.append(f"Stakeholder {i} missing required 'name' field")
                    
                if 'role' not in stakeholder:
                    errors.append(f"Stakeholder {i} missing required 'role' field")
                elif stakeholder['role'] not in [role.value for role in StakeholderRole]:
                    valid_roles = [role.value for role in StakeholderRole]
                    errors.append(f"Stakeholder {i} has invalid role '{stakeholder['role']}'. Must be one of: {', '.join(valid_roles)}")
        
        # Validate goals are meaningful
        goals = inputs.get('goals', [])
        if goals:
            for i, goal in enumerate(goals):
                if isinstance(goal, str) and len(goal.strip()) < 10:
                    errors.append(f"Goal {i} must be at least 10 characters long for meaningful analysis")
        
        # Validate success criteria
        success_criteria = inputs.get('success_criteria', [])
        if success_criteria:
            for i, criterion in enumerate(success_criteria):
                if isinstance(criterion, str) and len(criterion.strip()) < 5:
                    errors.append(f"Success criterion {i} must be at least 5 characters long")
        
        return errors

    async def _check_existing_projects(self, project_name: str) -> List[str]:
        """Check for existing projects with similar names."""
        try:
            # Search for similar project names in MCP memory
            similar_projects = await self.mcp_client.search_memory(
                "episodic",
                query=f"project_name:{project_name}",
                tags=["project_intake", "project_metadata"]
            )
            return [proj.get('project_name', '') for proj in similar_projects[:3]]
        except Exception as e:
            logger.warning(f"Could not check existing projects: {str(e)}")
            return []

    def _generate_project_recommendations(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent recommendations based on project inputs."""
        recommendations = {
            'template_suggestions': [],
            'stakeholder_suggestions': [],
            'timeline_recommendations': [],
            'risk_considerations': [],
            'next_steps': []
        }
        
        # Template suggestions based on business objective
        business_objective = inputs.get('business_objective', '').lower()
        if 'cost' in business_objective or 'save' in business_objective:
            recommendations['template_suggestions'].append('cost_reduction')
        if 'revenue' in business_objective or 'sales' in business_objective:
            recommendations['template_suggestions'].append('revenue_growth')
        if 'digital' in business_objective or 'technology' in business_objective:
            recommendations['template_suggestions'].append('digital_transformation')
        if 'efficiency' in business_objective or 'process' in business_objective:
            recommendations['template_suggestions'].append('operational_efficiency')
        
        # Default to standard ROI if no specific match
        if not recommendations['template_suggestions']:
            recommendations['template_suggestions'].append('standard_roi')
        
        # Stakeholder suggestions based on project type
        existing_stakeholders = {s.get('role') for s in inputs.get('stakeholders', [])}
        if 'financial_approver' not in existing_stakeholders:
            recommendations['stakeholder_suggestions'].append('Consider adding a financial approver for budget decisions')
        if 'technical_lead' not in existing_stakeholders and 'technology' in business_objective:
            recommendations['stakeholder_suggestions'].append('Add a technical lead for technology-related projects')
        
        # Timeline recommendations
        urgency = inputs.get('urgency', 'medium')
        budget_range = inputs.get('budget_range', 'undefined')
        
        if urgency == 'critical' and budget_range in ['250k_to_1m', 'over_1m']:
            recommendations['timeline_recommendations'].append('High-budget critical projects may require extended planning phase')
        elif urgency == 'low':
            recommendations['timeline_recommendations'].append('Low urgency allows for thorough analysis and stakeholder alignment')
        
        # Risk considerations
        if budget_range == 'over_1m':
            recommendations['risk_considerations'].append('Large budget requires comprehensive risk assessment and governance')
        if len(inputs.get('stakeholders', [])) > 8:
            recommendations['risk_considerations'].append('Multiple stakeholders may increase coordination complexity')
        
        # Next steps
        recommendations['next_steps'] = [
            'Review and validate stakeholder list',
            'Define detailed success criteria',
            'Schedule stakeholder alignment meeting',
            'Begin value driver analysis'
        ]
        
        return recommendations

    def _calculate_project_complexity_score(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate a complexity score for the project."""
        complexity_factors = {
            'stakeholder_count': len(inputs.get('stakeholders', [])),
            'goal_count': len(inputs.get('goals', [])),
            'constraint_count': len(inputs.get('constraints', [])),
            'budget_complexity': 1,
            'timeline_complexity': 1,
            'urgency_factor': 1
        }
        
        # Budget complexity scoring
        budget_range = inputs.get('budget_range', 'undefined')
        budget_scores = {
            'under_50k': 1, '50k_to_250k': 2, '250k_to_1m': 3, 'over_1m': 4, 'undefined': 2
        }
        complexity_factors['budget_complexity'] = budget_scores.get(budget_range, 2)
        
        # Timeline complexity scoring
        timeline = inputs.get('timeline', 'quarterly')
        timeline_scores = {
            'immediate': 4, 'quarterly': 2, 'annual': 3, 'multi_year': 4, 'ongoing': 3
        }
        complexity_factors['timeline_complexity'] = timeline_scores.get(timeline, 2)
        
        # Urgency factor
        urgency = inputs.get('urgency', 'medium')
        urgency_scores = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        complexity_factors['urgency_factor'] = urgency_scores.get(urgency, 2)
        
        # Calculate overall complexity score (1-10 scale)
        total_score = (
            min(complexity_factors['stakeholder_count'], 10) * 0.2 +
            min(complexity_factors['goal_count'], 5) * 0.15 +
            min(complexity_factors['constraint_count'], 5) * 0.15 +
            complexity_factors['budget_complexity'] * 0.25 +
            complexity_factors['timeline_complexity'] * 0.15 +
            complexity_factors['urgency_factor'] * 0.10
        )
        
        complexity_level = 'low'
        if total_score >= 7:
            complexity_level = 'high'
        elif total_score >= 4:
            complexity_level = 'medium'
        
        return {
            'complexity_score': round(total_score, 2),
            'complexity_level': complexity_level,
            'complexity_factors': complexity_factors
        }

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Process initial user input to structure and store comprehensive project information.

        Args:
            inputs: Dictionary containing:
                - project_name: Name of the project
                - description: Detailed project description
                - business_objective: Primary business objective
                - goals: List of project goals
                - stakeholders: List of stakeholder objects with name and role
                - budget_range: Budget classification
                - timeline: Project timeline
                - urgency: Project urgency level
                - success_criteria: List of success criteria
                - constraints: List of project constraints
                - industry: Industry classification
                - department: Department classification
                - project_phase: Current project phase

        Returns:
            AgentResult with structured project data and recommendations
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
            # Generate unique project ID
            project_id = f"proj_{uuid.uuid4().hex[:8]}"
            
            # Calculate project complexity
            complexity_analysis = self._calculate_project_complexity_score(inputs)
            
            # Generate intelligent recommendations
            recommendations = self._generate_project_recommendations(inputs)
            
            # Structure comprehensive project data
            project_data = {
                'project_id': project_id,
                'project_name': inputs['project_name'].strip(),
                'description': inputs['description'].strip(),
                'business_objective': inputs['business_objective'].strip(),
                'goals': inputs.get('goals', []),
                'stakeholders': inputs.get('stakeholders', []),
                'budget_range': inputs.get('budget_range', 'undefined'),
                'timeline': inputs.get('timeline', 'quarterly'),
                'urgency': inputs.get('urgency', 'medium'),
                'success_criteria': inputs.get('success_criteria', []),
                'constraints': inputs.get('constraints', []),
                'industry': inputs.get('industry', 'other'),
                'department': inputs.get('department', 'other'),
                'project_phase': inputs.get('project_phase', 'planning'),
                'complexity_analysis': complexity_analysis,
                'intake_timestamp': time.time(),
                'status': 'active'
            }
            
            # Create KnowledgeEntity for persistent storage
            entity_id = f"project_metadata_{project_id}"
            content = f"""
Project: {project_data['project_name']}
Description: {project_data['description']}
Business Objective: {project_data['business_objective']}
Goals: {'; '.join(project_data['goals'])}
Industry: {project_data['industry']}
Department: {project_data['department']}
Complexity Level: {complexity_analysis['complexity_level']}
Budget Range: {project_data['budget_range']}
Timeline: {project_data['timeline']}
Urgency: {project_data['urgency']}
            """.strip()
            
            knowledge_entity = KnowledgeEntity(
                entity_id=entity_id,
                content=content,
                metadata=project_data,
                tags=["project_intake", "project_metadata", f"industry_{project_data['industry']}"],
                confidence_score=0.95
            )
            
            # Store in MCP memory
            await self.mcp_client.store_knowledge_entity(knowledge_entity)
            
            # Store working memory for workflow coordination
            await self.mcp_client.store_memory(
                "working",
                "project_intake",
                {
                    "project_id": project_id,
                    "project_name": project_data['project_name'],
                    "complexity_level": complexity_analysis['complexity_level'],
                    "recommended_templates": recommendations['template_suggestions'],
                    "stakeholder_count": len(project_data['stakeholders'])
                },
                ["project_intake", "workflow_step"]
            )
            
            # Prepare result data
            result_data = {
                'project_data': project_data,
                'recommendations': recommendations,
                'complexity_analysis': complexity_analysis,
                'next_steps': {
                    'immediate': 'Proceed to template selection based on business objective',
                    'workflow_suggestions': recommendations['next_steps'],
                    'recommended_agents': ['template_selector', 'value_driver', 'stakeholder_analysis']
                },
                'validation_summary': {
                    'input_completeness': len(inputs) / 13 * 100,  # Percentage of optional fields provided
                    'stakeholder_coverage': len(project_data['stakeholders']),
                    'goal_clarity': len(project_data['goals']),
                    'constraint_awareness': len(project_data['constraints'])
                }
            }
            
            logger.info(f"Project intake complete: {project_data['project_name']} (ID: {project_id})")
            logger.info(f"Complexity: {complexity_analysis['complexity_level']}, Template suggestions: {recommendations['template_suggestions']}")
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Project intake failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Project intake failed: {str(e)}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
