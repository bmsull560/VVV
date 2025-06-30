"""
Unit tests for the production-ready BusinessCaseComposerAgent.

This suite covers:
1.  Input validation for required fields.
2.  Composition of business cases in JSON format.
3.  Composition of business cases in Markdown format.
4.  Dynamic inclusion/exclusion of optional sections (e.g., sensitivity analysis).
5.  Graceful error handling for invalid formats or unexpected exceptions.
6.  Correct integration with the MCP client for data persistence.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.business_case_composer.main import BusinessCaseComposerAgent, AgentStatus

# Mock data fixtures
@pytest.fixture
def valid_inputs():
    """Provides a dictionary of valid inputs for a standard test case."""
    return {
        "user_query": "Test Query for a new CRM",
        "value_drivers": [{"name": "Productivity Gain", "description": "10% increase in team efficiency"}],
        "roi_summary": {
            "total_annual_value": 50000,
            "roi_percentage": 250.5,
            "payback_period_months": 4.8,
            "npv": 120000
        },
        "narrative_output": {"narrative_text": "This is the executive summary.", "key_points": ["Point A"]},
        "critique_output": {"confidence_score": 0.95, "critique_summary": "Looks good.", "suggestions": []},
        "sensitivity_analysis_results": [
            {"variable_name": "Adoption Rate", "roi_impact_percentage": -15.5, "risk_level": "Medium"}
        ]
    }

@pytest.fixture
def mock_mcp_client():
    """Provides a mock MCP client with an async create_entity method."""
    client = MagicMock()
    client.create_entity = AsyncMock()
    return client

@pytest.fixture
def composer_agent(mock_mcp_client):
    """Provides an instance of the BusinessCaseComposerAgent for testing, with LLMClient patched."""
    with patch('agents.core.agent_base.LLMClient') as MockLLMClient:
        # The LLM client is mocked, so no real API key is needed.
        # The mock instance can be configured here if any of its methods are called.
        agent = BusinessCaseComposerAgent(
            agent_id="test_composer_agent",
            mcp_client=mock_mcp_client,
            config={}
        )
        yield agent

# Test cases
@pytest.mark.asyncio
async def test_input_validation_success(composer_agent, valid_inputs):
    """Tests that valid inputs pass the validation check."""
    result = composer_agent._validate_inputs(valid_inputs)
    assert result is None

@pytest.mark.asyncio
@pytest.mark.parametrize("missing_field", ["user_query", "value_drivers", "roi_summary", "narrative_output"])
async def test_input_validation_failure(composer_agent, valid_inputs, missing_field):
    """Tests that validation fails when a required field is missing."""
    invalid_inputs = valid_inputs.copy()
    del invalid_inputs[missing_field]
    
    result = await composer_agent.execute(invalid_inputs)
    assert result.status == AgentStatus.FAILED
    assert missing_field in result.data["message"]

@pytest.mark.asyncio
async def test_compose_json_output(composer_agent, valid_inputs):
    """Tests the composition of a business case in JSON format."""
    valid_inputs["output_format"] = "json"
    result = await composer_agent.execute(valid_inputs)
    
    assert result.status == AgentStatus.COMPLETED
    assert result.data["format"] == "json"
    doc = result.data["composed_business_case"]
    assert doc["title"] == f"Business Value Proposal for {valid_inputs['user_query']}"
    assert doc["financial_projections"]["roi_percentage"] == 250.5
    assert len(doc["sensitivity_analysis"]) == 1

@pytest.mark.asyncio
async def test_compose_markdown_output(composer_agent, valid_inputs):
    """Tests the composition of a business case in Markdown format."""
    valid_inputs["output_format"] = "markdown"
    result = await composer_agent.execute(valid_inputs)
    
    assert result.status == AgentStatus.COMPLETED
    assert result.data["format"] == "markdown"
    doc = result.data["composed_business_case"]
    assert "# Business Value Proposal" in doc
    assert "## Financial Projections (ROI)" in doc
    assert "| ROI Percentage | 250.50% |" in doc
    assert "### Sensitivity Analysis" in doc
    assert "| Adoption Rate | -15.50% | Medium |" in doc

@pytest.mark.asyncio
async def test_dynamic_section_exclusion(composer_agent, valid_inputs):
    """Tests that optional sections are excluded if their data is not provided."""
    inputs = valid_inputs.copy()
    del inputs["sensitivity_analysis_results"]
    inputs["output_format"] = "markdown"
    
    result = await composer_agent.execute(inputs)
    assert result.status == AgentStatus.COMPLETED
    doc = result.data["composed_business_case"]
    assert "### Sensitivity Analysis" not in doc

@pytest.mark.asyncio
async def test_invalid_output_format(composer_agent, valid_inputs):
    """Tests the agent's response to an unsupported output format."""
    valid_inputs["output_format"] = "xml"
    result = await composer_agent.execute(valid_inputs)
    assert result.status == AgentStatus.FAILED
    assert "Unsupported output format" in result.data["message"]

@pytest.mark.asyncio
async def test_mcp_storage_call(composer_agent, valid_inputs, mock_mcp_client):
    """Tests that the agent correctly calls the MCP client to store the result."""
    await composer_agent.execute(valid_inputs)
    mock_mcp_client.create_entity.assert_called_once()
    call_args = mock_mcp_client.create_entity.call_args[0][0]
    assert call_args.entity_type == "composed_business_case"
    assert "composed_document" in call_args.data

@pytest.mark.asyncio
async def test_graceful_handling_of_unexpected_error(composer_agent, valid_inputs):
    """Tests that the agent handles unexpected internal exceptions gracefully."""
    composer_agent._compose_json_document = MagicMock(side_effect=Exception("Unexpected composition error"))
    
    result = await composer_agent.execute(valid_inputs)
    assert result.status == AgentStatus.FAILED
    assert "An unexpected error occurred" in result.data["message"]
