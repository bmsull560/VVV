"""
Load and performance testing for B2BValue agent workflows.

This module tests agent performance under various load conditions,
validates response times, and ensures system stability under stress.
"""

import pytest
import asyncio
import time
import statistics
from typing import Dict, Any, List, Tuple
from unittest.mock import Mock, AsyncMock
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc

from agents.intake_assistant.main import IntakeAssistantAgent
from agents.value_driver.main import ValueDriverAgent
from agents.roi_calculator.main import ROICalculatorAgent
from agents.risk_mitigation.main import RiskMitigationAgent
from agents.sensitivity_analysis.main import SensitivityAnalysisAgent
from agents.analytics_aggregator.main import AnalyticsAggregatorAgent
from agents.core.agent_base import AgentResult, AgentStatus


class PerformanceMetrics:
    """Utility class for collecting and analyzing performance metrics."""
    
    def __init__(self):
        self.execution_times = []
        self.memory_usage = []
        self.cpu_usage = []
        self.error_count = 0
        self.success_count = 0
    
    def record_execution(self, execution_time_ms: float, success: bool):
        """Record execution metrics."""
        self.execution_times.append(execution_time_ms)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def record_system_metrics(self):
        """Record system resource usage."""
        process = psutil.Process()
        self.memory_usage.append(process.memory_info().rss / 1024 / 1024)  # MB
        self.cpu_usage.append(process.cpu_percent())
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.execution_times:
            return {}
        
        return {
            'execution_times': {
                'mean_ms': statistics.mean(self.execution_times),
                'median_ms': statistics.median(self.execution_times),
                'min_ms': min(self.execution_times),
                'max_ms': max(self.execution_times),
                'std_dev_ms': statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0,
                'p95_ms': sorted(self.execution_times)[int(len(self.execution_times) * 0.95)],
                'p99_ms': sorted(self.execution_times)[int(len(self.execution_times) * 0.99)]
            },
            'success_rate': self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0,
            'total_executions': self.success_count + self.error_count,
            'memory_usage': {
                'mean_mb': statistics.mean(self.memory_usage) if self.memory_usage else 0,
                'max_mb': max(self.memory_usage) if self.memory_usage else 0
            },
            'cpu_usage': {
                'mean_percent': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                'max_percent': max(self.cpu_usage) if self.cpu_usage else 0
            }
        }


class TestLoadPerformance:
    """Test agent performance under various load conditions."""
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Fast mock MCP client for performance testing."""
        client = Mock()
        client.store_entity = AsyncMock()
        client.search_entities = AsyncMock(return_value=[])
        client.get_entity = AsyncMock(return_value=None)
        client.update_entity = AsyncMock()
        return client
    
    @pytest.fixture
    def base_config(self):
        """Base configuration optimized for performance testing."""
        return {
            'agent_id': 'perf_test_agent',
            'timeout_seconds': 10,  # Reduced for faster testing
            'retry_attempts': 1,    # Reduced for faster testing
            'input_validation': {}
        }
    
    @pytest.fixture
    def sample_inputs(self):
        """Sample inputs for different agent types."""
        return {
            'intake': {
                'project_name': 'Load Test Project',
                'description': 'Performance testing project',
                'industry': 'technology',
                'department': 'it',
                'stakeholders': [
                    {'name': 'Test User', 'role': 'sponsor', 'influence_level': 'high'},
                    {'name': 'Test Owner', 'role': 'business_owner', 'influence_level': 'high'}
                ],
                'goals': ['Performance testing', 'Load validation'],
                'success_criteria': ['Fast response times', 'System stability'],
                'budget': 100000,
                'timeline': 6,
                'urgency': 'high',
                'expected_participants': 8
            },
            'value_driver': {
                'user_query': 'Analyze value drivers for load testing project',
                'analysis_type': 'comprehensive',
                'business_context': {
                    'industry': 'technology',
                    'company_size': 'large',
                    'project_type': 'optimization'
                }
            },
            'roi': {
                'drivers': [
                    {
                        'pillar': 'Cost Reduction',
                        'tier_2_drivers': [
                            {
                                'name': 'Reduce Manual Labor',
                                'tier_3_metrics': [
                                    {'name': 'Hours saved per week', 'value': 30},
                                    {'name': 'Average hourly rate', 'value': 60}
                                ]
                            }
                        ]
                    }
                ],
                'investment': 100000
            },
            'risk': {
                'project_details': {
                    'name': 'Load Test Project',
                    'budget': 100000,
                    'timeline': 6,
                    'expected_value': 200000
                },
                'risks': [
                    {
                        'name': 'Performance Risk',
                        'category': 'technical',
                        'probability': 'medium',
                        'impact': 'high'
                    },
                    {
                        'name': 'Scalability Risk',
                        'category': 'operational',
                        'probability': 'low',
                        'impact': 'medium'
                    }
                ],
                'risk_tolerance': 'medium'
            },
            'sensitivity': {
                'base_scenario': {
                    'investment': 100000,
                    'annual_benefits': 150000,
                    'time_horizon': 5
                },
                'sensitivity_variables': [
                    {
                        'name': 'annual_benefits',
                        'base_value': 150000,
                        'range_min': 100000,
                        'range_max': 200000
                    }
                ],
                'analysis_type': 'single_variable',
                'risk_tolerance': 'medium'
            }
        }
    
    @pytest.mark.asyncio
    async def test_single_agent_performance_baseline(self, mock_mcp_client, base_config, sample_inputs):
        """Test baseline performance for individual agents."""
        
        # Test cases for different agents
        test_cases = [
            (IntakeAssistantAgent, sample_inputs['intake']),
            (ValueDriverAgent, sample_inputs['value_driver']),
            (ROICalculatorAgent, sample_inputs['roi']),
            (RiskMitigationAgent, sample_inputs['risk']),
            (SensitivityAnalysisAgent, sample_inputs['sensitivity'])
        ]
        
        baseline_metrics = {}
        
        for agent_class, test_input in test_cases:
            agent_name = agent_class.__name__
            metrics = PerformanceMetrics()
            
            # Run single execution baseline
            agent = agent_class(f'baseline_{agent_name}', mock_mcp_client, base_config.copy())
            
            start_time = time.time()
            result = await agent.execute(test_input)
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            metrics.record_execution(execution_time, result.status == AgentStatus.COMPLETED)
            metrics.record_system_metrics()
            
            baseline_metrics[agent_name] = metrics.get_summary()
            
            # Baseline performance assertions
            assert result.status == AgentStatus.COMPLETED, f"{agent_name} failed baseline test"
            assert execution_time < 5000, f"{agent_name} baseline execution too slow: {execution_time}ms"
        
        # Print baseline results for reference
        print("\n=== BASELINE PERFORMANCE METRICS ===")
        for agent_name, metrics in baseline_metrics.items():
            print(f"{agent_name}: {metrics['execution_times']['mean_ms']:.2f}ms avg")
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_load(self, mock_mcp_client, base_config, sample_inputs):
        """Test performance under concurrent agent execution."""
        
        # Test concurrent execution of same agent type
        concurrent_levels = [5, 10, 20]
        
        for concurrency in concurrent_levels:
            metrics = PerformanceMetrics()
            
            # Create multiple agents
            agents = [
                IntakeAssistantAgent(f'concurrent_{i}', mock_mcp_client, base_config.copy())
                for i in range(concurrency)
            ]
            
            # Execute concurrently
            start_time = time.time()
            
            tasks = [
                agent.execute(sample_inputs['intake'].copy())
                for agent in agents
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = (time.time() - start_time) * 1000
            
            # Analyze results
            successful_results = [
                r for r in results 
                if isinstance(r, AgentResult) and r.status == AgentStatus.COMPLETED
            ]
            
            # Record metrics
            for result in successful_results:
                metrics.record_execution(result.execution_time_ms, True)
            
            for result in results:
                if not isinstance(result, AgentResult) or result.status != AgentStatus.COMPLETED:
                    metrics.record_execution(0, False)
            
            metrics.record_system_metrics()
            summary = metrics.get_summary()
            
            # Performance assertions
            assert summary['success_rate'] >= 0.95, f"Success rate too low at {concurrency} concurrent: {summary['success_rate']}"
            assert summary['execution_times']['p95_ms'] < 10000, f"P95 response time too high at {concurrency} concurrent"
            assert total_time < 30000, f"Total execution time too high at {concurrency} concurrent: {total_time}ms"
            
            print(f"\nConcurrency {concurrency}: {summary['success_rate']:.2%} success, {summary['execution_times']['mean_ms']:.2f}ms avg")
    
    @pytest.mark.asyncio
    async def test_mixed_agent_workflow_load(self, mock_mcp_client, base_config, sample_inputs):
        """Test performance of mixed agent workflows under load."""
        
        workflows = [
            [
                (IntakeAssistantAgent, sample_inputs['intake']),
                (ValueDriverAgent, sample_inputs['value_driver']),
                (ROICalculatorAgent, sample_inputs['roi'])
            ],
            [
                (IntakeAssistantAgent, sample_inputs['intake']),
                (RiskMitigationAgent, sample_inputs['risk']),
                (SensitivityAnalysisAgent, sample_inputs['sensitivity'])
            ]
        ]
        
        for workflow_idx, workflow in enumerate(workflows):
            metrics = PerformanceMetrics()
            
            # Execute workflow multiple times concurrently
            num_workflows = 5
            
            async def execute_workflow(workflow_id):
                workflow_start = time.time()
                
                for agent_class, test_input in workflow:
                    agent = agent_class(f'workflow_{workflow_idx}_{workflow_id}', mock_mcp_client, base_config.copy())
                    result = await agent.execute(test_input.copy())
                    
                    if result.status != AgentStatus.COMPLETED:
                        return False, (time.time() - workflow_start) * 1000
                
                return True, (time.time() - workflow_start) * 1000
            
            # Execute workflows concurrently
            tasks = [execute_workflow(i) for i in range(num_workflows)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze workflow results
            for result in results:
                if isinstance(result, tuple):
                    success, execution_time = result
                    metrics.record_execution(execution_time, success)
                else:
                    metrics.record_execution(0, False)
            
            metrics.record_system_metrics()
            summary = metrics.get_summary()
            
            # Workflow performance assertions
            assert summary['success_rate'] >= 0.8, f"Workflow {workflow_idx} success rate too low: {summary['success_rate']}"
            assert summary['execution_times']['mean_ms'] < 15000, f"Workflow {workflow_idx} average time too high"
            
            print(f"Workflow {workflow_idx}: {summary['success_rate']:.2%} success, {summary['execution_times']['mean_ms']:.2f}ms avg")
    
    @pytest.mark.asyncio
    async def test_sustained_load_performance(self, mock_mcp_client, base_config, sample_inputs):
        """Test performance under sustained load over time."""
        
        # Run sustained load for 30 seconds
        duration_seconds = 30
        request_interval = 0.5  # Request every 500ms
        
        metrics = PerformanceMetrics()
        
        async def sustained_execution():
            end_time = time.time() + duration_seconds
            
            while time.time() < end_time:
                agent = IntakeAssistantAgent('sustained_test', mock_mcp_client, base_config.copy())
                
                start = time.time()
                result = await agent.execute(sample_inputs['intake'].copy())
                execution_time = (time.time() - start) * 1000
                
                metrics.record_execution(execution_time, result.status == AgentStatus.COMPLETED)
                metrics.record_system_metrics()
                
                # Wait before next request
                await asyncio.sleep(request_interval)
        
        # Execute sustained load
        await sustained_execution()
        
        summary = metrics.get_summary()
        
        # Sustained load assertions
        assert summary['success_rate'] >= 0.95, f"Sustained load success rate too low: {summary['success_rate']}"
        assert summary['execution_times']['mean_ms'] < 3000, f"Sustained load average time too high: {summary['execution_times']['mean_ms']}"
        assert summary['memory_usage']['max_mb'] < 500, f"Memory usage too high: {summary['memory_usage']['max_mb']}MB"
        
        print(f"\nSustained Load ({duration_seconds}s): {summary['success_rate']:.2%} success, {summary['execution_times']['mean_ms']:.2f}ms avg")
        print(f"Memory: {summary['memory_usage']['mean_mb']:.1f}MB avg, {summary['memory_usage']['max_mb']:.1f}MB max")
    
    @pytest.mark.asyncio
    async def test_memory_usage_and_leaks(self, mock_mcp_client, base_config, sample_inputs):
        """Test memory usage patterns and detect potential memory leaks."""
        
        # Run multiple iterations to detect memory leaks
        iterations = 20
        memory_samples = []
        
        for i in range(iterations):
            # Force garbage collection before measurement
            gc.collect()
            
            # Measure memory before execution
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Execute agent
            agent = IntakeAssistantAgent(f'memory_test_{i}', mock_mcp_client, base_config.copy())
            result = await agent.execute(sample_inputs['intake'].copy())
            
            assert result.status == AgentStatus.COMPLETED
            
            # Measure memory after execution
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(memory_after - memory_before)
            
            # Clean up
            del agent
            gc.collect()
        
        # Analyze memory usage patterns
        avg_memory_per_execution = statistics.mean(memory_samples)
        max_memory_per_execution = max(memory_samples)
        
        # Memory usage assertions
        assert avg_memory_per_execution < 50, f"Average memory per execution too high: {avg_memory_per_execution}MB"
        assert max_memory_per_execution < 100, f"Max memory per execution too high: {max_memory_per_execution}MB"
        
        # Check for potential memory leaks (increasing trend)
        if len(memory_samples) >= 10:
            first_half_avg = statistics.mean(memory_samples[:len(memory_samples)//2])
            second_half_avg = statistics.mean(memory_samples[len(memory_samples)//2:])
            
            memory_growth = second_half_avg - first_half_avg
            assert memory_growth < 10, f"Potential memory leak detected: {memory_growth}MB growth"
        
        print(f"\nMemory Usage: {avg_memory_per_execution:.2f}MB avg, {max_memory_per_execution:.2f}MB max per execution")
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance(self, mock_mcp_client, base_config, sample_inputs):
        """Test performance when recovering from errors."""
        
        # Create a mock client that fails periodically
        failure_rate = 0.2  # 20% failure rate
        failure_count = 0
        
        original_store_entity = mock_mcp_client.store_entity
        
        async def failing_store_entity(*args, **kwargs):
            nonlocal failure_count
            if failure_count % 5 == 0:  # Fail every 5th call
                failure_count += 1
                raise Exception("Simulated MCP failure")
            failure_count += 1
            return await original_store_entity(*args, **kwargs)
        
        mock_mcp_client.store_entity = failing_store_entity
        
        metrics = PerformanceMetrics()
        
        # Execute multiple times with periodic failures
        for i in range(10):
            agent = IntakeAssistantAgent(f'error_recovery_{i}', mock_mcp_client, base_config.copy())
            
            start_time = time.time()
            result = await agent.execute(sample_inputs['intake'].copy())
            execution_time = (time.time() - start_time) * 1000
            
            metrics.record_execution(execution_time, result.status == AgentStatus.COMPLETED)
        
        summary = metrics.get_summary()
        
        # Error recovery assertions
        assert summary['success_rate'] >= 0.6, f"Error recovery success rate too low: {summary['success_rate']}"
        assert summary['execution_times']['mean_ms'] < 5000, f"Error recovery average time too high: {summary['execution_times']['mean_ms']}"
        
        print(f"\nError Recovery: {summary['success_rate']:.2%} success rate with simulated failures")
    
    @pytest.mark.asyncio
    async def test_scalability_limits(self, mock_mcp_client, base_config, sample_inputs):
        """Test system behavior at scalability limits."""
        
        # Test increasing levels of concurrency to find limits
        max_successful_concurrency = 0
        
        for concurrency in [50, 100, 200]:
            try:
                # Create agents
                agents = [
                    IntakeAssistantAgent(f'scale_{i}', mock_mcp_client, base_config.copy())
                    for i in range(concurrency)
                ]
                
                # Execute with timeout
                start_time = time.time()
                
                tasks = [
                    agent.execute(sample_inputs['intake'].copy())
                    for agent in agents
                ]
                
                # Wait with timeout
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=60.0  # 60 second timeout
                )
                
                execution_time = time.time() - start_time
                
                # Check results
                successful_results = [
                    r for r in results 
                    if isinstance(r, AgentResult) and r.status == AgentStatus.COMPLETED
                ]
                
                success_rate = len(successful_results) / len(results)
                
                if success_rate >= 0.8 and execution_time < 60:
                    max_successful_concurrency = concurrency
                    print(f"Scalability: {concurrency} concurrent agents - {success_rate:.2%} success in {execution_time:.1f}s")
                else:
                    print(f"Scalability limit reached at {concurrency} concurrent agents")
                    break
                    
            except asyncio.TimeoutError:
                print(f"Scalability limit: timeout at {concurrency} concurrent agents")
                break
            except Exception as e:
                print(f"Scalability limit: error at {concurrency} concurrent agents - {e}")
                break
        
        # Scalability assertions
        assert max_successful_concurrency >= 50, f"Scalability too low: max {max_successful_concurrency} concurrent agents"
        
        print(f"\nMax Scalability: {max_successful_concurrency} concurrent agents")


class TestPerformanceRegression:
    """Test for performance regressions across agent versions."""
    
    @pytest.mark.asyncio
    async def test_performance_benchmark(self, mock_mcp_client):
        """Benchmark test to establish performance baselines."""
        
        # This test should be run regularly to detect performance regressions
        # Store results for comparison with future runs
        
        config = {'agent_id': 'benchmark', 'input_validation': {}}
        
        benchmark_input = {
            'project_name': 'Benchmark Test Project',
            'description': 'Performance benchmark test',
            'industry': 'technology',
            'department': 'it',
            'stakeholders': [{'name': 'Benchmark User', 'role': 'sponsor', 'influence_level': 'high'}],
            'goals': ['Performance benchmarking'],
            'success_criteria': ['Consistent performance'],
            'budget': 100000,
            'timeline': 6,
            'urgency': 'medium',
            'expected_participants': 5
        }
        
        # Run benchmark iterations
        execution_times = []
        
        for i in range(10):
            agent = IntakeAssistantAgent(f'benchmark_{i}', mock_mcp_client, config.copy())
            
            start_time = time.time()
            result = await agent.execute(benchmark_input.copy())
            execution_time = (time.time() - start_time) * 1000
            
            assert result.status == AgentStatus.COMPLETED
            execution_times.append(execution_time)
        
        # Calculate benchmark metrics
        benchmark_metrics = {
            'mean_execution_time_ms': statistics.mean(execution_times),
            'median_execution_time_ms': statistics.median(execution_times),
            'max_execution_time_ms': max(execution_times),
            'std_dev_ms': statistics.stdev(execution_times),
            'p95_ms': sorted(execution_times)[int(len(execution_times) * 0.95)]
        }
        
        # Performance regression thresholds
        assert benchmark_metrics['mean_execution_time_ms'] < 2000, "Performance regression: mean execution time too high"
        assert benchmark_metrics['p95_ms'] < 3000, "Performance regression: P95 execution time too high"
        assert benchmark_metrics['std_dev_ms'] < 500, "Performance regression: execution time too variable"
        
        print(f"\n=== PERFORMANCE BENCHMARK ===")
        print(f"Mean: {benchmark_metrics['mean_execution_time_ms']:.2f}ms")
        print(f"P95: {benchmark_metrics['p95_ms']:.2f}ms")
        print(f"Max: {benchmark_metrics['max_execution_time_ms']:.2f}ms")
        print(f"Std Dev: {benchmark_metrics['std_dev_ms']:.2f}ms")


if __name__ == '__main__':
    # Run performance tests
    pytest.main([__file__, '-v', '--asyncio-mode=auto', '-s'])
