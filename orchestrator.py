import os
import sys
import yaml
import asyncio
import importlib
import logging
from typing import Dict, Any, List
from src.agents.core.agent_base import MCPClient

# Distributed tracing (OpenTelemetry)
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Prometheus metrics
from prometheus_client import start_http_server, Counter, Histogram

# Notification stub
import threading

def notify(event: str, context: Dict[str, Any]):
    # Stub: Replace with Slack/email integration as needed
    logging.warning(f"[NOTIFY] {event}: {context}")

# Setup tracing
resource = Resource(attributes={SERVICE_NAME: "b2bvalue-orchestrator"})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)
jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
tracer = trace.get_tracer(__name__)

# Setup Prometheus metrics
AGENT_EXECUTIONS = Counter('agent_executions_total', 'Total agent executions', ['agent'])
AGENT_FAILURES = Counter('agent_failures_total', 'Total agent failures', ['agent'])
AGENT_COMPENSATIONS = Counter('agent_compensations_total', 'Total agent compensations', ['agent'])
STAGE_DURATION = Histogram('stage_duration_seconds', 'Stage execution duration', ['stage'])

# Start Prometheus metrics server (in background)
def start_metrics_server():
    start_http_server(8000)
threading.Thread(target=start_metrics_server, daemon=True).start()

# Set up logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('logs/orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("orchestrator")

# Utility to dynamically import agent classes
def load_agent_class(agent_name: str):
    module_path = f"src.agents.{agent_name}.main"
    class_name = "".join(word.capitalize() for word in agent_name.split("_")) + "Agent"
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

class Orchestrator:
    def __init__(self, workflow_yaml: str, agent_yaml_dir: str):
        self.workflow = self._load_yaml(workflow_yaml)
        self.agent_yaml_dir = agent_yaml_dir
        self.mcp_client = MCPClient()  # Replace with real MCP client
        self.context = {}  # Shared context for all agents

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"YAML file not found: {path}")
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    async def run_stage(self, stage: Dict[str, Any]):
        agents = stage.get('agents', [])
        execution_mode = stage.get('execution_mode', 'sequential')
        retries = stage.get('retry_policy', {}).get('max_attempts', 1)
        backoff = stage.get('retry_policy', {}).get('backoff_factor', 1.5)
        compensation_action = stage.get('compensation_action')
        stage_name = stage.get('name', stage.get('id'))
        logger.info(f"=== Running stage: {stage_name} ===")
        with tracer.start_as_current_span(f"stage:{stage_name}") as stage_span, STAGE_DURATION.labels(stage=stage_name).time():
            try:
                if execution_mode == 'parallel':
                    await asyncio.gather(*[self.run_agent(agent_name, retries, backoff, compensation_action, stage_name) for agent_name in agents])
                else:  # default to sequential
                    for agent_name in agents:
                        await self.run_agent(agent_name, retries, backoff, compensation_action, stage_name)
            except Exception as e:
                logger.error(f"Stage failed: {e}")
                notify("stage_failure", {"stage": stage_name, "error": str(e)})
                if compensation_action:
                    logger.info(f"Running compensation action for stage: {compensation_action}")
                    await self.run_compensation_action(compensation_action, stage_name)

    async def run_agent(self, agent_name: str, retries: int, backoff: float, compensation_action: str = None, stage_name: str = ""):
        logger.info(f"--- Running agent: {agent_name}")
        with tracer.start_as_current_span(f"agent:{agent_name}") as agent_span:
            agent_class = load_agent_class(agent_name)
            agent_yaml = os.path.join(self.agent_yaml_dir, f"{agent_name}_agent.yaml")
            config = {}  # Extend as needed
            agent = agent_class(agent_yaml, self.mcp_client, config)
            attempt = 0
            while attempt < retries:
                try:
                    result = await agent.execute_with_resilience(self.context)
                    logger.info(f"Result from {agent_name}: {result}")
                    AGENT_EXECUTIONS.labels(agent=agent_name).inc()
                    # Update shared context with agent output
                    if hasattr(result, 'data') and isinstance(result.data, dict):
                        self.context.update(result.data)
                    return  # Success, exit retry loop
                except Exception as e:
                    attempt += 1
                    logger.error(f"Error in agent {agent_name}, attempt {attempt}/{retries}: {e}")
                    if attempt < retries:
                        await asyncio.sleep(backoff ** attempt)
                    else:
                        logger.error(f"Agent {agent_name} failed after {retries} attempts.")
                        AGENT_FAILURES.labels(agent=agent_name).inc()
                        notify("agent_failure", {"agent": agent_name, "stage": stage_name, "error": str(e)})
                        if compensation_action:
                            logger.info(f"Running compensation action for agent: {compensation_action}")
                            await self.run_compensation_action(compensation_action, stage_name)

    async def run_compensation_action(self, compensation_action: str, stage_name: str = ""):
        logger.warning(f"Compensation action triggered: {compensation_action}")
        AGENT_COMPENSATIONS.labels(agent=compensation_action).inc()
        notify("compensation_action", {"agent": compensation_action, "stage": stage_name})
        # Example: if compensation_action is an agent name, try running it
        try:
            agent_class = load_agent_class(compensation_action)
            agent_yaml = os.path.join(self.agent_yaml_dir, f"{compensation_action}_agent.yaml")
            config = {}
            agent = agent_class(agent_yaml, self.mcp_client, config)
            result = await agent.execute_with_resilience(self.context)
            logger.info(f"Compensation agent {compensation_action} result: {result}")
        except Exception as e:
            logger.error(f"Compensation action failed: {e}")
            notify("compensation_failure", {"agent": compensation_action, "stage": stage_name, "error": str(e)})

    async def run_workflow(self):
        stages = self.workflow.get('stages', [])
        for stage in stages:
            await self.run_stage(stage)
        print("\n=== Workflow complete ===")
        print("Final context:", self.context)

if __name__ == "__main__":
    workflow_yaml = sys.argv[1] if len(sys.argv) > 1 else "../Agents/global_config.yaml"
    agent_yaml_dir = sys.argv[2] if len(sys.argv) > 2 else "../Agents"
    orchestrator = Orchestrator(workflow_yaml, agent_yaml_dir)
    asyncio.run(orchestrator.run_workflow())
