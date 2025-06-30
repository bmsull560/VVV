import pytest
import asyncio
from typing import Dict, Any, Type

from agents.intake_assistant.main import IntakeAssistantAgent
from agents.template_selector.main import TemplateSelectorAgent
from agents.core.agent_base import AgentStatus, AgentResult
from agents.core.mcp_client import MCPClient
from memory.core import MemoryManager


@pytest.fixture
def mcp_client() -> MCPClient:
    """Provides a properly initialized MCPClient for integration tests."""
    memory_manager = MemoryManager()
    return MCPClient(memory_manager=memory_manager)


@pytest.mark.asyncio
async def test_intake_to_template_selection_workflow(mcp_client: MCPClient, monkeypatch):
    """
    Tests the full workflow from user query intake to template selection,
    ensuring data flows correctly between the IntakeAssistant and TemplateSelector agents.
    """
    # Mock MCP methods that are called by the intake agent
    async def mock_search_nodes(*args, **kwargs):
        return [] # Simulate no existing projects found

    async def mock_create_entities(*args, **kwargs):
        return {'status': 'success', 'entity_ids': ['mock-id']}

    monkeypatch.setattr(mcp_client, 'search_knowledge_graph_nodes', mock_search_nodes)
    monkeypatch.setattr(mcp_client, 'create_entities', mock_create_entities)

    # Mock the template database for the TemplateSelectorAgent
    def mock_load_templates(*args, **kwargs):
        return {
            "TPL-CRM-001": {
                "template_id": "TPL-CRM-001",
                "template_name": "CRM Implementation Plan",
                "industry": "Technology",
                "description": "A template for implementing a new CRM system.",
                "keywords": ["crm", "sales", "technology"],
                "complexity_score": 3
            },
            "TPL-GEN-001": {
                "template_id": "TPL-GEN-001",
                "template_name": "Generic Project Kickstart",
                "industry": "Generic",
                "description": "A general-purpose template for starting new projects.",
                "keywords": ["generic", "standard", "kickstart"],
                "complexity_score": 3
            }
        }
    monkeypatch.setattr(TemplateSelectorAgent, '_load_template_database', mock_load_templates)

    # 1. Initialize Agents
    intake_config = {"model": "gpt-4", "temperature": 0.1}
    template_config = {"model": "gpt-4", "temperature": 0.1}
    intake_agent = IntakeAssistantAgent("intake-001", mcp_client, intake_config)
    template_agent = TemplateSelectorAgent("template-selector-001", mcp_client, template_config)

    # 2. Define User Query and other required inputs for IntakeAssistant
    intake_inputs = {
        "user_query": "I need to build a business case for a new CRM system to improve sales productivity.",
        "project_name": "New CRM System",
        "description": "A project to implement a new CRM to improve sales team efficiency.",
        "business_objective": "Increase sales productivity by 15% within the first year."
    }

    # 3. Execute Intake Assistant Agent
    intake_result = await intake_agent.execute(intake_inputs)

    # 4. Assert Intake Success and Data Structuring
    assert intake_result.status == AgentStatus.COMPLETED, f"Intake agent failed: {intake_result.error_details}"
    assert "project_data" in intake_result.data, "Intake agent did not produce 'project_data'"

    # 5. Prepare input for and execute Template Selector Agent
    project_info = intake_result.data["project_data"]["basic_info"]
    template_inputs = {
        "industry": project_info.get("industry", "Technology"),  # Default to Technology for this test case
        "business_objective": project_info["business_objective"],
        # Pass any other optional inputs that might be available
        "stakeholder_types": project_info.get("stakeholder_types"),
        "complexity_level": project_info.get("complexity_level"),
        "primary_value_drivers": project_info.get("primary_value_drivers")
    }
    template_result = await template_agent.execute(template_inputs)

    # 6. Assert Template Selection Success
    assert template_result.status == AgentStatus.COMPLETED, f"Template agent failed: {template_result.error_details}"
    assert "selected_template" in template_result.data, "Template agent did not select a template"
    assert template_result.data["selected_template"]["template_id"] == "TPL-CRM-001"

    print(f"Workflow successful: Selected template '{template_result.data['selected_template']['template_id']}' for query.")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_input, expected_error_fragment",
    [
        # Missing required fields
        ({"description": "D", "business_objective": "O"}, "Required field 'user_query' is missing or null"),
        ({"user_query": "Q", "description": "D", "business_objective": "O"}, "Required field 'project_name' is missing or null"),
        ({"user_query": "Q", "project_name": "P", "business_objective": "O"}, "Required field 'description' is missing or null"),
        ({"user_query": "Q", "project_name": "P", "description": "D"}, "Required field 'business_objective' is missing or null"),
        # Field constraint violations
        ({"user_query": "", "project_name": "Test Project", "description": "A valid description of the project.", "business_objective": "A valid business objective."}, "Field 'user_query' must be at least 1 characters long"),
    ],
)
async def test_intake_workflow_validation_errors(
    mcp_client: MCPClient, invalid_input: Dict[str, Any], expected_error_fragment: str
):
    """
    Tests that the intake workflow handles various invalid inputs gracefully
    by checking for missing or empty required fields.
    """
    # 1. Initialize Agent
    intake_config = {"model": "gpt-4", "temperature": 0.1}
    intake_agent = IntakeAssistantAgent("intake-002", mcp_client, intake_config)

    # 2. Execute Intake Assistant Agent with invalid input
    intake_result = await intake_agent.execute(invalid_input)

    # 3. Assert Agent Failure with a specific validation message
    assert intake_result.status == AgentStatus.FAILED, f"Agent should fail on invalid input: {invalid_input}"
    assert "error" in intake_result.data, "Agent result should contain an 'error' key"
    assert intake_result.data["error"] == "Input validation failed"
    assert "details" in intake_result.data, "Agent result should contain a 'details' key"
    assert any(expected_error_fragment in detail for detail in intake_result.data["details"]), \
        f"Expected error fragment '{expected_error_fragment}' not found in details: {intake_result.data['details']}"

    print(f"Workflow handled invalid input correctly: {intake_result.data['details']}")


@pytest.mark.asyncio
async def test_workflow_handoff_with_unrecognized_industry(mcp_client: MCPClient, monkeypatch):
    """
    Tests the workflow's robustness when the Intake agent produces an industry
    that the Template Selector agent does not recognize. The selector should
    fall back to a default template.
    """
    # 1. Initialize Agents
    intake_config = {"model": "gpt-4", "temperature": 0.1}
    template_config = {"model": "gpt-4", "temperature": 0.1}

    class MockIntakeAgent(IntakeAssistantAgent):
        async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
            # Simulate successful execution but with a weird industry
            structured_data = {
                "industry": "Underwater Basket Weaving",
                "business_objective": "Increase basket output",
                "goals": ["Make more baskets"],
                "success_criteria": ["Baskets are woven"],
                "project_name": "Basket Case",
                "description": "Weaving baskets underwater"
            }
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data={"structured_data": structured_data},
                execution_time_ms=50
            )

    # Mock the template database to ensure a generic template is available
    def mock_load_templates(*args, **kwargs):
        return {
            "TPL-GEN-001": {
                "template_id": "TPL-GEN-001",
                "template_name": "Generic Project Kickstart",
                "industry": "Generic",
                "description": "A general-purpose template for starting new projects.",
                "keywords": ["generic", "standard", "kickstart"],
                "complexity_score": 3
            }
        }
    monkeypatch.setattr(TemplateSelectorAgent, '_load_template_database', mock_load_templates)

    intake_agent = MockIntakeAgent("intake-mock-001", mcp_client, intake_config)
    template_agent = TemplateSelectorAgent("template-selector-002", mcp_client, template_config)

    # 2. Execute mock intake agent
    intake_result = await intake_agent.execute({}) # Input doesn't matter for the mock

    # 3. Prepare input for and execute Template Selector Agent
    structured_data = intake_result.data["structured_data"]
    template_inputs = {
        "industry": structured_data["industry"],
        "business_objective": structured_data["business_objective"]
    }
    template_result = await template_agent.execute(template_inputs)

    # 4. Assert that the template agent completed and fell back to a default
    assert template_result.status == AgentStatus.COMPLETED, "Template agent should complete even with unknown industry"
    assert "selected_template_id" in template_result.data, "Template agent did not select a template"
    assert template_result.data["selected_template_id"] == "TPL-GEN-001", "Template agent did not fall back to the correct generic template"

    print("Workflow correctly handled unrecognized industry by falling back to default template.")