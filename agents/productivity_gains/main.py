"""
Productivity Gains Agent

This agent analyzes and quantifies productivity improvements from various business initiatives.
It evaluates time savings, efficiency gains, quality improvements, and their financial impact
across different business functions and processes.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from enum import Enum

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.types import KnowledgeEntity

logger = logging.getLogger(__name__)

class ProductivityCategory(Enum):
    """Categories of productivity improvement opportunities."""
    AUTOMATION = "automation"
    PROCESS_IMPROVEMENT = "process_improvement"
    TECHNOLOGY_UPGRADE = "technology_upgrade"
    TRAINING_DEVELOPMENT = "training_development"
    COLLABORATION_TOOLS = "collaboration_tools"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    QUALITY_IMPROVEMENT = "quality_improvement"
    KNOWLEDGE_MANAGEMENT = "knowledge_management"
    DECISION_SUPPORT = "decision_support"
    COMMUNICATION_EFFICIENCY = "communication_efficiency"

class ProductivityMetric(Enum):
    """Types of productivity metrics."""
    TIME_SAVINGS = "time_savings"
    ERROR_REDUCTION = "error_reduction"
    OUTPUT_INCREASE = "output_increase"
    CYCLE_TIME_REDUCTION = "cycle_time_reduction"
    QUALITY_IMPROVEMENT = "quality_improvement"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    EMPLOYEE_SATISFACTION = "employee_satisfaction"

class ProductivityGainsAgent(BaseAgent):
    """
    Analyzes and quantifies productivity improvements from business initiatives.
    Provides comprehensive evaluation of time savings, efficiency gains, quality improvements,
    and their financial impact across business functions.
    """

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Set up comprehensive validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['productivity_categories', 'baseline_metrics', 'affected_employees'],
                'field_types': {
                    'productivity_categories': 'array',
                    'baseline_metrics': 'object',
                    'affected_employees': 'number',
                    'average_hourly_rate': 'number',
                    'annual_hours_per_employee': 'number',
                    'improvement_timeline': 'string',
                    'current_processes': 'array',
                    'target_improvements': 'object',
                    'quality_metrics': 'object',
                    'implementation_costs': 'object',
                    'risk_factors': 'array'
                },
                'field_constraints': {
                    'affected_employees': {'min': 1},
                    'average_hourly_rate': {'min': 10, 'max': 500},
                    'annual_hours_per_employee': {'min': 1000, 'max': 3000},
                    'improvement_timeline': {'allowed_values': ['immediate', 'short_term', 'medium_term', 'long_term']}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Productivity improvement templates with industry benchmarks
        self.productivity_templates = {
            ProductivityCategory.AUTOMATION: {
                'description': 'Automate repetitive tasks and manual processes',
                'typical_time_savings_percent': 60,
                'typical_error_reduction_percent': 85,
                'implementation_complexity': 'high',
                'ramp_up_period_months': 6,
                'sustainability_factor': 0.95,  # Long-term retention of gains
                'quality_impact_score': 8,
                'employee_satisfaction_impact': 7
            },
            ProductivityCategory.PROCESS_IMPROVEMENT: {
                'description': 'Streamline workflows and eliminate inefficiencies',
                'typical_time_savings_percent': 30,
                'typical_error_reduction_percent': 40,
                'implementation_complexity': 'medium',
                'ramp_up_period_months': 3,
                'sustainability_factor': 0.85,
                'quality_impact_score': 7,
                'employee_satisfaction_impact': 6
            },
            ProductivityCategory.TECHNOLOGY_UPGRADE: {
                'description': 'Upgrade technology infrastructure and tools',
                'typical_time_savings_percent': 45,
                'typical_error_reduction_percent': 50,
                'implementation_complexity': 'high',
                'ramp_up_period_months': 8,
                'sustainability_factor': 0.90,
                'quality_impact_score': 8,
                'employee_satisfaction_impact': 8
            },
            ProductivityCategory.TRAINING_DEVELOPMENT: {
                'description': 'Improve employee skills and capabilities',
                'typical_time_savings_percent': 25,
                'typical_error_reduction_percent': 35,
                'implementation_complexity': 'medium',
                'ramp_up_period_months': 6,
                'sustainability_factor': 0.75,
                'quality_impact_score': 6,
                'employee_satisfaction_impact': 9
            },
            ProductivityCategory.COLLABORATION_TOOLS: {
                'description': 'Implement better collaboration and communication tools',
                'typical_time_savings_percent': 20,
                'typical_error_reduction_percent': 30,
                'implementation_complexity': 'low',
                'ramp_up_period_months': 2,
                'sustainability_factor': 0.80,
                'quality_impact_score': 6,
                'employee_satisfaction_impact': 8
            },
            ProductivityCategory.WORKFLOW_OPTIMIZATION: {
                'description': 'Optimize workflow sequences and dependencies',
                'typical_time_savings_percent': 35,
                'typical_error_reduction_percent': 25,
                'implementation_complexity': 'medium',
                'ramp_up_period_months': 4,
                'sustainability_factor': 0.85,
                'quality_impact_score': 7,
                'employee_satisfaction_impact': 6
            },
            ProductivityCategory.QUALITY_IMPROVEMENT: {
                'description': 'Reduce rework and improve first-time quality',
                'typical_time_savings_percent': 40,
                'typical_error_reduction_percent': 70,
                'implementation_complexity': 'medium',
                'ramp_up_period_months': 5,
                'sustainability_factor': 0.90,
                'quality_impact_score': 9,
                'employee_satisfaction_impact': 7
            },
            ProductivityCategory.KNOWLEDGE_MANAGEMENT: {
                'description': 'Improve access to information and knowledge sharing',
                'typical_time_savings_percent': 15,
                'typical_error_reduction_percent': 20,
                'implementation_complexity': 'low',
                'ramp_up_period_months': 3,
                'sustainability_factor': 0.70,
                'quality_impact_score': 5,
                'employee_satisfaction_impact': 6
            },
            ProductivityCategory.DECISION_SUPPORT: {
                'description': 'Provide better data and analytics for decision making',
                'typical_time_savings_percent': 25,
                'typical_error_reduction_percent': 45,
                'implementation_complexity': 'high',
                'ramp_up_period_months': 7,
                'sustainability_factor': 0.85,
                'quality_impact_score': 8,
                'employee_satisfaction_impact': 7
            },
            ProductivityCategory.COMMUNICATION_EFFICIENCY: {
                'description': 'Improve communication effectiveness and reduce overhead',
                'typical_time_savings_percent': 18,
                'typical_error_reduction_percent': 25,
                'implementation_complexity': 'low',
                'ramp_up_period_months': 2,
                'sustainability_factor': 0.75,
                'quality_impact_score': 5,
                'employee_satisfaction_impact': 7
            }
        }

    async def _analyze_productivity_improvements(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze and quantify productivity improvement opportunities."""
        categories = inputs.get('productivity_categories', [])
        baseline_metrics = inputs.get('baseline_metrics', {})
        affected_employees = inputs.get('affected_employees', 1)
        hourly_rate = inputs.get('average_hourly_rate', 50)
        annual_hours = inputs.get('annual_hours_per_employee', 2000)
        target_improvements = inputs.get('target_improvements', {})
        
        improvements = []
        
        for category in categories:
            if category not in [c.value for c in ProductivityCategory]:
                logger.warning(f"Unknown productivity category: {category}")
                continue
            
            category_enum = ProductivityCategory(category)
            template = self.productivity_templates.get(category_enum, {})
            
            # Get baseline metrics for this category
            baseline_time_hours = baseline_metrics.get(f"{category}_time_hours_per_week", 10)
            baseline_error_rate = baseline_metrics.get(f"{category}_error_rate_percent", 5)
            baseline_quality_score = baseline_metrics.get(f"{category}_quality_score", 7)
            
            # Calculate potential improvements
            time_savings_pct = target_improvements.get(f"{category}_time_savings", 
                                                     template.get('typical_time_savings_percent', 20))
            error_reduction_pct = target_improvements.get(f"{category}_error_reduction", 
                                                        template.get('typical_error_reduction_percent', 30))
            
            # Calculate time savings value
            weekly_time_saved_hours = baseline_time_hours * (time_savings_pct / 100)
            annual_time_saved_hours = weekly_time_saved_hours * 52
            annual_time_savings_value = annual_time_saved_hours * hourly_rate * affected_employees
            
            # Calculate error reduction value
            error_cost_per_incident = baseline_metrics.get(f"{category}_error_cost", hourly_rate * 2)
            current_errors_per_week = baseline_time_hours * (baseline_error_rate / 100)
            errors_prevented_per_week = current_errors_per_week * (error_reduction_pct / 100)
            annual_error_reduction_value = errors_prevented_per_week * 52 * error_cost_per_incident * affected_employees
            
            # Calculate quality improvement value (customer satisfaction, rework reduction)
            quality_improvement_factor = template.get('quality_impact_score', 5) / 10
            quality_value_multiplier = 1 + (quality_improvement_factor * 0.2)  # Up to 20% additional value
            
            # Total annual productivity value
            base_productivity_value = annual_time_savings_value + annual_error_reduction_value
            total_productivity_value = base_productivity_value * quality_value_multiplier
            
            # Calculate implementation metrics
            ramp_up_months = template.get('ramp_up_period_months', 6)
            sustainability_factor = template.get('sustainability_factor', 0.85)
            
            # First year value (considering ramp-up)
            ramp_up_factor = max(0.3, 1 - (ramp_up_months / 12))  # Minimum 30% value in first year
            first_year_value = total_productivity_value * ramp_up_factor
            
            # Long-term sustainable value
            sustainable_annual_value = total_productivity_value * sustainability_factor
            
            # Calculate productivity per employee metrics
            productivity_per_employee = total_productivity_value / affected_employees if affected_employees > 0 else 0
            time_saved_per_employee_hours = annual_time_saved_hours
            
            improvement = {
                'category': category,
                'description': template.get('description', f'Productivity improvement in {category}'),
                'affected_employees': affected_employees,
                'baseline_metrics': {
                    'weekly_time_hours': baseline_time_hours,
                    'error_rate_percent': baseline_error_rate,
                    'quality_score': baseline_quality_score
                },
                'projected_improvements': {
                    'time_savings_percent': time_savings_pct,
                    'error_reduction_percent': error_reduction_pct,
                    'weekly_time_saved_hours': round(weekly_time_saved_hours, 2),
                    'annual_time_saved_hours': round(annual_time_saved_hours, 2)
                },
                'financial_impact': {
                    'annual_time_savings_value': round(annual_time_savings_value, 2),
                    'annual_error_reduction_value': round(annual_error_reduction_value, 2),
                    'total_annual_productivity_value': round(total_productivity_value, 2),
                    'first_year_value': round(first_year_value, 2),
                    'sustainable_annual_value': round(sustainable_annual_value, 2),
                    'productivity_per_employee': round(productivity_per_employee, 2)
                },
                'implementation': {
                    'complexity': template.get('implementation_complexity', 'medium'),
                    'ramp_up_period_months': ramp_up_months,
                    'sustainability_factor': sustainability_factor
                },
                'quality_metrics': {
                    'quality_impact_score': template.get('quality_impact_score', 5),
                    'employee_satisfaction_impact': template.get('employee_satisfaction_impact', 6),
                    'quality_value_multiplier': round(quality_value_multiplier, 3)
                },
                'confidence_level': self._calculate_confidence_level(baseline_metrics, category, template)
            }
            
            improvements.append(improvement)
        
        # Sort by total annual productivity value
        improvements.sort(key=lambda x: x['financial_impact']['total_annual_productivity_value'], reverse=True)
        
        return improvements

    def _calculate_confidence_level(self, baseline_metrics: Dict[str, Any], category: str, template: Dict[str, Any]) -> str:
        """Calculate confidence level for productivity projections."""
        confidence_score = 0
        
        # Data quality assessment
        category_metrics = [k for k in baseline_metrics.keys() if category in k]
        if len(category_metrics) >= 3:  # Good baseline data
            confidence_score += 30
        elif len(category_metrics) >= 1:
            confidence_score += 20
        else:
            confidence_score += 10
        
        # Implementation complexity (lower complexity = higher confidence)
        complexity = template.get('implementation_complexity', 'medium')
        if complexity == 'low':
            confidence_score += 40
        elif complexity == 'medium':
            confidence_score += 30
        else:
            confidence_score += 20
        
        # Historical success factors
        sustainability = template.get('sustainability_factor', 0.85)
        if sustainability >= 0.9:
            confidence_score += 30
        elif sustainability >= 0.8:
            confidence_score += 25
        else:
            confidence_score += 15
        
        if confidence_score >= 80:
            return 'high'
        elif confidence_score >= 60:
            return 'medium'
        else:
            return 'low'

    def _generate_implementation_plan(self, improvements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate implementation plan for productivity improvements."""
        # Categorize by implementation complexity and timeline
        quick_wins = []
        strategic_initiatives = []
        long_term_projects = []
        
        for improvement in improvements:
            complexity = improvement['implementation']['complexity']
            ramp_up_months = improvement['implementation']['ramp_up_period_months']
            annual_value = improvement['financial_impact']['total_annual_productivity_value']
            
            # Prioritize based on value, complexity, and timeline
            if complexity == 'low' and ramp_up_months <= 3:
                quick_wins.append(improvement)
            elif complexity in ['low', 'medium'] and ramp_up_months <= 6:
                strategic_initiatives.append(improvement)
            else:
                long_term_projects.append(improvement)
        
        # Calculate aggregate metrics
        total_annual_value = sum(imp['financial_impact']['total_annual_productivity_value'] for imp in improvements)
        total_first_year_value = sum(imp['financial_impact']['first_year_value'] for imp in improvements)
        total_employees_affected = sum(imp['affected_employees'] for imp in improvements)
        
        # Calculate productivity metrics
        avg_productivity_per_employee = total_annual_value / total_employees_affected if total_employees_affected > 0 else 0
        total_time_saved_hours = sum(imp['projected_improvements']['annual_time_saved_hours'] * imp['affected_employees'] 
                                   for imp in improvements)
        
        implementation_plan = {
            'quick_wins': quick_wins[:3],  # Top 3 quick wins
            'strategic_initiatives': strategic_initiatives[:4],  # Top 4 strategic
            'long_term_projects': long_term_projects[:2],  # Top 2 long-term
            'aggregate_metrics': {
                'total_opportunities': len(improvements),
                'total_annual_productivity_value': round(total_annual_value, 2),
                'total_first_year_value': round(total_first_year_value, 2),
                'total_employees_affected': total_employees_affected,
                'average_productivity_per_employee': round(avg_productivity_per_employee, 2),
                'total_annual_time_saved_hours': round(total_time_saved_hours, 2),
                'equivalent_full_time_positions': round(total_time_saved_hours / 2000, 1)  # Assuming 2000 hours/year
            },
            'implementation_sequence': {
                'phase_1_immediate': [imp['category'] for imp in quick_wins],
                'phase_2_strategic': [imp['category'] for imp in strategic_initiatives[:2]],
                'phase_3_long_term': [imp['category'] for imp in long_term_projects[:1]]
            }
        }
        
        return implementation_plan

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Analyze and quantify productivity improvements from business initiatives.

        Args:
            inputs: Dictionary containing:
                - productivity_categories: List of productivity categories to analyze
                - baseline_metrics: Current performance metrics for each category
                - affected_employees: Number of employees affected by improvements
                - average_hourly_rate: Average hourly rate for cost calculations
                - annual_hours_per_employee: Annual working hours per employee
                - improvement_timeline: Timeline for implementing improvements
                - current_processes: List of current business processes
                - target_improvements: Target improvement percentages by category
                - quality_metrics: Current quality and satisfaction metrics
                - implementation_costs: Associated implementation costs
                - risk_factors: List of implementation risk factors

        Returns:
            AgentResult with detailed productivity analysis and implementation plan
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
            # Analyze productivity improvements
            improvements = await self._analyze_productivity_improvements(inputs)
            
            if not improvements:
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={
                        "message": "No productivity improvement opportunities identified",
                        "improvements": [],
                        "total_productivity_value": 0
                    },
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Generate implementation plan
            implementation_plan = self._generate_implementation_plan(improvements)
            
            # Calculate ROI metrics
            total_productivity_value = implementation_plan['aggregate_metrics']['total_annual_productivity_value']
            implementation_costs = inputs.get('implementation_costs', {})
            total_implementation_cost = sum(implementation_costs.values()) if implementation_costs else total_productivity_value * 0.2
            
            roi_1_year = ((implementation_plan['aggregate_metrics']['total_first_year_value'] - total_implementation_cost) / 
                         total_implementation_cost * 100) if total_implementation_cost > 0 else 0
            payback_months = (total_implementation_cost / (total_productivity_value / 12)) if total_productivity_value > 0 else 0
            
            # Prepare result data
            result_data = {
                'productivity_analysis': {
                    'improvements_identified': len(improvements),
                    'total_annual_productivity_value': round(total_productivity_value, 2),
                    'total_first_year_value': round(implementation_plan['aggregate_metrics']['total_first_year_value'], 2),
                    'employees_affected': implementation_plan['aggregate_metrics']['total_employees_affected'],
                    'productivity_per_employee': round(implementation_plan['aggregate_metrics']['average_productivity_per_employee'], 2),
                    'total_time_saved_hours': round(implementation_plan['aggregate_metrics']['total_annual_time_saved_hours'], 2),
                    'equivalent_fte_capacity': round(implementation_plan['aggregate_metrics']['equivalent_full_time_positions'], 1)
                },
                'improvements': improvements,
                'implementation_plan': implementation_plan,
                'roi_analysis': {
                    'total_implementation_cost': round(total_implementation_cost, 2),
                    'roi_first_year_percent': round(roi_1_year, 1),
                    'payback_period_months': round(payback_months, 1),
                    'net_present_value_3_year': round((total_productivity_value * 2.7 - total_implementation_cost), 2)  # Discounted 3-year NPV
                },
                'recommendations': {
                    'immediate_focus': implementation_plan['implementation_sequence']['phase_1_immediate'],
                    'priority_categories': [imp['category'] for imp in improvements[:3]],
                    'success_factors': [
                        'Establish clear baseline metrics before implementation',
                        'Provide adequate training and change management support',
                        'Monitor progress with regular performance reviews',
                        'Address employee concerns and resistance proactively',
                        'Implement feedback loops for continuous improvement'
                    ]
                },
                'input_summary': {
                    'categories_analyzed': inputs.get('productivity_categories', []),
                    'employees_affected': inputs.get('affected_employees', 1),
                    'timeline': inputs.get('improvement_timeline', 'medium_term')
                }
            }
            
            # Store analysis in MCP memory for workflow coordination
            project_id = inputs.get('project_id', 'unknown')
            await self.mcp_client.store_memory(
                "episodic",
                f"productivity_analysis_{project_id}",
                {
                    "total_productivity_value": total_productivity_value,
                    "employees_affected": implementation_plan['aggregate_metrics']['total_employees_affected'],
                    "time_saved_hours": implementation_plan['aggregate_metrics']['total_annual_time_saved_hours'],
                    "top_categories": [imp['category'] for imp in improvements[:3]],
                    "roi_first_year": roi_1_year
                },
                ["productivity_gains", "efficiency_analysis", f"project_{project_id}"]
            )
            
            logger.info(f"Productivity analysis completed: {len(improvements)} improvements identified, ${total_productivity_value:,.0f} annual value, {implementation_plan['aggregate_metrics']['equivalent_full_time_positions']} FTE equivalent")
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Productivity analysis failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Productivity analysis failed: {str(e)}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
