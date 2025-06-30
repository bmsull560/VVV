"""
Tests for the Report Builder Agent.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.report_builder.main import ReportBuilderAgent, ReportFormat, ReportTemplate
from agents.core.agent_base import AgentStatus

@pytest.fixture
def mock_mcp_client():
    """Fixture for a mock MCPClient."""
    client = MagicMock()
    client.get_entity = AsyncMock(return_value=None)
    client.get_workflow = AsyncMock(return_value=None)
    client.store_memory = AsyncMock(return_value="test_entity_id")
    return client

@pytest.fixture
def report_builder_agent(mock_mcp_client):
    """Fixture for a ReportBuilderAgent instance."""
    agent = ReportBuilderAgent(agent_id="test-report-builder", mcp_client=mock_mcp_client, config={})
    return agent

@pytest.mark.asyncio
async def test_basic_report_generation(report_builder_agent):
    """Test basic report generation with minimal inputs."""
    inputs = {
        'report_type': 'business_case',
        'data_sources': [
            {
                'type': 'direct',
                'name': 'test_data',
                'data': {
                    'project_name': 'Test Project',
                    'roi_metrics': {
                        'roi_percentage': 150,
                        'payback_period_months': 12,
                        'total_benefits': 500000,
                        'total_costs': 200000
                    }
                }
            }
        ],
        'output_format': 'json',
        'template': 'executive_summary'
    }
    
    result = await report_builder_agent.execute(inputs)
    
    assert result.status == AgentStatus.COMPLETED
    assert 'report_id' in result.data
    assert 'report' in result.data
    assert result.data['report']['format'] == 'json'
    assert result.data['report']['title'] == 'Business Value Analysis Report'
    assert 'sections' in result.data['report']
    assert len(result.data['report']['sections']) > 0

@pytest.mark.asyncio
async def test_input_validation_failure(report_builder_agent):
    """Test that the agent fails if input validation fails."""
    inputs = {
        'report_type': 'invalid_type',  # Invalid report type
        'data_sources': []  # Empty data sources
    }
    
    result = await report_builder_agent.execute(inputs)
    
    assert result.status == AgentStatus.FAILED
    assert 'error' in result.data
    assert 'Validation failed' in result.data['error']

@pytest.mark.asyncio
async def test_html_report_generation(report_builder_agent):
    """Test HTML report generation."""
    inputs = {
        'report_type': 'roi_analysis',
        'data_sources': [
            {
                'type': 'direct',
                'name': 'test_data',
                'data': {
                    'roi_summary': {
                        'roi_percentage': 200,
                        'payback_period_months': 6,
                        'total_annual_value': 300000,
                        'investment_amount': 100000
                    }
                }
            }
        ],
        'output_format': 'html',
        'template': 'financial_dashboard',
        'include_executive_summary': True
    }
    
    result = await report_builder_agent.execute(inputs)
    
    assert result.status == AgentStatus.COMPLETED
    assert result.data['report']['format'] == 'html'
    assert '<!DOCTYPE html>' in result.data['report']['content']
    assert 'Executive Summary' in result.data['report']['content']

@pytest.mark.asyncio
async def test_markdown_report_generation(report_builder_agent):
    """Test Markdown report generation."""
    inputs = {
        'report_type': 'risk_assessment',
        'data_sources': [
            {
                'type': 'direct',
                'name': 'test_data',
                'data': {
                    'risks': [
                        {
                            'name': 'Technical Risk',
                            'category': 'technical',
                            'probability': 'medium',
                            'impact': 'high',
                            'description': 'Risk description'
                        }
                    ]
                }
            }
        ],
        'output_format': 'markdown',
        'template': 'detailed_analysis'
    }
    
    result = await report_builder_agent.execute(inputs)
    
    assert result.status == AgentStatus.COMPLETED
    assert result.data['report']['format'] == 'markdown'
    assert '# ' in result.data['report']['content']  # Markdown heading
    assert 'Risk Assessment' in result.data['report']['content']

@pytest.mark.asyncio
async def test_report_with_charts(report_builder_agent):
    """Test report generation with charts."""
    inputs = {
        'report_type': 'value_driver_analysis',
        'data_sources': [
            {
                'type': 'direct',
                'name': 'test_data',
                'data': {
                    'value_drivers': [
                        {'name': 'Cost Reduction', 'value': 100000},
                        {'name': 'Revenue Growth', 'value': 150000},
                        {'name': 'Productivity Improvement', 'value': 75000}
                    ]
                }
            }
        ],
        'output_format': 'json',
        'template': 'executive_summary',
        'charts': [
            {
                'id': 'value_drivers_chart',
                'type': 'bar',
                'title': 'Value Drivers',
                'data_source': 'test_data',
                'data_path': 'value_drivers'
            }
        ]
    }
    
    result = await report_builder_agent.execute(inputs)
    
    assert result.status == AgentStatus.COMPLETED
    assert 'charts' in result.data['report']
    assert len(result.data['report']['charts']) > 0

@pytest.mark.asyncio
async def test_custom_template(report_builder_agent):
    """Test report generation with custom template."""
    inputs = {
        'report_type': 'custom',
        'data_sources': [
            {
                'type': 'direct',
                'name': 'test_data',
                'data': {
                    'custom_data': 'Custom content'
                }
            }
        ],
        'output_format': 'json',
        'template': 'custom',
        'sections': ['executive_summary', 'findings', 'recommendations'],
        'custom_styles': {
            'color_scheme': 'custom_scheme',
            'font_family': 'Roboto, sans-serif'
        }
    }
    
    result = await report_builder_agent.execute(inputs)
    
    assert result.status == AgentStatus.COMPLETED
    assert result.data['report']['template'] == 'custom'
    assert len(result.data['report']['sections']) == 3
    assert 'styles' in result.data['report']
    assert result.data['report']['styles']['color_scheme'] == 'custom_scheme'

@pytest.mark.asyncio
async def test_mcp_data_source_error_handling(report_builder_agent, mock_mcp_client):
    """Test error handling for MCP data sources."""
    # Mock MCP client to raise an exception
    mock_mcp_client.get_entity.side_effect = Exception("MCP error")
    
    inputs = {
        'report_type': 'business_case',
        'data_sources': [
            {
                'type': 'mcp_entity',
                'source_id': 'non_existent_entity'
            }
        ],
        'output_format': 'json',
        'template': 'executive_summary'
    }
    
    result = await report_builder_agent.execute(inputs)
    
    # Should still complete but with error in data
    assert result.status == AgentStatus.COMPLETED
    assert 'report' in result.data
    assert 'non_existent_entity' in result.data['report']['sections'][0]['content']
    assert 'error' in result.data['report']['sections'][0]['content'].lower()

@pytest.mark.asyncio
async def test_report_caching(report_builder_agent):
    """Test report caching functionality."""
    inputs = {
        'report_type': 'business_case',
        'data_sources': [
            {
                'type': 'direct',
                'name': 'test_data',
                'data': {
                    'project_name': 'Cache Test Project'
                }
            }
        ],
        'output_format': 'json',
        'template': 'executive_summary'
    }
    
    # First execution should generate a new report
    result1 = await report_builder_agent.execute(inputs)
    assert result1.status == AgentStatus.COMPLETED
    assert 'cached' not in result1.data or not result1.data['cached']
    
    # Second execution with same inputs should use cached report
    result2 = await report_builder_agent.execute(inputs)
    assert result2.status == AgentStatus.COMPLETED
    assert 'cached' in result2.data and result2.data['cached']
    assert result2.data['report_id'] != result1.data['report_id']  # IDs should be different due to timestamp
    
    # Execution with different inputs should generate a new report
    inputs['template'] = 'detailed_analysis'
    result3 = await report_builder_agent.execute(inputs)
    assert result3.status == AgentStatus.COMPLETED
    assert 'cached' not in result3.data or not result3.data['cached']