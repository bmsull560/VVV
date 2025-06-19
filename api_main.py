from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException

from memory.core import MemoryManager
from agents.core.mcp_client import MCPClient
from agents.value_driver.main import ValueDriverAgent
from agents.persona.main import PersonaAgent
from agents.roi_calculator.main import RoiCalculatorAgent
from agents.sensitivity_analysis.main import SensitivityAnalysisAgent
from agents.narrative_generator.main import NarrativeGeneratorAgent
from agents.critique.main import CritiqueAgent
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

# --- End Pydantic Models for /api/quantify-roi ---


# --- Pydantic Models for /api/generate-narrative ---

class CritiqueOutput(BaseModel):
    critique_summary: str
    suggestions: List[str]
    confidence_score: float

class NarrativeOutput(BaseModel):
    narrative_text: str
    key_points: List[str]

class GenerateNarrativeRequest(BaseModel):
    user_query: str
    value_drivers: List[ValueDriverPillar] # From discovery, with user inputs for T3 metrics
    personas: List[Persona] # From discovery
    roi_summary: RoiSummary # From quantification
    sensitivity_analysis_results: Optional[List[SensitivityScenarioOutput]] = None # From quantification

class NarrativeExecutionDetails(BaseModel):
    narrative_generator_agent_time_ms: Optional[int] = None
    critique_agent_time_ms: Optional[int] = None

class GenerateNarrativeResponse(BaseModel):
    narrative_output: NarrativeOutput
    critique_output: CritiqueOutput
    execution_details: Optional[NarrativeExecutionDetails] = None

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

    # Instantiate NarrativeGeneratorAgent
    narrative_config = agent_configs_from_yaml.get('narrative_generator', {})
    app.state.narrative_generator_agent = NarrativeGeneratorAgent(
        agent_id='narrative_generator_api',
        mcp_client=app.state.mcp_client,
        config=narrative_config
    )
    logger.info("NarrativeGeneratorAgent initialized.")

    # Instantiate CritiqueAgent
    critique_config = agent_configs_from_yaml.get('critique', {})
    app.state.critique_agent = CritiqueAgent(
        agent_id='critique_api',
        mcp_client=app.state.mcp_client,
        config=critique_config
    )
    logger.info("CritiqueAgent initialized.")
    logger.info("All agents initialized for API.")


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
async def discover_value(fastapi_request: DiscoverValueRequest, request_object: Request):  # Renamed 'request' to 'fastapi_request' to avoid conflict with 'request_object' for app.state
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


@app.post("/api/quantify-roi", response_model=QuantifyRoiResponse, tags=["Quantification"])
async def quantify_roi(fastapi_request: QuantifyRoiRequest, request_object: Request):
    """
    Calculates ROI based on selected value drivers and performs sensitivity analysis.
    """
    try:
        roi_calculator_agent: RoiCalculatorAgent = request_object.app.state.roi_calculator_agent
        sensitivity_analysis_agent: SensitivityAnalysisAgent = request_object.app.state.sensitivity_analysis_agent

        # --- Execute RoiCalculatorAgent ---
        # The ValueDriverPillar model in the request needs to be converted to the dict format expected by the agent.
        # Agents typically expect a list of dictionaries for 'drivers'.
        drivers_for_agent = [pillar.model_dump() for pillar in fastapi_request.value_drivers]

        roi_agent_input = {
            "drivers": drivers_for_agent,
            "investment": fastapi_request.investment_amount
        }

        roi_agent_result = await roi_calculator_agent.execute(roi_agent_input)

        if isinstance(roi_agent_result, Exception):
            logger.error(f"RoiCalculatorAgent execution failed: {roi_agent_result}")
            raise HTTPException(status_code=500, detail=f"RoiCalculatorAgent error: {str(roi_agent_result)}")
        if roi_agent_result.status == AgentStatus.FAILED:
            logger.error(f"RoiCalculatorAgent failed: {roi_agent_result.data}")
            raise HTTPException(status_code=500, detail=f"RoiCalculatorAgent failed: {roi_agent_result.data.get('error', 'Unknown error')}")

        try:
            # Assuming roi_agent_result.data directly matches RoiSummary fields or is a dict that can be unpacked
            roi_summary = RoiSummary(**roi_agent_result.data)
        except Exception as e_pydantic_roi:
            logger.error(f"Error parsing RoiCalculatorAgent output: {e_pydantic_roi}. Data: {roi_agent_result.data}")
            raise HTTPException(status_code=500, detail="Internal server error processing ROI data.")

        # --- Execute SensitivityAnalysisAgent (if variations provided) ---
        sensitivity_results_list = None
        sa_execution_time_ms = None

        if fastapi_request.sensitivity_variations:
            # Convert SensitivityVariationInput to the dict format expected by the agent if necessary
            variations_for_agent = [var.model_dump() for var in fastapi_request.sensitivity_variations]
            
            sa_agent_input = {
                "drivers": drivers_for_agent, # Or potentially drivers from ROI agent output if they are modified
                "investment": fastapi_request.investment_amount,
                "variations": variations_for_agent,
                # "base_roi_results": roi_agent_result.data # If SA agent needs full context from ROI agent
            }
            sa_agent_result = await sensitivity_analysis_agent.execute(sa_agent_input)

            if isinstance(sa_agent_result, Exception):
                logger.error(f"SensitivityAnalysisAgent execution failed: {sa_agent_result}")
                raise HTTPException(status_code=500, detail=f"SensitivityAnalysisAgent error: {str(sa_agent_result)}")
            if sa_agent_result.status == AgentStatus.FAILED:
                logger.error(f"SensitivityAnalysisAgent failed: {sa_agent_result.data}")
                raise HTTPException(status_code=500, detail=f"SensitivityAnalysisAgent failed: {sa_agent_result.data.get('error', 'Unknown error')}")

            sa_execution_time_ms = getattr(sa_agent_result, 'execution_time_ms', None)
            # Assuming sa_agent_result.data is a list of dicts matching SensitivityScenarioOutput fields
            try:
                sensitivity_results_list = [SensitivityScenarioOutput(**item) for item in sa_agent_result.data] if sa_agent_result.data else []
            except Exception as e_pydantic_sa:
                logger.error(f"Error parsing SensitivityAnalysisAgent output: {e_pydantic_sa}. Data: {sa_agent_result.data}")
                raise HTTPException(status_code=500, detail="Internal server error processing sensitivity analysis data.")

        quantification_data = QuantificationData(
            roi_summary=roi_summary,
            sensitivity_analysis_results=sensitivity_results_list
        )

        execution_details = QuantificationExecutionDetails(
            roi_calculator_agent_time_ms=getattr(roi_agent_result, 'execution_time_ms', None),
            sensitivity_analysis_agent_time_ms=sa_execution_time_ms
        )

        return QuantifyRoiResponse(
            quantification=quantification_data,
            execution_details=execution_details
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in quantify_roi endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/api/generate-narrative", response_model=GenerateNarrativeResponse, tags=["Narrative"])
async def generate_narrative(fastapi_request: GenerateNarrativeRequest, request_object: Request):
    """
    Generates a business case narrative based on discovered value, personas, and quantified ROI.
    """
    try:
        narrative_agent: NarrativeGeneratorAgent = request_object.app.state.narrative_generator_agent
        critique_agent: CritiqueAgent = request_object.app.state.critique_agent

        # 1. Prepare inputs for the NarrativeGeneratorAgent
        narrative_agent_inputs = {
            "user_query": fastapi_request.user_query,
            "value_drivers": [p.model_dump() for p in fastapi_request.value_drivers],
            "personas": [p.model_dump() for p in fastapi_request.personas],
            "roi_summary": fastapi_request.roi_summary.model_dump(),
            "sensitivity_analysis_results": 
                [s.model_dump() for s in fastapi_request.sensitivity_analysis_results] 
                if fastapi_request.sensitivity_analysis_results else None
        }

        # 2. Execute NarrativeGeneratorAgent
        narrative_result = await narrative_agent.execute(narrative_agent_inputs)
        if narrative_result.status == AgentStatus.FAILED:
            logger.error(f"NarrativeGeneratorAgent failed: {narrative_result.data}")
            raise HTTPException(status_code=500, detail=f"Narrative generation failed: {narrative_result.data.get('error')}")

        # 3. Prepare inputs for CritiqueAgent from narrative output
        critique_agent_inputs = {
            "narrative_text": narrative_result.data.get("narrative_text", ""),
            "key_points": narrative_result.data.get("key_points", [])
        }

        # 4. Execute CritiqueAgent
        critique_result = await critique_agent.execute(critique_agent_inputs)
        if critique_result.status == AgentStatus.FAILED:
            logger.error(f"CritiqueAgent failed: {critique_result.data}")
            # Failing critique might not be a fatal error for the whole endpoint, but we'll raise for now
            raise HTTPException(status_code=500, detail=f"Critique generation failed: {critique_result.data.get('error')}")

        # 5. Parse and combine results for the final response
        try:
            narrative_output = NarrativeOutput(**narrative_result.data)
            critique_output = CritiqueOutput(**critique_result.data)
        except Exception as e_pydantic:
            logger.error(f"Error parsing agent outputs: {e_pydantic}. Narrative Data: {narrative_result.data}, Critique Data: {critique_result.data}")
            raise HTTPException(status_code=500, detail="Internal server error processing agent results.")

        execution_details = NarrativeExecutionDetails(
            narrative_generator_agent_time_ms=narrative_result.execution_time_ms,
            critique_agent_time_ms=critique_result.execution_time_ms
        )

        return GenerateNarrativeResponse(
            narrative_output=narrative_output,
            critique_output=critique_output,
            execution_details=execution_details
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_narrative endpoint: {e}", exc_info=True)
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

