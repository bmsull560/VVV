"""
Unit tests for the production-ready TemplateSelectorAgent.

This test suite covers:
1.  Agent initialization and configuration loading.
2.  Pydantic-based input validation.
3.  Weighted scoring and confidence scoring logic.
4.  Correct handling of missing templates and invalid inputs.
5.  MCP audit trail recording.
6.  Graceful error handling for unexpected exceptions.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from agents.core.agent_base import AgentStatus
from agents.template_selector.main import (
    TemplateSelectorAgent, 
    IndustryType, 
    ComplexityLevel, 
    TemplateSelectorResult
)

from datetime import datetime, timezone

# --- Test Fixtures ---

@pytest.fixture
def mock_mcp_client():
    """Provides a mock MCP client with a nested 'memory' object."""
    mock_memory = MagicMock()
    mock_memory.create_entity = AsyncMock()

    client = MagicMock()
    client.memory = mock_memory
    return client

@pytest.fixture
def agent_config():
    """Provides a standard agent configuration for testing."""
    return {
        "scoring_weights": {
            'industry_match': 0.4,
            'objective_alignment': 0.3,
            'stakeholder_fit': 0.1,
            'complexity_match': 0.1,
            'value_driver_alignment': 0.1,
        },
        "template_database": {
            "tech_growth_case": {
                "name": "Tech Growth Business Case",
                "description": "For scaling a technology product.",
                "industries": ["technology", "financial_services"],
                "objectives": ["market_expansion", "product_launch"],
                "stakeholders": ["cto", "cfo", "product_manager"],
                "complexity": ["medium", "high"],
                "value_drivers": ["revenue_growth", "market_share"],
                "sections": ["executive_summary", "market_analysis", "product_roadmap"]
            },
            "cost_reduction_ops": {
                "name": "Operational Cost Reduction Plan",
                "description": "For improving operational efficiency.",
                "industries": ["manufacturing", "retail", "energy"],
                "objectives": ["cost_reduction", "efficiency_improvement"],
                "stakeholders": ["coo", "operations_manager"],
                "complexity": ["low", "medium"],
                "value_drivers": ["cost_savings", "process_optimization"],
                "sections": ["problem_statement", "proposed_solution", "cost_benefit_analysis"]
            }
        }
    }

@pytest.fixture
def template_agent(mock_mcp_client, agent_config):
    """Provides a configured instance of the TemplateSelectorAgent."""
    return TemplateSelectorAgent(
        agent_id="test-selector-agent-001",
        mcp_client=mock_mcp_client,
        config=agent_config
    )

# --- Test Cases ---

@pytest.mark.asyncio
async def test_initialization(template_agent):
    """Tests that the agent initializes correctly and loads its configuration."""
    assert template_agent.agent_id == "test-selector-agent-001"
    assert len(template_agent.template_database) == 2
    assert "tech_growth_case" in template_agent.template_database
    assert template_agent.scoring_weights['industry_match'] == 0.4

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_input, error_message", [
    ({}, "business_objective"), # Missing all required fields
    ({"industry": "technology"}, "business_objective"), # Missing one required field
    ({"business_objective": "Expand", "industry": "invalid_industry"}, "Input should be 'healthcare'"), # Invalid enum
])
async def test_input_validation_failure(template_agent, invalid_input, error_message):
    """Tests that the agent fails gracefully with invalid Pydantic inputs."""
    result = await template_agent.execute(invalid_input)
    assert result.status == AgentStatus.FAILED
    assert "Input validation error" in result.data["message"]
    assert error_message in result.data["message"]

@pytest.mark.asyncio
async def test_successful_selection_perfect_match(template_agent):
    """Tests a scenario where the input is a perfect match for a template."""
    perfect_input = {
        "business_objective": "product_launch",
        "industry": IndustryType.TECHNOLOGY,
        "stakeholder_types": ["cto", "cfo"],
        "complexity_level": ComplexityLevel.HIGH,
        "primary_value_drivers": ["revenue_growth"]
    }
    result = await template_agent.execute(perfect_input)
    assert result.status == AgentStatus.COMPLETED

    data = TemplateSelectorResult(**result.data)
    assert data.selected_template.template_id == "tech_growth_case"
    assert data.selected_template.overall_score > 0.9 # Should be very high
    assert data.selected_template.confidence_score == 1.0 # All optional fields provided

@pytest.mark.asyncio
async def test_selection_with_partial_input(template_agent):
    """Tests selection with only required inputs, expecting a lower confidence score."""
    partial_input = {
        "business_objective": "cost_reduction",
        "industry": IndustryType.MANUFACTURING,
    }
    result = await template_agent.execute(partial_input)
    assert result.status == AgentStatus.COMPLETED

    data = TemplateSelectorResult(**result.data)
    assert data.selected_template.template_id == "cost_reduction_ops"
    assert data.selected_template.confidence_score < 0.1 # No optional fields provided
    assert data.selected_template.overall_score < data.selected_template.match_score

@pytest.mark.asyncio
async def test_no_suitable_template_found(template_agent):
    """Tests that the agent returns a failure when no templates match the core criteria."""
    # Temporarily remove templates to simulate this scenario
    template_agent.template_database = {}
    no_match_input = {
        "business_objective": "something_unrelated",
        "industry": IndustryType.EDUCATION,
    }
    result = await template_agent.execute(no_match_input)
    assert result.status == AgentStatus.FAILED
    assert "No suitable templates found" in result.data["message"]

@pytest.mark.asyncio
async def test_mcp_audit_recording(template_agent, mock_mcp_client):
    """Tests that a successful execution correctly records an audit trail to MCP."""
    valid_input = {
        "business_objective": "product_launch",
        "industry": IndustryType.TECHNOLOGY,
    }
    await template_agent.execute(valid_input)

    mock_mcp_client.memory.create_entity.assert_called_once()
    mock_mcp_client.create_entities.assert_called_once()
    # Get the first argument (list of entities) from the call
    entity_list = mock_mcp_client.create_entities.call_args.args[0]
    assert len(entity_list) == 1
    entity = entity_list[0]
    assert entity.entity_type == "template_selection_analysis"
    assert entity.data["selected_template"]["template_name"] == "Tech Growth Business Case"
    assert entity.data["input_data"]["industry"] == "technology"
    assert entity.data["input_data"]["business_objective"] == "product_launch"

@pytest.mark.asyncio
async def test_graceful_handling_of_unexpected_error(template_agent):
    """Tests that the agent returns a generic failure on an unexpected internal error."""
    # Mock an internal method to raise an unhandled exception
    template_agent._get_template_recommendations = MagicMock(side_effect=Exception("Internal DB Error"))

    valid_input = {
        "business_objective": "product_launch",
        "industry": IndustryType.TECHNOLOGY,
    }
    result = await template_agent.execute(valid_input)

    assert result.status == AgentStatus.FAILED
    assert "An unexpected error occurred" in result.data["message"]
    assert "Internal DB Error" in result.data["message"]
