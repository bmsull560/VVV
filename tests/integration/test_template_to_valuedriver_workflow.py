import pytest
import asyncio
from typing import Dict, Any

from agents.template_selector.main import TemplateSelectorAgent
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
async def test_template_to_valuedriver_workflow(mcp_client: MCPClient):
    """
    Tests the workflow from a selected template to value driver identification.
    """
    # 1. Initialize Agent
    value_driver_config = {"model": "gpt-4", "temperature": 0.1}
    value_driver_agent = ValueDriverAgent("value-driver-001", mcp_client, value_driver_config)

    # 2. Define Inputs (simulating a selected template)
    template_name = "SaaS_CRM_Implementation"
    value_driver_inputs = {"template_name": template_name}

    # 3. Execute Value Driver Agent
    # 4. Execute Value Driver Agent with the selected template
    value_driver_inputs = {
        "structured_data": structured_data,
        "template_name": template_name
    }
    value_driver_result = await value_driver_agent.execute(value_driver_inputs)

    # 5. Assert Value Driver Success
    assert value_driver_result.status == AgentStatus.COMPLETED, f"Value Driver agent failed: {value_driver_result.data.get('message')}"
    assert "value_drivers" in value_driver_result.data, "Value Driver agent did not produce 'value_drivers'"
    
    value_drivers = value_driver_result.data["value_drivers"]
    assert isinstance(value_drivers, list), "Value drivers should be a list"
    assert len(value_drivers) > 0, "Value Driver agent returned no value drivers"
    assert "name" in value_drivers[0] and "description" in value_drivers[0], "Value driver objects are missing required keys"

    print(f"Workflow successful: Identified {len(value_drivers)} value drivers using template '{template_name}'.")
