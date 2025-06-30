import pytest
from agents.proposal_generator.main import ProposalGeneratorAgent
from agents.core.agent_base import AgentStatus


@pytest.fixture
def proposal_agent():
    """Fixture for a ProposalGeneratorAgent instance."""
    # Mock MCPClient and config as needed for more complex tests
    return ProposalGeneratorAgent(agent_id="test_proposal_agent", mcp_client=None, config={})


@pytest.mark.asyncio
async def test_generate_markdown_proposal(proposal_agent):
    """Test successful generation of a markdown proposal."""
    test_input = {
        "business_objective": "Test Objective",
        "value_drivers": [{"driver": "test"}],
        "roi_analysis": {"roi": "150%"},
        "risk_analysis": {"risk": "low"},
        "output_format": "markdown",
    }
    result = await proposal_agent.execute(test_input)
    assert result.status == AgentStatus.COMPLETED
    assert "# Business Proposal" in result.data["proposal"]


@pytest.mark.asyncio
async def test_input_validation_failure(proposal_agent):
    """Test that the agent fails with invalid input."""
    test_input = {"bad_input": "test"}  # Missing required fields
    result = await proposal_agent.execute(test_input)
    assert result.status == AgentStatus.FAILED
    assert "Invalid input" in result.data["message"]
