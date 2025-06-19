from fastapi import FastAPI, HTTPException
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

# --- End Pydantic Models ---

app = FastAPI(
    title="B2BValue API",
    description="API for the B2BValue Interactive Calculator and Proposal Generator.",
    version="0.1.0",
)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the B2BValue API!"}

# Future endpoints will be added here

@app.post("/api/discover-value", response_model=DiscoverValueResponse, tags=["Discovery"])
async def discover_value(request: DiscoverValueRequest):
    """
    Processes a user query to discover potential value drivers and target personas.
    """
    # TODO: Replace simulated data with actual agent calls
    # This will require setting up MemoryManager, MCPClient, and instantiating agents
    # within the FastAPI application lifecycle or via dependency injection.

    # Simulated ValueDriverAgent output
    sim_value_drivers = [
        ValueDriverPillar(
            pillar="Cost Savings", 
            tier_2_drivers=[
                Tier2Driver(
                    name="Reduce Manual Labor", 
                    description="Automating manual processes to reduce employee hours.", 
                    keywords_found=["manual process", "time-consuming"],
                    tier_3_metrics=[
                        Tier3Metric(name="Hours saved per week", type="number", default_value=10),
                        Tier3Metric(name="Average hourly rate", type="currency", default_value=50)
                    ]
                )
            ]
        ),
        ValueDriverPillar(
            pillar="Productivity Gains",
            tier_2_drivers=[
                Tier2Driver(
                    name="Accelerate Task Completion",
                    description="Reducing the time it takes to complete key business tasks.",
                    keywords_found=["slow", "bottleneck"],
                    tier_3_metrics=[
                        Tier3Metric(name="Time saved per task (minutes)", type="number", default_value=60),
                        Tier3Metric(name="Tasks per week", type="number", default_value=20)
                    ]
                )
            ]
        )
    ]

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

