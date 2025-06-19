import os
import sys
import yaml
import asyncio
import importlib
import logging
from typing import Dict, Any, List
from functools import reduce
from memory.core import MemoryManager
from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

# --- Context Management Utilities ---
def _get_from_context(context: Dict[str, Any], path: str):
    """Access a nested dictionary value using dot notation."""
    try:
        return reduce(lambda d, key: d[key], path.split('.'), context)
    except (KeyError, TypeError):
        logger.warning(f"Could not resolve path '{path}' in context.")
        return None

def _set_in_context(context: Dict[str, Any], path: str, value: Any):
    """Set a nested dictionary value using dot notation."""
    keys = path.split('.')
    d = context
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value

# --- Dynamic Agent Loading ---
def load_agent_class(agent_name: str):
    """Dynamically import an agent class from its module."""
    try:
        module_path = f"agents.{agent_name}.main"
        class_name = "".join(word.capitalize() for word in agent_name.split('_')) + "Agent"
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to load agent '{agent_name}': {e}")
        raise

# --- Orchestrator Class ---
class Orchestrator:
    def __init__(self, workflow_path: str):
        self.workflow = self._load_yaml(workflow_path)
        
        # Initialize and inject the MemoryManager
        self.memory_manager = MemoryManager()
        self.memory_manager.initialize()
        logger.info("MemoryManager initialized successfully in Orchestrator.")
        
        self.mcp_client = MCPClient(self.memory_manager)
        logger.info("MCPClient initialized with MemoryManager.")
        
        self.context = {}

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    async def run_workflow(self, initial_context: Dict[str, Any] = None):
        """Execute the entire workflow defined in the YAML file."""
        self.context = initial_context or {}
        logger.info(f"Starting workflow: {self.workflow.get('name', 'Untitled')}")
        for stage_config in self.workflow.get('stages', []):
            success = await self.run_stage(stage_config)
            if not success:
                logger.error(f"Workflow aborted due to failure in stage: {stage_config.get('name')}")
                return self.context
        logger.info("Workflow completed successfully.")
        return self.context

    async def run_stage(self, stage_config: Dict[str, Any]) -> bool:
        """Execute a single stage of the workflow."""
        stage_name = stage_config.get('name', 'Unnamed Stage')
        logger.info(f"=== Running Stage: {stage_name} ===")
        try:
            agent_configs = stage_config.get('agents', [])
            if stage_config.get('execution_mode') == 'parallel':
                results = await asyncio.gather(*[self.run_agent_wrapper(agent_config) for agent_config in agent_configs])
                if not all(results):
                    raise Exception("A parallel agent failed.")
            else:
                for agent_config in agent_configs:
                    if not await self.run_agent_wrapper(agent_config):
                        raise Exception(f"Agent {agent_config.get('name')} failed.")
            return True
        except Exception as e:
            logger.error(f"Stage '{stage_name}' failed: {e}")
            # Handle compensation/failure logic here if needed
            return False

    async def run_agent_wrapper(self, agent_config: Dict[str, Any]) -> bool:
        """A wrapper for agent execution providing retry logic."""
        agent_name = agent_config.get('name')
        retries = agent_config.get('retry', 1)
        for attempt in range(retries):
            try:
                await self.execute_agent(agent_config)
                return True  # Success
            except Exception as e:
                logger.warning(f"Agent '{agent_name}' attempt {attempt + 1}/{retries} failed: {e}")
                if attempt + 1 == retries:
                    logger.error(f"Agent '{agent_name}' failed after all retries.")
                    return False
                await asyncio.sleep(1.5 ** attempt)
        return False

    async def execute_agent(self, agent_config: Dict[str, Any]):
        """Prepare inputs, run a single agent, and map its outputs."""
        agent_name = agent_config['name']
        logger.info(f"--- Executing Agent: {agent_name} ---")

        # 1. Prepare inputs using explicit mapping
        inputs = {}
        for target_key, context_path in agent_config.get('inputs', {}).items():
            inputs[target_key] = _get_from_context(self.context, context_path)

        # 2. Instantiate and run the agent
        agent_class = load_agent_class(agent_name)
        agent = agent_class(agent_id=agent_name, mcp_client=self.mcp_client, config={})
        result = await agent.execute(inputs)

        if result.status != AgentStatus.COMPLETED:
            raise Exception(f"Agent returned status: {result.status}. Error: {result.data.get('error')}")

        # 3. Map outputs back to the context
        for source_key, context_path in agent_config.get('outputs', {}).items():
            if result.data and source_key in result.data:
                _set_in_context(self.context, context_path, result.data[source_key])
        
        logger.info(f"--- Finished Agent: {agent_name} ---")

if __name__ == '__main__':
    # Example of how to run the orchestrator
    # This requires a workflow YAML file (e.g., workflow.yaml)
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <path_to_workflow_yaml>")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    orchestrator = Orchestrator(workflow_path=workflow_file)

    # Example initial context for a workflow run
    initial_data = {
        "user_query": "Our manufacturing company wants to reduce operational overhead and improve production line efficiency."
    }

    final_context = asyncio.run(orchestrator.run_workflow(initial_context=initial_data))
    print("\n=== WORKFLOW FINISHED ===")
    print("Final Context:", yaml.dump(final_context, indent=2))
