import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.intake_assistant.main import IntakeAssistantAgent
from agents.core.agent_base import AgentStatus
from agents.utils.validation import ValidationResult
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def mock_mcp_client():
    """Fixture for a mock MCPClient."""
    client = MagicMock()
    client.create_entities = AsyncMock(return_value=None)
    client.search_nodes = AsyncMock(return_value=[])
    return client

@pytest.fixture
def intake_agent(mock_mcp_client):
    """Fixture for an IntakeAssistantAgent instance."""
    # Create agent with mock_mcp_client properly injected
    agent = IntakeAssistantAgent(agent_id="test-intake-agent", mcp_client=mock_mcp_client, config={})
    # Reset any mocks to ensure clean state between tests
    mock_mcp_client.search_nodes.reset_mock()
    mock_mcp_client.create_entities.reset_mock()
    return agent

@pytest.mark.asyncio
async def test_successful_intake(intake_agent, mock_mcp_client):
    """Test the successful processing of a valid project intake."""
    inputs = {
        'project_name': 'New CRM Integration',
        'description': 'Integrating our new CRM with the sales pipeline.',
        'business_objective': 'Improve customer relationship management efficiency',
        'industry': 'technology',
        'department': 'sales',
        'goals': ['Improve lead tracking', 'Automate sales reports'],
        'success_criteria': ['Increase lead conversion by 15%', 'Reduce manual reporting by 50%'],
        'stakeholders': [
            {'name': 'John Doe', 'role': 'sponsor'},
            {'name': 'Jane Smith', 'role': 'project_manager'}
        ],
        'budget_range': '50k_to_250k',
        'timeline': 'quarterly',
        'urgency': 'medium',
        'expected_participants': 10,
        'geographic_scope': 'national',
        'regulatory_requirements': []
    }
    
    # Mock validate_inputs to always return valid for this test
    intake_agent.validate_inputs = AsyncMock(return_value=ValidationResult(is_valid=True, errors=[]))

    result = await intake_agent.execute(inputs)

    assert result.status == AgentStatus.COMPLETED
    assert 'project_data' in result.data
    assert 'recommendations' in result.data
    assert 'analysis_summary' in result.data
    assert result.data['metadata']['mcp_storage_success'] is True

    mock_mcp_client.create_entities.assert_called_once()
    knowledge_entity = mock_mcp_client.create_entities.call_args[0][0][0]
    assert knowledge_entity.title == "Project Intake: New CRM Integration"
    assert knowledge_entity.metadata['project_id'].startswith('proj_')
    assert knowledge_entity.metadata['industry'] == 'technology'

@pytest.mark.asyncio
async def test_input_validation_failure(intake_agent, mock_mcp_client):
    """Test that the agent fails if input validation fails."""
    inputs = {
        'project_name': 'a',
        'description': 'a',
        'goals': []
    } # These inputs will fail validation
    
    # Do not mock validate_inputs here, let the actual validation run

    result = await intake_agent.execute(inputs)

    assert result.status == AgentStatus.FAILED
    assert 'Input validation failed' in result.data['error']
    expected_errors = [
        "Field 'project_name' must be at least 3 characters long",
        "Project name must be at least 5 characters long.",
        "Required field 'business_objective' is missing or null",
        "Field 'description' must be at least 20 characters long",
        "Goals cannot be an empty list if provided."
    ]
    assert all(err in result.data['details'] for err in expected_errors)
    mock_mcp_client.create_entities.assert_not_called()

@pytest.mark.asyncio
async def test_mcp_storage_failure(intake_agent, mock_mcp_client, caplog):
    """Test that the agent handles MCP storage failures gracefully."""
    inputs = {
        'project_name': 'Project for MCP Failure',
        'description': 'This project will cause MCP storage to fail.',
        'business_objective': 'Test MCP error handling',
        'industry': 'technology',
        'department': 'it',
        'goals': ['Ensure robustness'],
        'success_criteria': ['No data loss'],
        'stakeholders': [{'name': 'Test User', 'role': 'sponsor'}],
        'budget_range': 'under_50k',
        'timeline': 'quarterly',
        'urgency': 'low',
        'expected_participants': 2,
        'geographic_scope': 'local',
        'regulatory_requirements': []
    }
    
    # Mock validate_inputs to always return valid for this test
    intake_agent.validate_inputs = AsyncMock(return_value=ValidationResult(is_valid=True, errors=[]))

    mock_mcp_client.create_entities.side_effect = Exception("MCP connection error")

    with caplog.at_level(logging.ERROR):
        result = await intake_agent.execute(inputs)

    assert result.status == AgentStatus.FAILED
    assert 'Failed to store project data in memory' in result.data['error']
    assert 'MCP connection error' in result.data['details']
    assert 'MCP storage failed' in result.error_details
    assert "AUDIT: Failed to create KnowledgeEntity" in caplog.text
    assert "MCP connection error" in caplog.text

@pytest.mark.asyncio
async def test_check_existing_projects_found(intake_agent, mock_mcp_client):
    """Test _check_existing_projects when similar projects are found."""
    mock_mcp_client.search_nodes.return_value = [
        {'name': 'Existing New CRM Integration Project', 'observations': ['CRM integration for sales']},
        {'name': 'CRM Upgrade Initiative', 'observations': ['Upgrade existing CRM system']}
    ]
    intake_agent.mcp_client = mock_mcp_client
    intake_agent.validate_inputs = AsyncMock(return_value=ValidationResult(is_valid=True, errors=[]))
    intake_agent._check_existing_projects.cache_clear() # Clear the cache

    inputs = {
        'project_name': 'New CRM Integration',
        'description': 'Integrating our new CRM with the sales pipeline.',
        'business_objective': 'Improve customer relationship management efficiency',
        'industry': 'technology',
        'department': 'sales',
        'goals': ['Improve lead tracking', 'Automate sales reports'],
        'success_criteria': ['Increase lead conversion by 15%', 'Reduce manual reporting by 50%'],
        'stakeholders': [
            {'name': 'John Doe', 'role': 'sponsor'},
            {'name': 'Jane Smith', 'role': 'project_manager'}
        ],
        'budget_range': '50k_to_250k',
        'timeline': 'quarterly',
        'urgency': 'medium',
        'expected_participants': 10,
        'geographic_scope': 'national',
        'regulatory_requirements': []
    }

    result = await intake_agent.execute(inputs)

    assert result.status == AgentStatus.FAILED
    assert "Similar project name already exists" in result.data['error']
    # Ensure search_nodes was called with the project name
    assert mock_mcp_client.search_nodes.call_count >= 1
    assert mock_mcp_client.search_nodes.call_args.kwargs.get('query') == 'New CRM Integration'

@pytest.mark.asyncio
async def test_check_existing_projects_not_found(intake_agent, mock_mcp_client):
    """Test _check_existing_projects when no similar projects are found."""
    mock_mcp_client.search_nodes.return_value = [] # No existing projects
    intake_agent.mcp_client = mock_mcp_client
    intake_agent.validate_inputs = AsyncMock(return_value=ValidationResult(is_valid=True, errors=[]))

    inputs = {
        'project_name': 'Truly Unique Project',
        'description': 'A project that has no duplicates.',
        'business_objective': 'Achieve uniqueness and originality in all aspects',
        'industry': 'technology',
        'department': 'it',
        'goals': ['Be original'],
        'success_criteria': ['Pass uniqueness test'],
        'stakeholders': [{'name': 'Solo', 'role': 'sponsor'}],
        'budget_range': 'under_50k',
        'timeline': 'quarterly',
        'urgency': 'low',
        'expected_participants': 1,
        'geographic_scope': 'local',
        'regulatory_requirements': []
    }

    result = await intake_agent.execute(inputs)

    assert result.status == AgentStatus.COMPLETED # Should succeed as no duplicates are found


@pytest.mark.asyncio
async def test_mcp_audit_logging_success(intake_agent, mock_mcp_client, caplog):
    """Test that audit logs are generated for successful MCP write operations."""
    inputs = {
        'project_name': 'Audit Log Test Project',
        'description': 'Testing successful audit logging for MCP.',
        'business_objective': 'Verify logging',
        'industry': 'technology',
        'department': 'it',
        'goals': ['Log everything'],
        'success_criteria': ['Logs are perfect'],
        'stakeholders': [{'name': 'Logger', 'role': 'sponsor'}],
        'budget_range': 'under_50k',
        'timeline': 'quarterly',
        'urgency': 'low',
        'expected_participants': 1,
        'geographic_scope': 'local',
        'regulatory_requirements': []
    }
    
    intake_agent.validate_inputs = AsyncMock(return_value=ValidationResult(is_valid=True, errors=[]))

    with caplog.at_level(logging.INFO):
        result = await intake_agent.execute(inputs)

    assert result.status == AgentStatus.COMPLETED
    assert "AUDIT: Attempting to create KnowledgeEntity" in caplog.text
    assert "AUDIT: Successfully created KnowledgeEntity" in caplog.text
    assert f"Successfully stored project intake for {result.data['project_data']['project_id']}" in caplog.text

@pytest.mark.asyncio
async def test_overall_unexpected_error_handling(intake_agent, caplog):
    """Test that the agent handles unexpected errors gracefully at the top level."""
    # Simulate an unexpected error by making a method raise an exception
    intake_agent._classify_project_type = MagicMock(side_effect=Exception("Unexpected classification error"))

    inputs = {
        'project_name': 'Error Test',
        'description': 'This project will trigger an unexpected error.',
        'business_objective': 'Handle errors',
        'industry': 'technology',
        'department': 'it',
        'goals': ['Catch all exceptions'],
        'success_criteria': ['No crashes'],
        'stakeholders': [{'name': 'Error Handler', 'role': 'sponsor'}],
        'budget_range': 'under_50k',
        'timeline': 'quarterly',
        'urgency': 'low',
        'expected_participants': 1,
        'geographic_scope': 'local',
        'regulatory_requirements': []
    }

    # Mock validate_inputs to allow the process to proceed to the error point
    intake_agent.validate_inputs = AsyncMock(return_value=ValidationResult(is_valid=True, errors=[]))

    with caplog.at_level(logging.ERROR):
        result = await intake_agent.execute(inputs)

    assert result.status == AgentStatus.FAILED
    assert "An error occurred during core processing for agent test-intake-agent" in result.data['error']
    assert "Unexpected classification error" in result.data['error']
    assert "An error occurred during core processing for agent test-intake-agent: Unexpected classification error" in caplog.text
    assert "ERROR" in caplog.text

@pytest.mark.asyncio
async def test_structure_data_normalization(intake_agent):
    """Test that _structure_data correctly normalizes input data."""
    inputs = {
        'project_name': 'Test Project',
        'description': 'A test description.',
        'goals': ['Goal 1', None, 'Goal 2'],  # Mixed list with None
        'success_criteria': 'Single criteria string', # String instead of list
        'budget_range': '100k_to_500k'
    }

    # Call the internal method directly for focused testing
    structured_data = intake_agent._structure_data(inputs)

    assert isinstance(structured_data['goals'], list)
    assert structured_data['goals'] == ['Goal 1', 'Goal 2'] # None should be filtered out

    assert isinstance(structured_data['success_criteria'], list)
    assert structured_data['success_criteria'] == ['Single criteria string'] # Should be converted to list

    assert structured_data['project_name'] == 'Test Project'
    assert structured_data['budget_range'] == '100k_to_500k'

    # Test with empty or missing fields
    inputs_empty = {
        'project_name': 'Empty Test',
        'description': 'Another test description.'
    }
    structured_data_empty = intake_agent._structure_data(inputs_empty)
    assert structured_data_empty['goals'] == []
    assert structured_data_empty['success_criteria'] == []

@pytest.mark.asyncio
async def test_structure_data_type_conversion(intake_agent):
    """Test that _structure_data correctly converts non-list inputs to lists of strings."""
    inputs_conversion = {
        'project_name': 'Conversion Test',
        'description': 'This tests type conversion.',
        'goals': 123,  # Non-list input
        'success_criteria': {'key': 'value'} # Another non-list input
    }

    structured_data = intake_agent._structure_data(inputs_conversion)

    assert isinstance(structured_data['goals'], list)
    assert structured_data['goals'] == ['123']

    assert isinstance(structured_data['success_criteria'], list)
    assert structured_data['success_criteria'] == ["{'key': 'value'}"]
