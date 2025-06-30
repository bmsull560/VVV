import pytest
import asyncio
from typing import Dict, Any

from agents.business_case_composer.main import BusinessCaseComposerAgent, OutputFormat
from agents.core.agent_base import AgentStatus
from agents.core.mcp_client import MCPClient
from memory.core import MemoryManager


@pytest.fixture
def mcp_client() -> MCPClient:
    """Provides a properly initialized MCPClient for integration tests."""
    memory_manager = MemoryManager()
    return MCPClient(memory_manager=memory_manager)


@pytest.mark.asyncio
async def test_full_composition_workflow(mcp_client: MCPClient):
    """
    Tests the final composition stage of the business case workflow.
    """
    # 1. Initialize Agent
    composer_config = {"model": "gpt-4", "temperature": 0.1}
    composer_agent = BusinessCaseComposerAgent("composer-001", mcp_client, composer_config)

    # 2. Define Inputs (simulating the complete set of outputs from all upstream agents)
    composition_inputs = {
        "user_query": "business case for a new CRM system",
        "value_drivers": [
            {"name": "Reduced Manual Data Entry", "description": "..."},
            {"name": "Increased Sales Team Efficiency", "description": "..."}
        ],
        "roi_summary": {
            "total_annual_value": 65000,
            "roi_percentage": 260.0,
            "payback_period_months": 4.6
        },
        "narrative_output": {
            "narrative_text": "Investing in a new CRM system will drive significant value...",
            "confidence_score": 0.95
        },
        "output_format": OutputFormat.JSON
    }

    # 3. Execute Business Case Composer Agent
    composition_result = await composer_agent.execute(composition_inputs)

    # 4. Assert Composition Success
    assert composition_result.status == AgentStatus.COMPLETED, f"Composer agent failed: {composition_result.data.get('message')}"
    assert "composed_business_case" in composition_result.data, "Composer agent did not produce a business case"
    
    business_case = composition_result.data["composed_business_case"]
    assert isinstance(business_case, dict), "Business case should be a dict for JSON format"
    assert "title" in business_case
    assert "executive_summary" in business_case
    assert "financial_projections" in business_case
    assert business_case["financial_projections"]["roi_percentage"] == 260.0

    print(f"Workflow successful: Composed final business case document.")
