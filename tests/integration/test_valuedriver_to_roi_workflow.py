import pytest
import asyncio
from typing import Dict, Any

from agents.roi_calculator.main import ROICalculatorAgent
from agents.core.agent_base import AgentStatus
from agents.core.mcp_client import MCPClient
from memory.core import MemoryManager


@pytest.fixture
def mcp_client() -> MCPClient:
    """Provides a properly initialized MCPClient for integration tests."""
    memory_manager = MemoryManager()
    return MCPClient(memory_manager=memory_manager)


@pytest.mark.asyncio
async def test_valuedriver_to_roi_workflow(mcp_client: MCPClient):
    """
    Tests the workflow from identified value drivers to ROI calculation.
    """
    # 1. Initialize Agent
    roi_config = {"model": "gpt-4", "temperature": 0.1}
    roi_agent = ROICalculatorAgent("roi-calculator-001", mcp_client, roi_config)

    # 2. Define Inputs (simulating output from ValueDriverAgent)
    value_drivers = [
        {
            "name": "Reduced Manual Data Entry",
            "description": "Automating data entry from emails and calls into the CRM.",
            "financial_impact": {
                "type": "cost_savings",
                "value_usd_per_year": 15000
            }
        },
        {
            "name": "Increased Sales Team Efficiency",
            "description": "Sales reps spend less time on admin and more time selling.",
            "financial_impact": {
                "type": "revenue_increase",
                "value_usd_per_year": 50000
            }
        }
    ]
    
    roi_inputs = {
        "value_drivers": value_drivers,
        "investment_cost": 25000
    }

    # 3. Execute ROI Calculator Agent
    roi_result = await roi_agent.execute(roi_inputs)

    # 4. Assert ROI Calculation Success
    assert roi_result.status == AgentStatus.COMPLETED, f"ROI agent failed: {roi_result.data.get('message')}"
    assert "roi_summary" in roi_result.data, "ROI agent did not produce 'roi_summary'"
    
    roi_summary = roi_result.data["roi_summary"]
    assert isinstance(roi_summary, dict), "ROI summary should be a dict"
    assert "total_annual_value" in roi_summary
    assert "roi_percentage" in roi_summary
    assert "payback_period_months" in roi_summary
    assert roi_summary["total_annual_value"] > 0

    print(f"Workflow successful: Calculated ROI summary.")
