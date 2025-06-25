import pytest
import yaml
from unittest.mock import MagicMock

from agents.template_selector.main import TemplateSelectorAgent, TemplateSelectorInput
from agents.core.agent_base import AgentStatus


@pytest.fixture
def agent_config():
    """Loads the agent's configuration from the YAML file."""
    with open("agents/template_selector_agent.yaml", "r") as f:
        return yaml.safe_load(f)["config"]


class TestTemplateSelectorAgent:
    """Test suite for the TemplateSelectorAgent."""

    def setup_method(self):
        """Initializes the agent and mock MCP client for each test."""
        with open("agents/template_selector_agent.yaml", "r") as f:
            config = yaml.safe_load(f)

        self.config = config['config']
        self.mock_mcp_client = MagicMock()
        self.agent = TemplateSelectorAgent(
            agent_id="test_template_selector",
            mcp_client=self.mock_mcp_client,
            config=self.config
        )

    def test_initialization(self):
        """Tests that the agent initializes correctly."""
        assert self.agent is not None
        assert self.agent.agent_id == "test_template_selector"
        assert len(self.agent.template_database) > 0, "Template database should be loaded"
        assert "standard_roi" in self.agent.template_database

    @pytest.mark.asyncio
    async def test_perfect_match_selection(self):
        """Tests the agent's ability to select the correct template with a perfect match."""
        perfect_input = {
            "business_objective": "cost_reduction",
            "industry": "technology",
            "stakeholder_types": ["financial_buyer", "executive", "operations"],
            "complexity_level": "medium",
            "primary_value_drivers": ["cost_savings", "productivity", "automation", "efficiency"]
        }
        result = await self.agent.execute(perfect_input)
        assert result.status == AgentStatus.COMPLETED
        selected_template = result.data['selected_template']
        assert selected_template['template_id'] == "standard_roi"
        assert selected_template['match_score'] == pytest.approx(1.0)
        assert selected_template['confidence_score'] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_partial_match_selection(self):
        """Tests selection with a partial match, expecting the best fit."""
        partial_input = {
            "business_objective": "revenue_growth",
            "industry": "retail",
            "complexity_level": "high"
        }
        result = await self.agent.execute(partial_input)
        assert result.status == AgentStatus.COMPLETED
        selected_template = result.data['selected_template']
        assert selected_template['template_id'] == "revenue_growth"
        assert selected_template['match_score'] < 1.0
        assert selected_template['confidence_score'] < 1.0

    @pytest.mark.asyncio
    async def test_invalid_input_handling(self):
        """Tests that the agent handles invalid input gracefully."""
        invalid_payload = {"industry": "technology"}
        result = await self.agent.execute(invalid_payload)
        assert result.status == AgentStatus.FAILED
        assert "validation error" in result.data["message"].lower()

    def test_confidence_score_logic(self):
        """Unit tests the confidence score calculation based on provided optional fields."""
        # Case 1: All optional fields provided -> score should be 1.0
        full_input = TemplateSelectorInput(**{
            "business_objective": "test", "industry": "generic", "stakeholder_types": ["a"],
            "complexity_level": "low", "primary_value_drivers": ["b"]
        })
        score, _ = self.agent._calculate_confidence_score(full_input)
        assert score == pytest.approx(1.0)

        # Case 2: No optional fields provided -> score should be 0.0
        partial_input_none = TemplateSelectorInput(**{"business_objective": "test", "industry": "generic"})
        score, _ = self.agent._calculate_confidence_score(partial_input_none)
        assert score == pytest.approx(0.0)

        # Case 3: One of three optional fields provided -> score should be 1/3
        partial_input_one = TemplateSelectorInput(**{
            "business_objective": "test", "industry": "generic", "complexity_level": "low"
        })
        expected_score = 1 / 3.0
        score, _ = self.agent._calculate_confidence_score(partial_input_one)
        assert score == pytest.approx(expected_score)

    def test_scoring_logic(self):
        """Unit tests the template scoring logic based on weighted component scores."""
        input_model = TemplateSelectorInput(**{
            "business_objective": "cost_reduction",
            "industry": "technology",
            "stakeholder_types": ["executive"],
            "complexity_level": "high",
            "primary_value_drivers": ["efficiency"]
        })
        template = self.agent.template_database["standard_roi"]
        weights = self.agent.scoring_weights

        # Calculate expected component scores based on the new logic
        industry_score = 1.0
        objective_score = 1.0
        # 1 of 3 stakeholders match
        stakeholder_score = 1 / len(template.stakeholders)
        # 'high' complexity is a match
        complexity_score = 1.0
        # 1 of 4 value drivers match
        value_driver_score = 1 / len(template.value_drivers)

        expected_total_score = (
            weights['industry_match'] * industry_score +
            weights['objective_alignment'] * objective_score +
            weights['stakeholder_fit'] * stakeholder_score +
            weights['complexity_match'] * complexity_score +
            weights['value_driver_alignment'] * value_driver_score
        )

        # Expected: 0.25*1 + 0.30*1 + 0.15*(1/3) + 0.15*1 + 0.15*(1/4) = 0.7875
        assert expected_total_score == pytest.approx(0.7875)

        score, _ = self.agent._calculate_match_score(template, input_model)
        assert score == pytest.approx(expected_total_score)
