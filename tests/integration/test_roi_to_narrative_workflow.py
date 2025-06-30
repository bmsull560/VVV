import pytest
import asyncio
from typing import Dict, Any

from agents.narrative_generator.main import NarrativeGeneratorAgent
from agents.core.agent_base import AgentStatus
from agents.core.mcp_client import MCPClient
from memory.core import MemoryManager


@pytest.fixture
def mcp_client() -> MCPClient:
    """Provides a properly initialized MCPClient for integration tests."""
    memory_manager = MemoryManager()
    return MCPClient(memory_manager=memory_manager)


@pytest.mark.asyncio
async def test_roi_to_narrative_workflow(mcp_client: MCPClient):
    """
    Tests the workflow from an ROI summary to narrative generation.
    """
    # 1. Initialize Agent
    narrative_config = {"model": "gpt-4", "temperature": 0.7}
    narrative_agent = NarrativeGeneratorAgent("narrative-generator-001", mcp_client, narrative_config)

    # 2. Define Inputs (simulating outputs from previous agents)
    roi_summary = {
        "total_annual_value": 65000,
        "roi_percentage": 260.0,
        "payback_period_months": 4.6,
        "npv": 150000
    }
    value_drivers = [
        {"name": "Reduced Manual Data Entry", "description": "Automating data entry..."},
        {"name": "Increased Sales Team Efficiency", "description": "Sales reps spend less time..."}
    ]
    user_query = "business case for a new CRM system"

    narrative_inputs = {
        "roi_summary": roi_summary,
        "value_drivers": value_drivers,
        "user_query": user_query
    }

    # 3. Execute Narrative Generator Agent
    narrative_result = await narrative_agent.execute(narrative_inputs)

    # 4. Assert Narrative Generation Success
    assert narrative_result.status == AgentStatus.COMPLETED, f"Narrative agent failed: {narrative_result.data.get('message')}"
    assert "narrative_output" in narrative_result.data, "Narrative agent did not produce 'narrative_output'"
    
    narrative_output = narrative_result.data["narrative_output"]
    assert isinstance(narrative_output, dict), "Narrative output should be a dict"
    assert "narrative_text" in narrative_output and len(narrative_output["narrative_text"]) > 50
    assert "confidence_score" in narrative_output and narrative_output["confidence_score"] > 0

    print(f"Workflow successful: Generated narrative with confidence score {narrative_output['confidence_score']}.")
