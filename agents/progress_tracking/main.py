"""
Progress Tracking Agent

This agent monitors and reports on the progress of business case development workflows.
It provides detailed tracking, milestone analysis, bottleneck identification, and operational
visibility for both individual projects and organizational overview.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timedelta

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.types import KnowledgeEntity

logger = logging.getLogger(__name__)

class WorkflowStage(Enum):
    """Comprehensive workflow stages for business case development."""
    PROJECT_INTAKE = "project_intake"
    TEMPLATE_SELECTION = "template_selection"
    VALUE_DRIVER_ANALYSIS = "value_driver_analysis"
    DATA_COLLECTION = "data_collection"
    ROI_CALCULATION = "roi_calculation"
    SENSITIVITY_ANALYSIS = "sensitivity_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    BUSINESS_CASE_COMPOSITION = "business_case_composition"
    NARRATIVE_GENERATION = "narrative_generation"
    STAKEHOLDER_REVIEW = "stakeholder_review"
    FINALIZATION = "finalization"
    COMPLETED = "completed"

class ProgressStatus(Enum):
    """Progress status indicators."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    SKIPPED = "skipped"

class ProgressTrackingAgent(BaseAgent):
    """
    Monitors and reports the progress of business case development workflows.
    Provides comprehensive tracking, bottleneck identification, and operational visibility.
    """

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Set up validation rules for progress tracking
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['action'],
                'field_types': {
                    'action': 'string',
                    'project_id': 'string',
                    'current_stage': 'string',
                    'stage_data': 'object',
                    'user_id': 'string',
                    'organization_filter': 'string',
                    'include_metrics': 'boolean',
                    'time_range': 'string'
                },
                'field_constraints': {
                    'action': {'allowed_values': ['update_progress', 'get_progress', 'get_organizational_overview', 'get_stage_analytics', 'identify_bottlenecks']},
                    'current_stage': {'allowed_values': [stage.value for stage in WorkflowStage]},
                    'time_range': {'allowed_values': ['24h', '7d', '30d', '90d', 'all']}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Define workflow stage dependencies and typical durations
        self.stage_dependencies = {
            WorkflowStage.PROJECT_INTAKE: [],
            WorkflowStage.TEMPLATE_SELECTION: [WorkflowStage.PROJECT_INTAKE],
            WorkflowStage.VALUE_DRIVER_ANALYSIS: [WorkflowStage.TEMPLATE_SELECTION],
            WorkflowStage.DATA_COLLECTION: [WorkflowStage.VALUE_DRIVER_ANALYSIS],
            WorkflowStage.ROI_CALCULATION: [WorkflowStage.DATA_COLLECTION],
            WorkflowStage.SENSITIVITY_ANALYSIS: [WorkflowStage.ROI_CALCULATION],
            WorkflowStage.RISK_ASSESSMENT: [WorkflowStage.SENSITIVITY_ANALYSIS],
            WorkflowStage.BUSINESS_CASE_COMPOSITION: [WorkflowStage.RISK_ASSESSMENT],
            WorkflowStage.NARRATIVE_GENERATION: [WorkflowStage.BUSINESS_CASE_COMPOSITION],
            WorkflowStage.STAKEHOLDER_REVIEW: [WorkflowStage.NARRATIVE_GENERATION],
            WorkflowStage.FINALIZATION: [WorkflowStage.STAKEHOLDER_REVIEW],
            WorkflowStage.COMPLETED: [WorkflowStage.FINALIZATION]
        }
        
        # Typical stage durations in hours (for bottleneck analysis)
        self.typical_stage_durations = {
            WorkflowStage.PROJECT_INTAKE: 2,
            WorkflowStage.TEMPLATE_SELECTION: 1,
            WorkflowStage.VALUE_DRIVER_ANALYSIS: 4,
            WorkflowStage.DATA_COLLECTION: 8,
            WorkflowStage.ROI_CALCULATION: 3,
            WorkflowStage.SENSITIVITY_ANALYSIS: 2,
            WorkflowStage.RISK_ASSESSMENT: 4,
            WorkflowStage.BUSINESS_CASE_COMPOSITION: 6,
            WorkflowStage.NARRATIVE_GENERATION: 3,
            WorkflowStage.STAKEHOLDER_REVIEW: 24,
            WorkflowStage.FINALIZATION: 2,
            WorkflowStage.COMPLETED: 0
        }

    async def _get_project_progress(self, project_id: str) -> Dict[str, Any]:
        """Retrieve current progress for a specific project."""
        try:
            # Get project metadata and workflow state
            project_memories = await self.mcp_client.search_memory(
                "episodic",
                query=f"project_id:{project_id}",
                tags=["workflow_progress", "project_metadata"]
            )
            
            if not project_memories:
                return {
                    'project_id': project_id,
                    'status': 'not_found',
                    'stages': {},
                    'overall_progress': 0
                }
            
            # Organize progress by stages
            stages_progress = {}
            project_data = {}
            
            for memory in project_memories:
                if 'stage_name' in memory:
                    stage_name = memory['stage_name']
                    stages_progress[stage_name] = {
                        'status': memory.get('status', 'not_started'),
                        'start_time': memory.get('start_time'),
                        'end_time': memory.get('end_time'),
                        'duration_hours': memory.get('duration_hours'),
                        'agent_used': memory.get('agent_used'),
                        'data_quality': memory.get('data_quality', 'unknown'),
                        'notes': memory.get('notes', '')
                    }
                elif 'project_name' in memory:
                    project_data = memory
            
            # Calculate overall progress
            total_stages = len(WorkflowStage)
            completed_stages = len([s for s in stages_progress.values() if s['status'] == 'completed'])
            overall_progress = round((completed_stages / total_stages) * 100)
            
            # Identify current stage
            current_stage = 'project_intake'
            for stage in WorkflowStage:
                if stage.value not in stages_progress or stages_progress[stage.value]['status'] != 'completed':
                    current_stage = stage.value
                    break
            
            return {
                'project_id': project_id,
                'project_name': project_data.get('project_name', 'Unknown'),
                'current_stage': current_stage,
                'overall_progress': overall_progress,
                'completed_stages': completed_stages,
                'total_stages': total_stages,
                'stages': stages_progress,
                'project_metadata': project_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get project progress for {project_id}: {str(e)}")
            return {
                'project_id': project_id,
                'status': 'error',
                'error': str(e)
            }

    async def _update_stage_progress(self, project_id: str, stage: str, stage_data: Dict[str, Any]) -> bool:
        """Update progress for a specific workflow stage."""
        try:
            # Validate stage
            if stage not in [s.value for s in WorkflowStage]:
                raise ValueError(f"Invalid stage: {stage}")
            
            # Prepare stage progress data
            progress_data = {
                'project_id': project_id,
                'stage_name': stage,
                'status': stage_data.get('status', 'in_progress'),
                'start_time': stage_data.get('start_time', time.time()),
                'end_time': stage_data.get('end_time'),
                'agent_used': stage_data.get('agent_used', 'unknown'),
                'data_quality': stage_data.get('data_quality', 'good'),
                'notes': stage_data.get('notes', ''),
                'updated_timestamp': time.time()
            }
            
            # Calculate duration if stage is completed
            if progress_data['status'] == 'completed' and progress_data['end_time']:
                duration_seconds = progress_data['end_time'] - progress_data['start_time']
                progress_data['duration_hours'] = round(duration_seconds / 3600, 2)
            
            # Store progress update in memory
            await self.mcp_client.store_memory(
                "episodic",
                f"workflow_progress_{project_id}_{stage}",
                progress_data,
                ["workflow_progress", "stage_tracking", f"project_{project_id}"]
            )
            
            logger.info(f"Updated stage progress: {project_id} - {stage} - {progress_data['status']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update stage progress: {str(e)}")
            return False

    async def _get_organizational_overview(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get organizational overview of all projects and their progress."""
        try:
            # Get all project progress data
            all_progress = await self.mcp_client.search_memory(
                "episodic",
                query="workflow_progress",
                tags=["workflow_progress"]
            )
            
            # Organize by projects
            projects_overview = {}
            stage_statistics = {}
            
            for progress in all_progress:
                project_id = progress.get('project_id')
                if not project_id:
                    continue
                
                if project_id not in projects_overview:
                    projects_overview[project_id] = {
                        'project_id': project_id,
                        'stages': {},
                        'last_activity': 0
                    }
                
                stage_name = progress.get('stage_name')
                if stage_name:
                    projects_overview[project_id]['stages'][stage_name] = progress
                    
                    # Track last activity
                    updated_time = progress.get('updated_timestamp', 0)
                    if updated_time > projects_overview[project_id]['last_activity']:
                        projects_overview[project_id]['last_activity'] = updated_time
                    
                    # Accumulate stage statistics
                    status = progress.get('status', 'unknown')
                    stage_key = f"{stage_name}_{status}"
                    stage_statistics[stage_key] = stage_statistics.get(stage_key, 0) + 1
            
            # Calculate summary metrics
            total_projects = len(projects_overview)
            active_projects = 0
            completed_projects = 0
            stalled_projects = 0
            
            current_time = time.time()
            one_week_ago = current_time - (7 * 24 * 3600)
            
            for project in projects_overview.values():
                completed_stages = len([s for s in project['stages'].values() if s.get('status') == 'completed'])
                total_stages = len(WorkflowStage)
                
                if completed_stages == total_stages:
                    completed_projects += 1
                elif project['last_activity'] > one_week_ago:
                    active_projects += 1
                else:
                    stalled_projects += 1
            
            return {
                'summary': {
                    'total_projects': total_projects,
                    'active_projects': active_projects,
                    'completed_projects': completed_projects,
                    'stalled_projects': stalled_projects,
                    'completion_rate': round((completed_projects / total_projects * 100) if total_projects > 0 else 0, 2)
                },
                'projects': list(projects_overview.values()),
                'stage_statistics': stage_statistics,
                'generated_at': current_time
            }
            
        except Exception as e:
            logger.error(f"Failed to get organizational overview: {str(e)}")
            return {'error': str(e)}

    async def _identify_bottlenecks(self) -> Dict[str, Any]:
        """Identify workflow bottlenecks and performance issues."""
        try:
            # Get all stage progress data
            all_progress = await self.mcp_client.search_memory(
                "episodic",
                query="workflow_progress",
                tags=["workflow_progress"]
            )
            
            # Analyze stage durations and bottlenecks
            stage_analysis = {}
            current_time = time.time()
            
            for progress in all_progress:
                stage_name = progress.get('stage_name')
                status = progress.get('status')
                duration_hours = progress.get('duration_hours', 0)
                start_time = progress.get('start_time', 0)
                
                if not stage_name:
                    continue
                
                if stage_name not in stage_analysis:
                    stage_analysis[stage_name] = {
                        'total_instances': 0,
                        'completed_instances': 0,
                        'in_progress_instances': 0,
                        'blocked_instances': 0,
                        'failed_instances': 0,
                        'total_duration_hours': 0,
                        'durations': [],
                        'stuck_instances': [],
                        'typical_duration': self.typical_stage_durations.get(WorkflowStage(stage_name), 4)
                    }
                
                analysis = stage_analysis[stage_name]
                analysis['total_instances'] += 1
                
                if status == 'completed':
                    analysis['completed_instances'] += 1
                    analysis['total_duration_hours'] += duration_hours
                    analysis['durations'].append(duration_hours)
                elif status == 'in_progress':
                    analysis['in_progress_instances'] += 1
                    # Check if stuck (in progress longer than typical duration)
                    hours_in_progress = (current_time - start_time) / 3600
                    if hours_in_progress > analysis['typical_duration'] * 2:
                        analysis['stuck_instances'].append({
                            'project_id': progress.get('project_id'),
                            'hours_in_progress': round(hours_in_progress, 2),
                            'expected_duration': analysis['typical_duration']
                        })
                elif status == 'blocked':
                    analysis['blocked_instances'] += 1
                elif status == 'failed':
                    analysis['failed_instances'] += 1
            
            # Calculate bottleneck metrics
            bottlenecks = []
            for stage_name, analysis in stage_analysis.items():
                if analysis['completed_instances'] > 0:
                    avg_duration = analysis['total_duration_hours'] / analysis['completed_instances']
                    typical_duration = analysis['typical_duration']
                    
                    bottleneck_score = 0
                    issues = []
                    
                    # Duration-based bottleneck detection
                    if avg_duration > typical_duration * 1.5:
                        bottleneck_score += 3
                        issues.append(f"Average duration ({avg_duration:.1f}h) exceeds typical ({typical_duration}h)")
                    
                    # Failure rate analysis
                    failure_rate = analysis['failed_instances'] / analysis['total_instances']
                    if failure_rate > 0.1:
                        bottleneck_score += 2
                        issues.append(f"High failure rate: {failure_rate:.1%}")
                    
                    # Blocked instances
                    if analysis['blocked_instances'] > 0:
                        bottleneck_score += 1
                        issues.append(f"{analysis['blocked_instances']} blocked instances")
                    
                    # Stuck instances
                    if analysis['stuck_instances']:
                        bottleneck_score += len(analysis['stuck_instances'])
                        issues.append(f"{len(analysis['stuck_instances'])} stuck instances")
                    
                    if bottleneck_score > 0:
                        bottlenecks.append({
                            'stage': stage_name,
                            'bottleneck_score': bottleneck_score,
                            'issues': issues,
                            'analysis': analysis
                        })
            
            # Sort by bottleneck score
            bottlenecks.sort(key=lambda x: x['bottleneck_score'], reverse=True)
            
            return {
                'bottlenecks': bottlenecks[:5],  # Top 5 bottlenecks
                'stage_analysis': stage_analysis,
                'recommendations': self._generate_bottleneck_recommendations(bottlenecks[:3])
            }
            
        except Exception as e:
            logger.error(f"Failed to identify bottlenecks: {str(e)}")
            return {'error': str(e)}

    def _generate_bottleneck_recommendations(self, bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on identified bottlenecks."""
        recommendations = []
        
        for bottleneck in bottlenecks:
            stage = bottleneck['stage']
            issues = bottleneck['issues']
            
            if 'Average duration' in str(issues):
                recommendations.append(f"Optimize {stage} process - consider automation or additional resources")
            
            if 'failure rate' in str(issues):
                recommendations.append(f"Review {stage} validation and error handling procedures")
            
            if 'blocked instances' in str(issues):
                recommendations.append(f"Investigate dependencies and resource availability for {stage}")
            
            if 'stuck instances' in str(issues):
                recommendations.append(f"Implement automated monitoring and escalation for {stage}")
        
        if not recommendations:
            recommendations.append("No significant bottlenecks detected - workflow performance is optimal")
        
        return recommendations

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute progress tracking operations based on the requested action.

        Args:
            inputs: Dictionary containing:
                - action: Type of operation ('update_progress', 'get_progress', 'get_organizational_overview', 'identify_bottlenecks')
                - project_id: Project identifier (for project-specific operations)
                - current_stage: Current workflow stage (for updates)
                - stage_data: Stage-specific data (for updates)
                - Additional parameters based on action type

        Returns:
            AgentResult with progress data, analytics, or operational insights
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
            action = inputs['action']
            result_data = {}
            
            if action == 'update_progress':
                project_id = inputs.get('project_id')
                current_stage = inputs.get('current_stage')
                stage_data = inputs.get('stage_data', {})
                
                if not project_id or not current_stage:
                    raise ValueError("project_id and current_stage required for update_progress")
                
                success = await self._update_stage_progress(project_id, current_stage, stage_data)
                result_data = {
                    'action': 'update_progress',
                    'success': success,
                    'project_id': project_id,
                    'stage': current_stage,
                    'timestamp': time.time()
                }
                
            elif action == 'get_progress':
                project_id = inputs.get('project_id')
                if not project_id:
                    raise ValueError("project_id required for get_progress")
                
                progress_data = await self._get_project_progress(project_id)
                result_data = {
                    'action': 'get_progress',
                    'progress': progress_data
                }
                
            elif action == 'get_organizational_overview':
                filters = {
                    'organization_filter': inputs.get('organization_filter'),
                    'time_range': inputs.get('time_range', '30d'),
                    'include_metrics': inputs.get('include_metrics', True)
                }
                
                overview = await self._get_organizational_overview(filters)
                result_data = {
                    'action': 'get_organizational_overview',
                    'overview': overview,
                    'filters_applied': filters
                }
                
            elif action == 'identify_bottlenecks':
                bottleneck_analysis = await self._identify_bottlenecks()
                result_data = {
                    'action': 'identify_bottlenecks',
                    'analysis': bottleneck_analysis,
                    'generated_at': time.time()
                }
                
            else:
                raise ValueError(f"Unknown action: {action}")
            
            logger.info(f"Progress tracking completed: {action}")
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Progress tracking failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Progress tracking failed: {str(e)}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
