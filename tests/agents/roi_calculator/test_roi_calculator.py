import pytest
from agents.roi_calculator.main import ROICalculatorAgent
from agents.core.agent_base import AgentStatus

@pytest.fixture
def agent():
    """Fixture to provide a ROICalculatorAgent instance for testing."""
    return ROICalculatorAgent(agent_id="test-roi-agent", mcp_client=None, config={})

@pytest.mark.asyncio
async def test_successful_roi_calculation(agent):
    """Test a standard successful ROI calculation."""
    inputs = {'investment': 1000, 'gain': 1500}
    result = await agent.execute(inputs)
    assert result.status == AgentStatus.COMPLETED
    assert result.data['roi_percentage'] == 50.0

@pytest.mark.asyncio
async def test_zero_investment(agent):
    """Test that an investment of zero results in a failure."""
    inputs = {'investment': 0, 'gain': 100}
    result = await agent.execute(inputs)
    assert result.status == AgentStatus.FAILED
    assert result.data['error'] == 'Investment must be a positive number.'

@pytest.mark.asyncio
async def test_negative_investment(agent):
    """Test that a negative investment results in a failure."""
    inputs = {'investment': -100, 'gain': 100}
    result = await agent.execute(inputs)
    assert result.status == AgentStatus.FAILED
    assert result.data['error'] == 'Investment must be a positive number.'

@pytest.mark.asyncio
async def test_non_numeric_input(agent):
    """Test that non-numeric inputs result in a failure."""
    inputs = {'investment': 'one thousand', 'gain': 1500}
    result = await agent.execute(inputs)
    assert result.status == AgentStatus.FAILED
    assert "'investment' and 'gain' must be provided and must be numbers." in result.data['error']

@pytest.mark.asyncio
async def test_invalid_input_type(agent):
    """Test that the agent raises a TypeError for non-dictionary inputs."""
    with pytest.raises(TypeError):
        await agent.execute("not a dict")

