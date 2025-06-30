import pytest
import asyncio
from typing import Dict, Any
import logging

from agents.roi_calculator.main import ROICalculatorAgent
from agents.value_driver.main import ValueDriverAgent
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
    # Set logging level for ValueDriverAgent to DEBUG
    logging.getLogger('agents.value_driver.main').setLevel(logging.DEBUG)

    # 1. Initialize Agent
    roi_config = {"model": "gpt-4", "temperature": 0.1}
    roi_agent = ROICalculatorAgent("roi-calculator-001", mcp_client, roi_config)

    # 2. Execute ValueDriverAgent to get actual value drivers
    value_driver_config = {"model": "gpt-4", "temperature": 0.1}
    value_driver_agent = ValueDriverAgent("value-driver-001", mcp_client, value_driver_config)

    value_driver_inputs = {
        "user_query": "We need to reduce manual data entry and improve sales efficiency.",
        "include_quantification": True
    }
    value_driver_result = await value_driver_agent.execute(value_driver_inputs)

    assert value_driver_result.status == AgentStatus.COMPLETED, f"ValueDriverAgent failed: {value_driver_result.data.get('message')}"
    assert "value_drivers" in value_driver_result.data, "ValueDriverAgent did not produce 'value_drivers'"
    assert len(value_driver_result.data["value_drivers"]) > 0, "ValueDriverAgent returned empty 'value_drivers'"

    extracted_value_drivers = value_driver_result.data["value_drivers"]
    
    roi_inputs = {
        "value_drivers": extracted_value_drivers,
        "investment_cost": 25000 # Keep investment cost fixed for this test
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
