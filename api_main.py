from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from memory.core import MemoryManager
from agents.core.mcp_client import MCPClient
from agents.value_driver.main import ValueDriverAgent
from agents.persona.main import PersonaAgent
from agents.roi_calculator.main import RoiCalculatorAgent
from agents.sensitivity_analysis.main import SensitivityAnalysisAgent
# We might need load_config from orchestrator or a similar utility
# from orchestrator import load_agent_config # Placeholder
import asyncio
import yaml # For loading agent configurations
from agents.core.agent_base import AgentStatus # For checking agent results
import logging # For logging initialization messages

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Basic logging for now

from fastapi import Request # To access app.state
from pydantic import BaseModel
from typing import List, Optional, Any

# --- Pydantic Models for /api/discover-value --- 

class DiscoverValueRequest(BaseModel):
    user_query: str
    # industry: Optional[str] = None # Future extension
    # company_size: Optional[str] = None # Future extension

class Tier3Metric(BaseModel):
    name: str
    type: str
    default_value: Any 
    value: Optional[Any] = None

class Tier2Driver(BaseModel):
    name: str
    description: str
    keywords_found: List[str]
    tier_3_metrics: List[Tier3Metric]

class ValueDriverPillar(BaseModel):
    pillar: str
    tier_2_drivers: List[Tier2Driver]

class Persona(BaseModel):
    name: str
    description: str

class DiscoveryData(BaseModel):
    value_drivers: List[ValueDriverPillar]
    personas: List[Persona]

class ExecutionDetails(BaseModel):
    value_driver_agent_time_ms: Optional[int] = None
    persona_agent_time_ms: Optional[int] = None

class DiscoverValueResponse(BaseModel):
    discovery: DiscoveryData
    execution_details: Optional[ExecutionDetails] = None

# --- End Pydantic Models for /api/discover-value ---


# --- Pydantic Models for /api/quantify-roi ---

class RoiSummary(BaseModel):
    total_annual_value: float
    roi_percentage: float
    payback_period_months: float
    # Add other relevant fields from RoiCalculatorAgent output as needed
    # e.g., detailed_breakdown: Optional[List[Dict[str, Any]]] = None

class SensitivityVariationInput(BaseModel):
    metric_name: str  # Full path to the metric if deeply nested, or unique name
    pillar_name: str # To identify which pillar the metric belongs to
    tier2_driver_name: str # To identify which T2 driver the metric belongs to
    percentage_change: float # e.g., -10.0 for -10%, 15.0 for +15%

class SensitivityScenarioOutput(BaseModel):
    scenario_name: str # e.g., "Hours Saved per Week -10%"
    varied_metric: str
    percentage_change: float
    resulting_roi_percentage: float
    resulting_total_annual_value: float
    # Add other relevant fields from SensitivityAnalysisAgent output

class QuantifyRoiRequest(BaseModel):
    value_drivers: List[ValueDriverPillar] # Tier3Metric.value should be populated by user
    investment_amount: float
    sensitivity_variations: Optional[List[SensitivityVariationInput]] = None

class QuantificationData(BaseModel):
    roi_summary: RoiSummary
    sensitivity_analysis_results: Optional[List[SensitivityScenarioOutput]] = None

class QuantificationExecutionDetails(BaseModel):
    roi_calculator_agent_time_ms: Optional[int] = None
    sensitivity_analysis_agent_time_ms: Optional[int] = None

class QuantifyRoiResponse(BaseModel):
    quantification: QuantificationData
    execution_details: Optional[QuantificationExecutionDetails] = None

# --- End Pydantic Models ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MemoryManager, MCPClient, and Agents
    logger.info("API starting up...")
    app.state.memory_manager = MemoryManager()
    # Initialize memory tiers if they have explicit initialize methods
    # Example: await app.state.memory_manager.working_memory.initialize()
    #          await app.state.memory_manager.episodic_memory.initialize()
    #          await app.state.memory_manager.semantic_memory.initialize()
    #          await app.state.memory_manager.knowledge_graph.initialize()
    # Explicitly initialize memory tiers
    try:
        await app.state.memory_manager.initialize() # Assuming initialize is async
        logger.info("MemoryManager tiers initialized.")
    except AttributeError:
        # Fallback if MemoryManager.initialize is not async or does not exist
        # This might happen if the class structure was changed or if it's not an async method
        try:
            app.state.memory_manager.initialize() # Try synchronous version
            logger.info("MemoryManager tiers initialized (sync).")
        except Exception as e_init:
            logger.error(f"Failed to initialize MemoryManager tiers: {e_init}")
            # Depending on severity, might want to raise an error and stop app startup

    app.state.mcp_client = MCPClient(app.state.memory_manager)
    app.state.mcp_client.setup_default_access_controls()
    logger.info("MemoryManager and MCPClient initialized.")

    # Load agent configurations from workflow.yaml
    workflow_config_path = "workflow.yaml" # Assuming it's in the same directory or accessible path
    agent_configs_from_yaml = {}
    try:
        with open(workflow_config_path, 'r') as f:
            workflow_yaml = yaml.safe_load(f)
        
        for stage in workflow_yaml.get('stages', []):
            for agent_spec in stage.get('agents', []):
                agent_name = agent_spec.get('name')
                if agent_name:
                    # Store the whole agent spec, as 'config' might be one of its keys
                    # or the agent might use other keys like 'inputs' for its setup.
                    agent_configs_from_yaml[agent_name] = agent_spec.get('config', {})
        logger.info(f"Agent configurations loaded from {workflow_config_path}")
    except FileNotFoundError:
        logger.error(f"Workflow configuration file not found: {workflow_config_path}. Agents will use default configs.")
    except Exception as e_yaml:
        logger.error(f"Error loading or parsing {workflow_config_path}: {e_yaml}. Agents will use default configs.")

    # Instantiate ValueDriverAgent
    vd_config = agent_configs_from_yaml.get('value_driver', {})
    app.state.value_driver_agent = ValueDriverAgent(
        agent_id='value_driver_api',
        mcp_client=app.state.mcp_client,
        config=vd_config
    )
    logger.info("ValueDriverAgent initialized.")

    # Instantiate PersonaAgent
    persona_config = agent_configs_from_yaml.get('persona', {})
    app.state.persona_agent = PersonaAgent(
        agent_id='persona_api',
        mcp_client=app.state.mcp_client,
        config=persona_config
    )
    logger.info("PersonaAgent initialized.")

    # Instantiate RoiCalculatorAgent
    roi_config = agent_configs_from_yaml.get('roi_calculator', {})
    app.state.roi_calculator_agent = RoiCalculatorAgent(
        agent_id='roi_calculator_api',
        mcp_client=app.state.mcp_client,
        config=roi_config
    )
    logger.info("RoiCalculatorAgent initialized.")

    # Instantiate SensitivityAnalysisAgent
    sa_config = agent_configs_from_yaml.get('sensitivity_analysis', {})
    app.state.sensitivity_analysis_agent = SensitivityAnalysisAgent(
        agent_id='sensitivity_analysis_api',
        mcp_client=app.state.mcp_client,
        config=sa_config
    )
    logger.info("SensitivityAnalysisAgent initialized.")
    logger.info("All agents initialized.")


    yield
    # Shutdown: Cleanup resources if any
    logger.info("API shutting down...")


app = FastAPI(lifespan=lifespan,
    title="B2BValue API",
    description="API for the B2BValue Interactive Calculator and Proposal Generator.",
    version="0.1.0",
)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the B2BValue API!"}

# Future endpoints will be added here

@app.post("/api/discover-value", response_model=DiscoverValueResponse, tags=["Discovery"])
async def discover_value(fastapi_request: DiscoverValueRequest, request_object: Request): # Renamed 'request' to 'fastapi_request' to avoid conflict with 'request_object' for app.state
    """
    Processes a user query to discover potential value drivers and target personas.
    """
    try:
        value_driver_agent: ValueDriverAgent = request_object.app.state.value_driver_agent
        persona_agent: PersonaAgent = request_object.app.state.persona_agent

        agent_input = {"user_query": fastapi_request.user_query}

        # Execute agents concurrently
        vd_result_task = value_driver_agent.execute(agent_input)
        persona_result_task = persona_agent.execute(agent_input)

        vd_agent_result, persona_agent_result = await asyncio.gather(
            vd_result_task,
            persona_result_task,
            return_exceptions=True # Return exceptions so we can handle them
        )

        # Process ValueDriverAgent result
        if isinstance(vd_agent_result, Exception):
            logger.error(f"ValueDriverAgent execution failed: {vd_agent_result}")
            raise HTTPException(status_code=500, detail=f"ValueDriverAgent error: {str(vd_agent_result)}")
        if vd_agent_result.status == AgentStatus.FAILED:
            logger.error(f"ValueDriverAgent failed: {vd_agent_result.data}")
            raise HTTPException(status_code=500, detail=f"ValueDriverAgent failed: {vd_agent_result.data.get('error', 'Unknown error')}")
        
        value_drivers_data = vd_agent_result.data
        # Ensure the data is in the correct format for Pydantic model
        # This might involve transforming the list of dicts into a list of ValueDriverPillar if not already directly compatible
        # For now, assuming direct compatibility based on previous agent output structure.
        try:
            value_drivers = [ValueDriverPillar(**item) for item in value_drivers_data] if value_drivers_data else []
        except Exception as e_pydantic_vd:
            logger.error(f"Error parsing ValueDriverAgent output: {e_pydantic_vd}. Data: {value_drivers_data}")
            raise HTTPException(status_code=500, detail="Internal server error processing value driver data.")

        # Process PersonaAgent result
        if isinstance(persona_agent_result, Exception):
            logger.error(f"PersonaAgent execution failed: {persona_agent_result}")
            raise HTTPException(status_code=500, detail=f"PersonaAgent error: {str(persona_agent_result)}")
        if persona_agent_result.status == AgentStatus.FAILED:
            logger.error(f"PersonaAgent failed: {persona_agent_result.data}")
            raise HTTPException(status_code=500, detail=f"PersonaAgent failed: {persona_agent_result.data.get('error', 'Unknown error')}")

        personas_data = persona_agent_result.data
        # Ensure data format for Pydantic model
        try:
            personas = [Persona(**item) for item in personas_data] if personas_data else []
        except Exception as e_pydantic_p:
            logger.error(f"Error parsing PersonaAgent output: {e_pydantic_p}. Data: {personas_data}")
            raise HTTPException(status_code=500, detail="Internal server error processing persona data.")

        execution_details = ExecutionDetails(
            value_driver_agent_time_ms=getattr(vd_agent_result, 'execution_time_ms', None),
            persona_agent_time_ms=getattr(persona_agent_result, 'execution_time_ms', None)
        )

        discovery_data = DiscoveryData(
            value_drivers=value_drivers,
            personas=personas
        )

        return DiscoverValueResponse(
            discovery=discovery_data,
            execution_details=execution_details
        )

    except HTTPException: # Re-raise HTTPExceptions to let FastAPI handle them
        raise
    except Exception as e:
        logger.error(f"Error in discover_value endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

    # Simulated PersonaAgent output
    sim_personas = [
        Persona(name="Sales Leader (CRO, VP of Sales)", description="Focuses on sales team efficiency, revenue targets, and sales cycle length."),
        Persona(name="Sales Operations Manager", description="Concerned with process optimization, data accuracy, and CRM management.")
    ]

    # In a real implementation, you would call your agents here:
    # e.g., value_driver_result = await value_driver_agent.execute({'user_query': request.user_query})
    # e.g., persona_result = await persona_agent.execute({'user_query': request.user_query})
    # Then, you'd parse their results into the Pydantic models.
    # Error handling for agent failures would also be critical.

    response_data = DiscoverValueResponse(
        discovery=DiscoveryData(
            value_drivers=sim_value_drivers, 
            personas=sim_personas
        ),
        execution_details=ExecutionDetails(
            value_driver_agent_time_ms=75, # Simulated time
            persona_agent_time_ms=45  # Simulated time
        )
    )
    return response_data

