"""
Integration test configuration and utilities.

This module provides configuration management, test fixtures,
and utilities for integration testing across the B2BValue agent system.
"""

import os
import json
import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Test configuration paths
TEST_CONFIG_DIR = Path(__file__).parent / "config"
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_RESULTS_DIR = Path(__file__).parent / "results"

# Ensure directories exist
TEST_CONFIG_DIR.mkdir(exist_ok=True)
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_RESULTS_DIR.mkdir(exist_ok=True)


@dataclass
class AgentTestConfig:
    """Configuration for individual agent testing."""
    agent_id: str
    timeout_seconds: int = 30
    retry_attempts: int = 3
    max_concurrent_executions: int = 10
    performance_threshold_ms: int = 5000
    memory_limit_mb: int = 256
    enable_logging: bool = True
    log_level: str = "INFO"


@dataclass
class WorkflowTestConfig:
    """Configuration for workflow testing."""
    workflow_name: str
    agents: List[str]
    max_execution_time_ms: int = 30000
    success_rate_threshold: float = 0.95
    enable_performance_monitoring: bool = True


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    concurrent_users: List[int]
    test_duration_seconds: int = 60
    ramp_up_seconds: int = 10
    success_rate_threshold: float = 0.9
    response_time_p95_ms: int = 10000
    memory_usage_limit_mb: int = 1024


@dataclass
class IntegrationTestConfig:
    """Master configuration for integration testing."""
    test_environment: str = "integration"
    database_url: str = "postgresql://test:test@localhost:5432/b2bvalue_test"
    mcp_server_url: str = "http://localhost:8080"
    enable_real_mcp: bool = False
    enable_real_database: bool = False
    
    # Agent configurations
    agents: Dict[str, AgentTestConfig] = None
    
    # Workflow configurations
    workflows: Dict[str, WorkflowTestConfig] = None
    
    # Load test configuration
    load_test: LoadTestConfig = None
    
    # Test data configurations
    test_data_sets: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize default configurations."""
        if self.agents is None:
            self.agents = self._create_default_agent_configs()
        
        if self.workflows is None:
            self.workflows = self._create_default_workflow_configs()
        
        if self.load_test is None:
            self.load_test = LoadTestConfig(
                concurrent_users=[5, 10, 20, 50],
                test_duration_seconds=60,
                ramp_up_seconds=10
            )
        
        if self.test_data_sets is None:
            self.test_data_sets = self._create_default_test_data_sets()
    
    def _create_default_agent_configs(self) -> Dict[str, AgentTestConfig]:
        """Create default agent configurations."""
        agents = [
            "intake_assistant", "value_driver", "roi_calculator",
            "risk_mitigation", "sensitivity_analysis", "analytics_aggregator",
            "database_connector", "data_correlator"
        ]
        
        return {
            agent: AgentTestConfig(
                agent_id=f"test_{agent}",
                timeout_seconds=30,
                retry_attempts=3,
                max_concurrent_executions=10,
                performance_threshold_ms=5000 if agent != "analytics_aggregator" else 10000,
                memory_limit_mb=256
            )
            for agent in agents
        }
    
    def _create_default_workflow_configs(self) -> Dict[str, WorkflowTestConfig]:
        """Create default workflow configurations."""
        return {
            "business_case_creation": WorkflowTestConfig(
                workflow_name="business_case_creation",
                agents=["intake_assistant", "value_driver", "roi_calculator", "risk_mitigation"],
                max_execution_time_ms=30000,
                success_rate_threshold=0.95
            ),
            "financial_analysis": WorkflowTestConfig(
                workflow_name="financial_analysis",
                agents=["roi_calculator", "sensitivity_analysis", "analytics_aggregator"],
                max_execution_time_ms=25000,
                success_rate_threshold=0.9
            ),
            "risk_assessment": WorkflowTestConfig(
                workflow_name="risk_assessment",
                agents=["risk_mitigation", "sensitivity_analysis", "data_correlator"],
                max_execution_time_ms=20000,
                success_rate_threshold=0.9
            ),
            "data_analysis": WorkflowTestConfig(
                workflow_name="data_analysis",
                agents=["database_connector", "data_correlator", "analytics_aggregator"],
                max_execution_time_ms=35000,
                success_rate_threshold=0.85
            )
        }
    
    def _create_default_test_data_sets(self) -> Dict[str, str]:
        """Create default test data set configurations."""
        return {
            "small_project": "test_data/small_project.json",
            "medium_project": "test_data/medium_project.json",
            "large_project": "test_data/large_project.json",
            "complex_project": "test_data/complex_project.json",
            "financial_data": "test_data/financial_data.json",
            "risk_scenarios": "test_data/risk_scenarios.json",
            "performance_dataset": "test_data/performance_dataset.json"
        }


class TestDataManager:
    """Manages test data for integration testing."""
    
    def __init__(self, config: IntegrationTestConfig):
        self.config = config
        self.test_data_cache = {}
    
    def load_test_data(self, dataset_name: str) -> Dict[str, Any]:
        """Load test data from configuration."""
        if dataset_name in self.test_data_cache:
            return self.test_data_cache[dataset_name]
        
        if dataset_name not in self.config.test_data_sets:
            raise ValueError(f"Unknown test dataset: {dataset_name}")
        
        data_file = TEST_DATA_DIR / self.config.test_data_sets[dataset_name]
        
        if not data_file.exists():
            # Create default test data if file doesn't exist
            test_data = self._create_default_test_data(dataset_name)
            self.save_test_data(dataset_name, test_data)
        else:
            with open(data_file, 'r') as f:
                test_data = json.load(f)
        
        self.test_data_cache[dataset_name] = test_data
        return test_data
    
    def save_test_data(self, dataset_name: str, data: Dict[str, Any]):
        """Save test data to file."""
        if dataset_name not in self.config.test_data_sets:
            raise ValueError(f"Unknown test dataset: {dataset_name}")
        
        data_file = TEST_DATA_DIR / self.config.test_data_sets[dataset_name]
        data_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.test_data_cache[dataset_name] = data
    
    def _create_default_test_data(self, dataset_name: str) -> Dict[str, Any]:
        """Create default test data for a dataset."""
        
        if dataset_name == "small_project":
            return {
                "intake": {
                    "project_name": "Small CRM Integration",
                    "description": "Integrate new CRM system with existing tools",
                    "industry": "technology",
                    "department": "sales",
                    "stakeholders": [
                        {"name": "Alice Smith", "role": "sponsor", "influence_level": "high"},
                        {"name": "Bob Johnson", "role": "owner", "influence_level": "high"}
                    ],
                    "goals": [
                        "Improve sales team productivity",
                        "Reduce data entry time by 30%"
                    ],
                    "success_criteria": [
                        "CRM integration completed within 3 months",
                        "User adoption rate > 80%"
                    ],
                    "budget": 50000,
                    "timeline": 3,
                    "urgency": "medium",
                    "expected_participants": 5
                },
                "value_driver": {
                    "user_query": "Analyze productivity gains from CRM integration",
                    "analysis_type": "focused",
                    "focus_areas": ["productivity_gains"],
                    "business_context": {
                        "industry": "technology",
                        "company_size": "small",
                        "project_type": "integration"
                    }
                },
                "roi": {
                    "drivers": [
                        {
                            "pillar": "Productivity Gains",
                            "tier_2_drivers": [
                                {
                                    "name": "Accelerate Task Completion",
                                    "tier_3_metrics": [
                                        {"name": "Time saved per task (minutes)", "value": 10},
                                        {"name": "Tasks per week", "value": 50}
                                    ]
                                }
                            ]
                        }
                    ],
                    "investment": 50000
                }
            }
        
        elif dataset_name == "medium_project":
            return {
                "intake": {
                    "project_name": "Customer Portal Modernization",
                    "description": "Modernize customer portal with new UI and features",
                    "industry": "financial_services",
                    "department": "customer_service",
                    "stakeholders": [
                        {"name": "Carol Davis", "role": "sponsor", "influence_level": "high"},
                        {"name": "David Wilson", "role": "owner", "influence_level": "high"},
                        {"name": "Eve Brown", "role": "user", "influence_level": "medium"}
                    ],
                    "goals": [
                        "Improve customer satisfaction scores by 25%",
                        "Reduce support ticket volume by 40%",
                        "Increase self-service adoption by 60%"
                    ],
                    "success_criteria": [
                        "Customer satisfaction survey improvement",
                        "Support ticket reduction measurable within 6 months",
                        "Self-service usage analytics show 60% increase"
                    ],
                    "budget": 150000,
                    "timeline": 6,
                    "urgency": "high",
                    "expected_participants": 12
                },
                "risks": [
                    {
                        "name": "User Adoption Challenges",
                        "category": "operational",
                        "probability": "medium",
                        "impact": "high"
                    },
                    {
                        "name": "Integration Complexity",
                        "category": "technical",
                        "probability": "medium",
                        "impact": "medium"
                    },
                    {
                        "name": "Budget Overrun",
                        "category": "financial",
                        "probability": "low",
                        "impact": "medium"
                    }
                ]
            }
        
        elif dataset_name == "large_project":
            return {
                "intake": {
                    "project_name": "Enterprise Resource Planning Implementation",
                    "description": "Implement comprehensive ERP system across multiple departments",
                    "industry": "manufacturing",
                    "department": "operations",
                    "stakeholders": [
                        {"name": "Frank Miller", "role": "sponsor", "influence_level": "high"},
                        {"name": "Grace Taylor", "role": "owner", "influence_level": "high"},
                        {"name": "Henry Anderson", "role": "user", "influence_level": "high"},
                        {"name": "Ivy Thompson", "role": "user", "influence_level": "medium"},
                        {"name": "Jack Wilson", "role": "stakeholder", "influence_level": "medium"}
                    ],
                    "goals": [
                        "Streamline operations across all departments",
                        "Reduce operational costs by 20%",
                        "Improve reporting accuracy by 95%",
                        "Enhance inventory management efficiency by 40%"
                    ],
                    "success_criteria": [
                        "ERP system fully operational within 18 months",
                        "All departments migrated successfully",
                        "Cost reduction targets achieved within 2 years",
                        "User training completion rate > 90%"
                    ],
                    "budget": 500000,
                    "timeline": 18,
                    "urgency": "medium",
                    "expected_participants": 35
                }
            }
        
        elif dataset_name == "financial_data":
            return {
                "roi_scenarios": [
                    {
                        "name": "Conservative Scenario",
                        "investment": 100000,
                        "annual_benefits": 120000,
                        "time_horizon": 5,
                        "discount_rate": 0.08
                    },
                    {
                        "name": "Optimistic Scenario",
                        "investment": 100000,
                        "annual_benefits": 180000,
                        "time_horizon": 5,
                        "discount_rate": 0.08
                    },
                    {
                        "name": "Pessimistic Scenario",
                        "investment": 100000,
                        "annual_benefits": 80000,
                        "time_horizon": 5,
                        "discount_rate": 0.08
                    }
                ],
                "sensitivity_variables": [
                    {
                        "name": "annual_benefits",
                        "base_value": 150000,
                        "range_min": 100000,
                        "range_max": 200000
                    },
                    {
                        "name": "implementation_cost",
                        "base_value": 100000,
                        "range_min": 80000,
                        "range_max": 150000
                    },
                    {
                        "name": "time_to_value",
                        "base_value": 6,
                        "range_min": 3,
                        "range_max": 12
                    }
                ]
            }
        
        elif dataset_name == "risk_scenarios":
            return {
                "common_risks": [
                    {
                        "name": "Technical Integration Complexity",
                        "category": "technical",
                        "probability": "medium",
                        "impact": "high",
                        "description": "Challenges integrating with existing systems"
                    },
                    {
                        "name": "User Resistance to Change",
                        "category": "operational",
                        "probability": "high",
                        "impact": "medium",
                        "description": "Users may resist adopting new processes"
                    },
                    {
                        "name": "Vendor Performance Issues",
                        "category": "vendor",
                        "probability": "low",
                        "impact": "high",
                        "description": "Third-party vendor may not deliver as expected"
                    },
                    {
                        "name": "Budget Constraints",
                        "category": "financial",
                        "probability": "medium",
                        "impact": "high",
                        "description": "Project may exceed allocated budget"
                    },
                    {
                        "name": "Timeline Delays",
                        "category": "timeline",
                        "probability": "medium",
                        "impact": "medium",
                        "description": "Project may take longer than planned"
                    }
                ],
                "risk_tolerance_profiles": [
                    {
                        "name": "Conservative",
                        "risk_tolerance": "low",
                        "description": "Prefer lower risk with guaranteed returns"
                    },
                    {
                        "name": "Moderate",
                        "risk_tolerance": "medium",
                        "description": "Balanced approach to risk and return"
                    },
                    {
                        "name": "Aggressive",
                        "risk_tolerance": "high",
                        "description": "Willing to accept higher risk for higher returns"
                    }
                ]
            }
        
        elif dataset_name == "performance_dataset":
            return {
                "load_test_scenarios": [
                    {
                        "name": "Light Load",
                        "concurrent_users": 5,
                        "duration_seconds": 30,
                        "expected_success_rate": 0.99
                    },
                    {
                        "name": "Normal Load",
                        "concurrent_users": 20,
                        "duration_seconds": 60,
                        "expected_success_rate": 0.95
                    },
                    {
                        "name": "Heavy Load",
                        "concurrent_users": 50,
                        "duration_seconds": 120,
                        "expected_success_rate": 0.9
                    },
                    {
                        "name": "Stress Test",
                        "concurrent_users": 100,
                        "duration_seconds": 300,
                        "expected_success_rate": 0.8
                    }
                ],
                "performance_benchmarks": {
                    "intake_assistant": {"max_response_time_ms": 2000},
                    "value_driver": {"max_response_time_ms": 3000},
                    "roi_calculator": {"max_response_time_ms": 2500},
                    "risk_mitigation": {"max_response_time_ms": 3000},
                    "sensitivity_analysis": {"max_response_time_ms": 4000},
                    "analytics_aggregator": {"max_response_time_ms": 5000},
                    "database_connector": {"max_response_time_ms": 1000},
                    "data_correlator": {"max_response_time_ms": 3500}
                }
            }
        
        else:
            return {}


class TestConfigurationManager:
    """Manages test configuration loading and saving."""
    
    @staticmethod
    def load_config(config_file: Optional[str] = None) -> IntegrationTestConfig:
        """Load integration test configuration."""
        if config_file is None:
            config_file = TEST_CONFIG_DIR / "integration_test_config.yaml"
        
        config_path = Path(config_file)
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Convert nested dictionaries to dataclass instances
            if 'agents' in config_data:
                config_data['agents'] = {
                    name: AgentTestConfig(**agent_config)
                    for name, agent_config in config_data['agents'].items()
                }
            
            if 'workflows' in config_data:
                config_data['workflows'] = {
                    name: WorkflowTestConfig(**workflow_config)
                    for name, workflow_config in config_data['workflows'].items()
                }
            
            if 'load_test' in config_data:
                config_data['load_test'] = LoadTestConfig(**config_data['load_test'])
            
            return IntegrationTestConfig(**config_data)
        else:
            # Create default configuration
            config = IntegrationTestConfig()
            TestConfigurationManager.save_config(config, config_path)
            return config
    
    @staticmethod
    def save_config(config: IntegrationTestConfig, config_file: Optional[str] = None):
        """Save integration test configuration."""
        if config_file is None:
            config_file = TEST_CONFIG_DIR / "integration_test_config.yaml"
        
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert dataclass instances to dictionaries
        config_dict = asdict(config)
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)


# Environment-specific configurations
def get_test_environment() -> str:
    """Get current test environment from environment variables."""
    return os.getenv('TEST_ENVIRONMENT', 'integration')


def get_database_url() -> str:
    """Get test database URL from environment variables."""
    return os.getenv('TEST_DATABASE_URL', 'postgresql://test:test@localhost:5432/b2bvalue_test')


def get_mcp_server_url() -> str:
    """Get MCP server URL from environment variables."""
    return os.getenv('TEST_MCP_SERVER_URL', 'http://localhost:8080')


def is_real_mcp_enabled() -> bool:
    """Check if real MCP testing is enabled."""
    return os.getenv('ENABLE_REAL_MCP', 'false').lower() == 'true'


def is_real_database_enabled() -> bool:
    """Check if real database testing is enabled."""
    return os.getenv('ENABLE_REAL_DATABASE', 'false').lower() == 'true'


# Test utilities
def create_test_directories():
    """Create necessary test directories."""
    directories = [
        TEST_CONFIG_DIR,
        TEST_DATA_DIR,
        TEST_RESULTS_DIR,
        TEST_DATA_DIR / "test_data"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def cleanup_test_environment():
    """Clean up test environment after test runs."""
    # Clean up test result files older than 7 days
    import time
    current_time = time.time()
    
    if TEST_RESULTS_DIR.exists():
        for file_path in TEST_RESULTS_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (7 * 24 * 60 * 60):  # 7 days
                    file_path.unlink()


if __name__ == "__main__":
    # Initialize test configuration
    create_test_directories()
    
    # Create and save default configuration
    config = IntegrationTestConfig()
    TestConfigurationManager.save_config(config)
    
    # Create test data manager and initialize default test data
    data_manager = TestDataManager(config)
    
    # Create default test datasets
    for dataset_name in config.test_data_sets.keys():
        try:
            data_manager.load_test_data(dataset_name)
            print(f"Created test dataset: {dataset_name}")
        except Exception as e:
            print(f"Error creating test dataset {dataset_name}: {e}")
    
    print("Integration test configuration initialized successfully!")
