"""
Workflow Coordinator Agent Example

This module demonstrates how to implement a Workflow Coordinator Agent
that orchestrates the business case creation workflow by managing state,
invoking appropriate agents, and maintaining context throughout the process.
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class WorkflowStep(Enum):
    """Enumeration of workflow steps in the business case creation process."""
    TEMPLATE_SELECTION = "template_selection"
    VALUE_DRIVER_SELECTION = "value_driver_selection"
    DATA_INTEGRATION = "data_integration"
    ROI_CALCULATION = "roi_calculation"
    SENSITIVITY_ANALYSIS = "sensitivity_analysis"
    BUSINESS_CASE_COMPOSITION = "business_case_composition"
    NARRATIVE_GENERATION = "narrative_generation"
    REVIEW_AND_FINALIZATION = "review_and_finalization"

class WorkflowCoordinatorAgent(BaseAgent):
    """
    Agent that coordinates the business case creation workflow.
    
    This agent manages the state transitions, agent invocations, and data flow
    throughout the multi-step business case creation process.
    """

    def __init__(self, agent_id: str, mcp_client: Any, config: Dict[str, Any]):
        """
        Initialize the Workflow Coordinator Agent with validation rules.
        
        Args:
            agent_id: Unique identifier for this agent
            mcp_client: MCP client instance for memory access
            config: Configuration dictionary
        """
        # Define validation rules in config
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['workflow_action'],
                'field_types': {
                    'workflow_action': 'string',
                    'workflow_id': 'string',
                    'current_step': 'string',
                    'step_data': 'object',
                    'stakeholder_persona': 'string'
                },
                'field_constraints': {
                    'workflow_action': {
                        'enum': ['start', 'continue', 'complete', 'cancel']
                    }
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Define workflow steps and their dependencies
        self.workflow_steps = {
            WorkflowStep.TEMPLATE_SELECTION: {
                "agent_type": "template_selector",
                "dependencies": [],
                "next_steps": [WorkflowStep.VALUE_DRIVER_SELECTION]
            },
            WorkflowStep.VALUE_DRIVER_SELECTION: {
                "agent_type": "value_driver",
                "dependencies": [WorkflowStep.TEMPLATE_SELECTION],
                "next_steps": [WorkflowStep.DATA_INTEGRATION]
            },
            WorkflowStep.DATA_INTEGRATION: {
                "agent_type": "data_integration",
                "dependencies": [WorkflowStep.VALUE_DRIVER_SELECTION],
                "next_steps": [WorkflowStep.ROI_CALCULATION]
            },
            WorkflowStep.ROI_CALCULATION: {
                "agent_type": "roi_calculator",
                "dependencies": [WorkflowStep.DATA_INTEGRATION],
                "next_steps": [WorkflowStep.SENSITIVITY_ANALYSIS]
            },
            WorkflowStep.SENSITIVITY_ANALYSIS: {
                "agent_type": "sensitivity_analysis",
                "dependencies": [WorkflowStep.ROI_CALCULATION],
                "next_steps": [WorkflowStep.BUSINESS_CASE_COMPOSITION]
            },
            WorkflowStep.BUSINESS_CASE_COMPOSITION: {
                "agent_type": "business_case_composer",
                "dependencies": [WorkflowStep.SENSITIVITY_ANALYSIS],
                "next_steps": [WorkflowStep.NARRATIVE_GENERATION]
            },
            WorkflowStep.NARRATIVE_GENERATION: {
                "agent_type": "narrative_generator",
                "dependencies": [WorkflowStep.BUSINESS_CASE_COMPOSITION],
                "next_steps": [WorkflowStep.REVIEW_AND_FINALIZATION]
            },
            WorkflowStep.REVIEW_AND_FINALIZATION: {
                "agent_type": "review_coordinator",
                "dependencies": [WorkflowStep.NARRATIVE_GENERATION],
                "next_steps": []
            }
        }
    
    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Perform workflow coordinator-specific validations.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            List[str]: List of error messages (empty if all validations pass)
        """
        errors = []
        
        workflow_action = inputs.get('workflow_action', '')
        
        # For continue action, workflow_id and current_step are required
        if workflow_action == 'continue':
            if not inputs.get('workflow_id'):
                errors.append("workflow_id is required for 'continue' action")
            if not inputs.get('current_step'):
                errors.append("current_step is required for 'continue' action")
            elif inputs.get('current_step') not in [step.value for step in WorkflowStep]:
                errors.append(f"Invalid current_step: {inputs.get('current_step')}")
        
        return errors
    
    async def _create_workflow_state(self, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create initial workflow state.
        
        Args:
            initial_data: Initial workflow data
            
        Returns:
            Dictionary containing workflow state
        """
        workflow_id = f"wf_{int(time.time())}"
        
        workflow_state = {
            "workflow_id": workflow_id,
            "status": "active",
            "current_step": WorkflowStep.TEMPLATE_SELECTION.value,
            "completed_steps": [],
            "step_results": {},
            "context": initial_data,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        
        # Store in MCP (simulated)
        logger.info(f"Created workflow state: {workflow_id}")
        
        return workflow_state
    
    async def _load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Load workflow state from MCP.
        
        Args:
            workflow_id: ID of the workflow to load
            
        Returns:
            Dictionary containing workflow state or None if not found
        """
        # In a real implementation, this would load from MCP
        # For this example, we'll return a sample state
        logger.info(f"Loading workflow state: {workflow_id}")
        
        return {
            "workflow_id": workflow_id,
            "status": "active",
            "current_step": WorkflowStep.VALUE_DRIVER_SELECTION.value,
            "completed_steps": [WorkflowStep.TEMPLATE_SELECTION.value],
            "step_results": {
                "template_selection": {
                    "selected_template": "tech_roi_001",
                    "industry": "technology",
                    "company_size": "medium"
                }
            },
            "context": {
                "project_name": "AI Customer Service",
                "client_name": "TechCorp",
                "stakeholder_persona": "executive"
            },
            "created_at": time.time() - 1800,  # 30 minutes ago
            "updated_at": time.time() - 300    # 5 minutes ago
        }
    
    async def _execute_workflow_step(self, step: WorkflowStep, 
                                   workflow_state: Dict[str, Any],
                                   step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific workflow step.
        
        Args:
            step: Workflow step to execute
            workflow_state: Current workflow state
            step_data: Data for the step execution
            
        Returns:
            Dictionary containing step execution result
        """
        step_config = self.workflow_steps[step]
        agent_type = step_config["agent_type"]
        
        logger.info(f"Executing workflow step: {step.value} using {agent_type}")
        
        # Prepare agent inputs based on step type and workflow context
        agent_inputs = {**workflow_state["context"], **step_data}
        
        # Simulate agent execution based on step type
        if step == WorkflowStep.TEMPLATE_SELECTION:
            result = {
                "selected_template": "tech_roi_001",
                "industry": agent_inputs.get("industry", "technology"),
                "company_size": agent_inputs.get("company_size", "medium")
            }
        elif step == WorkflowStep.VALUE_DRIVER_SELECTION:
            result = {
                "selected_drivers": ["cost_reduction", "productivity_gains"],
                "driver_metrics": {
                    "cost_reduction": ["operational_cost", "maintenance_cost"],
                    "productivity_gains": ["process_time", "employee_efficiency"]
                }
            }
        elif step == WorkflowStep.DATA_INTEGRATION:
            result = {
                "data_sources": ["crm", "erp"],
                "metrics_retrieved": {
                    "operational_cost": 2000000,
                    "process_time": 45,
                    "employee_count": 120
                }
            }
        elif step == WorkflowStep.ROI_CALCULATION:
            result = {
                "annual_roi": 125.0,
                "payback_period": 9.6,
                "total_benefit": 1250000,
                "investment_amount": 1000000
            }
        elif step == WorkflowStep.SENSITIVITY_ANALYSIS:
            result = {
                "best_case_roi": 150.0,
                "worst_case_roi": 100.0,
                "most_likely_roi": 125.0,
                "key_variables": ["adoption_rate", "cost_savings"]
            }
        elif step == WorkflowStep.BUSINESS_CASE_COMPOSITION:
            result = {
                "business_case_id": f"bc_{int(time.time())}",
                "sections_created": 7,
                "total_pages": 15
            }
        elif step == WorkflowStep.NARRATIVE_GENERATION:
            result = {
                "narratives_generated": 7,
                "total_word_count": 3500,
                "stakeholder_persona": agent_inputs.get("stakeholder_persona", "executive")
            }
        else:
            result = {"status": "completed"}
        
        # Simulate execution time
        await asyncio.sleep(1)
        
        return {
            "status": "completed",
            "result": result,
            "execution_time": 1000,  # ms
            "timestamp": time.time()
        }
    
    async def _update_workflow_state(self, workflow_state: Dict[str, Any],
                                   completed_step: WorkflowStep,
                                   step_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update workflow state after step completion.
        
        Args:
            workflow_state: Current workflow state
            completed_step: Step that was completed
            step_result: Result of the completed step
            
        Returns:
            Updated workflow state
        """
        # Add completed step to the list
        workflow_state["completed_steps"].append(completed_step.value)
        workflow_state["step_results"][completed_step.value] = step_result
        workflow_state["updated_at"] = time.time()
        
        # Determine next step
        next_steps = self.workflow_steps[completed_step]["next_steps"]
        if next_steps:
            workflow_state["current_step"] = next_steps[0].value
        else:
            workflow_state["status"] = "completed"
            workflow_state["current_step"] = None
        
        # Store updated state in MCP (simulated)
        logger.info(f"Updated workflow state: {workflow_state['workflow_id']}")
        
        return workflow_state
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute the workflow coordination logic after validation.
        
        Args:
            inputs: Dictionary of validated input values
            
        Returns:
            AgentResult: Result of the workflow coordination
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
        
        workflow_action = inputs['workflow_action']
        
        try:
            if workflow_action == 'start':
                # Create new workflow
                initial_data = inputs.get('step_data', {})
                workflow_state = await self._create_workflow_state(initial_data)
                
                result_data = {
                    "workflow_id": workflow_state["workflow_id"],
                    "status": workflow_state["status"],
                    "current_step": workflow_state["current_step"],
                    "next_action": "Execute template selection step"
                }
                
            elif workflow_action == 'continue':
                # Load existing workflow and execute next step
                workflow_id = inputs['workflow_id']
                workflow_state = await self._load_workflow_state(workflow_id)
                
                if not workflow_state:
                    return AgentResult(
                        status=AgentStatus.FAILED,
                        data={"error": f"Workflow not found: {workflow_id}"},
                        execution_time_ms=int((time.monotonic() - start_time) * 1000)
                    )
                
                current_step = WorkflowStep(workflow_state["current_step"])
                step_data = inputs.get('step_data', {})
                
                # Execute the current step
                step_result = await self._execute_workflow_step(current_step, workflow_state, step_data)
                
                # Update workflow state
                workflow_state = await self._update_workflow_state(workflow_state, current_step, step_result)
                
                result_data = {
                    "workflow_id": workflow_state["workflow_id"],
                    "status": workflow_state["status"],
                    "completed_step": current_step.value,
                    "current_step": workflow_state["current_step"],
                    "step_result": step_result["result"]
                }
                
            elif workflow_action == 'complete':
                workflow_id = inputs.get('workflow_id')
                if workflow_id:
                    # Mark workflow as completed
                    logger.info(f"Completing workflow: {workflow_id}")
                
                result_data = {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "message": "Workflow completed successfully"
                }
                
            elif workflow_action == 'cancel':
                workflow_id = inputs.get('workflow_id')
                if workflow_id:
                    # Mark workflow as cancelled
                    logger.info(f"Cancelling workflow: {workflow_id}")
                
                result_data = {
                    "workflow_id": workflow_id,
                    "status": "cancelled",
                    "message": "Workflow cancelled by user"
                }
            
            else:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Unknown workflow action: {workflow_action}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Log success
            logger.info(f"Successfully executed workflow action: {workflow_action}")
            
            # Return successful result
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data,
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
            
        except Exception as e:
            logger.error(f"Error in workflow coordination: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Workflow coordination failed: {str(e)}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
