"""
MCP (Model Context Protocol) compliance validation tests.

This module validates that all agents properly implement MCP standards
for memory operations, entity storage, and cross-agent communication.
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from agents.intake_assistant.main import IntakeAssistantAgent
from agents.value_driver.main import ValueDriverAgent
from agents.roi_calculator.main import ROICalculatorAgent
from agents.risk_mitigation.main import RiskMitigationAgent
from agents.sensitivity_analysis.main import SensitivityAnalysisAgent
from agents.analytics_aggregator.main import AnalyticsAggregatorAgent
from agents.database_connector.main import DatabaseConnectorAgent
from agents.data_correlator.main import DataCorrelatorAgent
from agents.core.agent_base import AgentResult, AgentStatus
from memory.types import KnowledgeEntity


class TestMCPCompliance:
    """Test MCP standard compliance across all agents."""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Mock MCP client with full compliance tracking."""
        client = Mock()
        
        # Track all MCP operations
        client.operations_log = []
        
        def log_operation(op_type, *args, **kwargs):
            client.operations_log.append({
                'operation': op_type,
                'timestamp': datetime.utcnow().isoformat(),
                'args': args,
                'kwargs': kwargs
            })
        
        # Mock MCP operations with logging
        client.store_entity = AsyncMock(side_effect=lambda *args, **kwargs: log_operation('store_entity', *args, **kwargs))
        client.search_entities = AsyncMock(side_effect=lambda *args, **kwargs: log_operation('search_entities', *args, **kwargs) or [])
        client.get_entity = AsyncMock(side_effect=lambda *args, **kwargs: log_operation('get_entity', *args, **kwargs))
        client.update_entity = AsyncMock(side_effect=lambda *args, **kwargs: log_operation('update_entity', *args, **kwargs))
        client.delete_entity = AsyncMock(side_effect=lambda *args, **kwargs: log_operation('delete_entity', *args, **kwargs))
        client.list_entities = AsyncMock(side_effect=lambda *args, **kwargs: log_operation('list_entities', *args, **kwargs) or [])
        
        return client
    
    @pytest.fixture
    def base_config(self):
        """Base agent configuration."""
        return {
            'agent_id': 'mcp_test_agent',
            'timeout_seconds': 30,
            'retry_attempts': 3,
            'input_validation': {}
        }
    
    @pytest.mark.asyncio
    async def test_entity_storage_compliance(self, mock_mcp_client, base_config):
        """Test that all agents properly store entities according to MCP standards."""
        
        # Test data for different agents
        test_cases = [
            {
                'agent_class': IntakeAssistantAgent,
                'input': {
                    'project_name': 'MCP Test Project',
                    'description': 'Testing MCP compliance',
                    'industry': 'technology',
                    'department': 'it',
                    'stakeholders': [{'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'}],
                    'goals': ['Test MCP storage'],
                    'success_criteria': ['Entity stored correctly'],
                    'budget': 100000,
                    'timeline': 6,
                    'urgency': 'medium',
                    'expected_participants': 5
                },
                'expected_entity_type': 'project_intake'
            },
            {
                'agent_class': ValueDriverAgent,
                'input': {
                    'user_query': 'Test value driver analysis for MCP compliance',
                    'analysis_type': 'comprehensive',
                    'business_context': {'industry': 'technology', 'company_size': 'medium'}
                },
                'expected_entity_type': 'value_analysis'
            },
            {
                'agent_class': RiskMitigationAgent,
                'input': {
                    'project_details': {
                        'name': 'MCP Test Project',
                        'budget': 100000,
                        'timeline': 6,
                        'expected_value': 150000
                    },
                    'risks': [
                        {
                            'name': 'Test Risk',
                            'category': 'technical',
                            'probability': 'medium',
                            'impact': 'low'
                        }
                    ],
                    'risk_tolerance': 'medium'
                },
                'expected_entity_type': 'risk_assessment'
            }
        ]
        
        for test_case in test_cases:
            # Create and execute agent
            agent = test_case['agent_class']('mcp_test', mock_mcp_client, base_config.copy())
            result = await agent.execute(test_case['input'])
            
            # Validate successful execution
            assert result.status == AgentStatus.SUCCESS, f"Agent {test_case['agent_class'].__name__} failed execution"
            
            # Validate MCP storage was called
            assert mock_mcp_client.store_entity.called, f"Agent {test_case['agent_class'].__name__} did not store entity"
            
            # Reset mock for next test
            mock_mcp_client.reset_mock()
    
    @pytest.mark.asyncio
    async def test_entity_structure_compliance(self, mock_mcp_client, base_config):
        """Test that stored entities comply with MCP structure requirements."""
        
        stored_entities = []
        
        def capture_entity(entity):
            stored_entities.append(entity)
            return AsyncMock()
        
        mock_mcp_client.store_entity.side_effect = capture_entity
        
        # Execute intake agent to capture entity structure
        agent = IntakeAssistantAgent('structure_test', mock_mcp_client, base_config.copy())
        
        test_input = {
            'project_name': 'Structure Test Project',
            'description': 'Testing entity structure compliance',
            'industry': 'technology',
            'department': 'it',
            'stakeholders': [{'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'}],
            'goals': ['Test structure'],
            'success_criteria': ['Valid structure'],
            'budget': 50000,
            'timeline': 3,
            'urgency': 'low',
            'expected_participants': 3
        }
        
        result = await agent.execute(test_input)
        assert result.status == AgentStatus.SUCCESS
        assert len(stored_entities) > 0
        
        # Validate entity structure
        entity = stored_entities[0]
        
        # Required MCP fields
        assert hasattr(entity, 'entity_id'), "Entity missing entity_id field"
        assert hasattr(entity, 'entity_type'), "Entity missing entity_type field"
        assert hasattr(entity, 'content'), "Entity missing content field"
        assert hasattr(entity, 'metadata'), "Entity missing metadata field"
        
        # Validate field types
        assert isinstance(entity.entity_id, str), "entity_id must be string"
        assert isinstance(entity.entity_type, str), "entity_type must be string"
        assert isinstance(entity.content, dict), "content must be dictionary"
        assert isinstance(entity.metadata, dict), "metadata must be dictionary"
        
        # Validate content structure
        assert 'project_name' in entity.content, "Content missing project_name"
        assert 'timestamp' in entity.metadata, "Metadata missing timestamp"
        assert 'agent_id' in entity.metadata, "Metadata missing agent_id"
    
    @pytest.mark.asyncio
    async def test_cross_agent_entity_access(self, mock_mcp_client, base_config):
        """Test that agents can properly access entities created by other agents."""
        
        # Simulate entity storage and retrieval
        entity_store = {}
        
        def store_entity_side_effect(entity):
            entity_store[entity.entity_id] = entity
            return AsyncMock()
        
        def get_entity_side_effect(entity_id):
            return entity_store.get(entity_id)
        
        def search_entities_side_effect(query):
            return [entity for entity in entity_store.values() 
                   if query.lower() in str(entity.content).lower()]
        
        mock_mcp_client.store_entity.side_effect = store_entity_side_effect
        mock_mcp_client.get_entity.side_effect = get_entity_side_effect
        mock_mcp_client.search_entities.side_effect = search_entities_side_effect
        
        # Step 1: Store entity with first agent
        intake_agent = IntakeAssistantAgent('cross_test_1', mock_mcp_client, base_config.copy())
        
        intake_input = {
            'project_name': 'Cross Agent Test',
            'description': 'Testing cross-agent entity access',
            'industry': 'technology',
            'department': 'it',
            'stakeholders': [{'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'}],
            'goals': ['Cross-agent access'],
            'success_criteria': ['Entities accessible'],
            'budget': 75000,
            'timeline': 4,
            'urgency': 'medium',
            'expected_participants': 4
        }
        
        intake_result = await intake_agent.execute(intake_input)
        assert intake_result.status == AgentStatus.SUCCESS
        
        project_id = intake_result.data['project_id']
        
        # Verify entity was stored
        assert len(entity_store) > 0
        assert project_id in entity_store
        
        # Step 2: Access entity with second agent (simulated)
        retrieved_entity = mock_mcp_client.get_entity(project_id)
        assert retrieved_entity is not None
        assert retrieved_entity.content['project_name'] == 'Cross Agent Test'
        
        # Step 3: Search for entities
        search_results = mock_mcp_client.search_entities('Cross Agent Test')
        assert len(search_results) > 0
        assert search_results[0].content['project_name'] == 'Cross Agent Test'
    
    @pytest.mark.asyncio
    async def test_mcp_operation_logging(self, mock_mcp_client, base_config):
        """Test that all MCP operations are properly logged."""
        
        # Execute multiple agents to generate MCP operations
        agents_and_inputs = [
            (IntakeAssistantAgent, {
                'project_name': 'Logging Test',
                'description': 'Test MCP operation logging',
                'industry': 'technology',
                'department': 'it',
                'stakeholders': [{'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'}],
                'goals': ['Test logging'],
                'success_criteria': ['Operations logged'],
                'budget': 25000,
                'timeline': 2,
                'urgency': 'low',
                'expected_participants': 2
            }),
            (ValueDriverAgent, {
                'user_query': 'Test logging for value driver analysis',
                'analysis_type': 'basic',
                'business_context': {'industry': 'technology', 'company_size': 'small'}
            })
        ]
        
        for agent_class, test_input in agents_and_inputs:
            agent = agent_class('logging_test', mock_mcp_client, base_config.copy())
            result = await agent.execute(test_input)
            assert result.status == AgentStatus.SUCCESS
        
        # Validate operations were logged
        assert len(mock_mcp_client.operations_log) > 0
        
        # Check for required operation types
        operations = [op['operation'] for op in mock_mcp_client.operations_log]
        assert 'store_entity' in operations, "store_entity operations should be logged"
        
        # Validate log structure
        for log_entry in mock_mcp_client.operations_log:
            assert 'operation' in log_entry
            assert 'timestamp' in log_entry
            assert isinstance(log_entry['timestamp'], str)
    
    @pytest.mark.asyncio
    async def test_entity_versioning_support(self, mock_mcp_client, base_config):
        """Test support for entity versioning in MCP operations."""
        
        stored_entities = []
        
        def capture_entity(entity):
            stored_entities.append(entity)
            return AsyncMock()
        
        mock_mcp_client.store_entity.side_effect = capture_entity
        mock_mcp_client.update_entity.side_effect = capture_entity
        
        # Store initial entity
        agent = IntakeAssistantAgent('version_test', mock_mcp_client, base_config.copy())
        
        initial_input = {
            'project_name': 'Versioning Test',
            'description': 'Initial version',
            'industry': 'technology',
            'department': 'it',
            'stakeholders': [{'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'}],
            'goals': ['Version control'],
            'success_criteria': ['Versions tracked'],
            'budget': 30000,
            'timeline': 2,
            'urgency': 'low',
            'expected_participants': 2
        }
        
        result = await agent.execute(initial_input)
        assert result.status == AgentStatus.SUCCESS
        assert len(stored_entities) > 0
        
        # Validate versioning metadata
        entity = stored_entities[0]
        assert 'version' in entity.metadata or 'created_at' in entity.metadata
        assert 'agent_id' in entity.metadata
    
    @pytest.mark.asyncio
    async def test_mcp_error_handling(self, mock_mcp_client, base_config):
        """Test proper error handling for MCP operations."""
        
        # Simulate MCP operation failures
        mock_mcp_client.store_entity.side_effect = Exception("MCP storage error")
        
        agent = IntakeAssistantAgent('error_test', mock_mcp_client, base_config.copy())
        
        test_input = {
            'project_name': 'Error Test',
            'description': 'Testing error handling',
            'industry': 'technology',
            'department': 'it',
            'stakeholders': [{'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'}],
            'goals': ['Error handling'],
            'success_criteria': ['Graceful failure'],
            'budget': 10000,
            'timeline': 1,
            'urgency': 'low',
            'expected_participants': 1
        }
        
        # Execute and expect graceful error handling
        result = await agent.execute(test_input)
        
        # Agent should handle MCP errors gracefully
        # Implementation may vary - either continue with local processing
        # or fail with appropriate error status
        assert result.status in [AgentStatus.SUCCESS, AgentStatus.ERROR]
        
        # If error, should have meaningful error information
        if result.status == AgentStatus.ERROR:
            assert 'error' in result.data or 'message' in result.data
    
    @pytest.mark.asyncio
    async def test_memory_consistency_validation(self, mock_mcp_client, base_config):
        """Test memory consistency across multiple agent interactions."""
        
        # Track entity operations for consistency validation
        entity_operations = []
        
        def track_store_operation(entity):
            entity_operations.append(('store', entity.entity_id, entity))
            return AsyncMock()
        
        def track_update_operation(entity):
            entity_operations.append(('update', entity.entity_id, entity))
            return AsyncMock()
        
        mock_mcp_client.store_entity.side_effect = track_store_operation
        mock_mcp_client.update_entity.side_effect = track_update_operation
        
        # Execute multiple agents in sequence
        agents = [
            (IntakeAssistantAgent, {
                'project_name': 'Consistency Test',
                'description': 'Testing memory consistency',
                'industry': 'technology',
                'department': 'it',
                'stakeholders': [{'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'}],
                'goals': ['Consistency'],
                'success_criteria': ['Memory consistent'],
                'budget': 40000,
                'timeline': 3,
                'urgency': 'medium',
                'expected_participants': 3
            }),
            (ValueDriverAgent, {
                'user_query': 'Analyze consistency test project value drivers',
                'analysis_type': 'comprehensive',
                'business_context': {'industry': 'technology', 'company_size': 'medium'}
            })
        ]
        
        for agent_class, test_input in agents:
            agent = agent_class('consistency_test', mock_mcp_client, base_config.copy())
            result = await agent.execute(test_input)
            assert result.status == AgentStatus.SUCCESS
        
        # Validate entity operations consistency
        assert len(entity_operations) > 0
        
        # Check for duplicate entity IDs (should not exist)
        entity_ids = [op[1] for op in entity_operations]
        assert len(entity_ids) == len(set(entity_ids)), "Duplicate entity IDs detected"
        
        # Validate entity content consistency
        for operation, entity_id, entity in entity_operations:
            assert entity.entity_id == entity_id
            assert len(entity.entity_id) > 0
            assert entity.entity_type in [
                'project_intake', 'value_analysis', 'roi_calculation', 
                'risk_assessment', 'sensitivity_analysis', 'analytics_aggregation'
            ]


class TestMCPPerformance:
    """Test MCP operation performance and scalability."""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Mock MCP client with performance tracking."""
        client = Mock()
        client.operation_times = []
        
        async def timed_store_entity(entity):
            import time
            start = time.time()
            await asyncio.sleep(0.01)  # Simulate network delay
            end = time.time()
            client.operation_times.append(('store', (end - start) * 1000))
            return AsyncMock()
        
        client.store_entity = timed_store_entity
        client.search_entities = AsyncMock(return_value=[])
        client.get_entity = AsyncMock(return_value=None)
        
        return client
    
    @pytest.mark.asyncio
    async def test_mcp_operation_performance(self, mock_mcp_client):
        """Test MCP operation performance under normal conditions."""
        config = {'agent_id': 'perf_test', 'input_validation': {}}
        
        agent = IntakeAssistantAgent('perf_test', mock_mcp_client, config)
        
        test_input = {
            'project_name': 'Performance Test',
            'description': 'Testing MCP performance',
            'industry': 'technology',
            'department': 'it',
            'stakeholders': [{'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'}],
            'goals': ['Performance'],
            'success_criteria': ['Fast execution'],
            'budget': 50000,
            'timeline': 3,
            'urgency': 'medium',
            'expected_participants': 3
        }
        
        # Execute agent
        result = await agent.execute(test_input)
        assert result.status == AgentStatus.SUCCESS
        
        # Validate performance metrics
        assert len(mock_mcp_client.operation_times) > 0
        
        # Check operation times are reasonable (< 100ms per operation)
        for operation, time_ms in mock_mcp_client.operation_times:
            assert time_ms < 100, f"MCP {operation} operation took {time_ms}ms (too slow)"
    
    @pytest.mark.asyncio
    async def test_concurrent_mcp_operations(self, mock_mcp_client):
        """Test MCP performance under concurrent operations."""
        config = {'agent_id': 'concurrent_test', 'input_validation': {}}
        
        # Create multiple agents for concurrent testing
        agents = [
            IntakeAssistantAgent(f'concurrent_{i}', mock_mcp_client, config.copy())
            for i in range(3)
        ]
        
        test_inputs = [
            {
                'project_name': f'Concurrent Test {i}',
                'description': f'Testing concurrent MCP operations {i}',
                'industry': 'technology',
                'department': 'it',
                'stakeholders': [{'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'}],
                'goals': [f'Concurrency {i}'],
                'success_criteria': [f'Concurrent execution {i}'],
                'budget': 20000 + i * 5000,
                'timeline': 2 + i,
                'urgency': 'medium',
                'expected_participants': 2 + i
            }
            for i in range(3)
        ]
        
        # Execute agents concurrently
        tasks = [
            agent.execute(test_input)
            for agent, test_input in zip(agents, test_inputs)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Validate all executions succeeded
        successful_results = [
            r for r in results 
            if isinstance(r, AgentResult) and r.status == AgentStatus.SUCCESS
        ]
        
        assert len(successful_results) == 3
        
        # Validate MCP operations completed
        assert len(mock_mcp_client.operation_times) >= 3


if __name__ == '__main__':
    # Run MCP compliance tests
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])
