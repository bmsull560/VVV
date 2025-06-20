#!/usr/bin/env python3
"""
Validation script to check if the integration test framework is properly configured.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add tests directory to path
tests_dir = project_root / "tests"
sys.path.insert(0, str(tests_dir))

def validate_imports():
    """Validate that all required modules can be imported."""
    print("🔍 Validating imports...")
    
    try:
        # Try importing from tests.integration package
        from tests.integration.test_config import IntegrationTestConfig, TestConfigurationManager
        print("✅ test_config imports successful")
        
        from tests.integration.test_runner import TestRunner
        print("✅ test_runner imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ General error: {e}")
        return False

def validate_config():
    """Validate that configuration can be loaded."""
    print("\n🔍 Validating configuration...")
    
    try:
        from tests.integration.test_config import TestConfigurationManager
        config = TestConfigurationManager.load_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   - Test environment: {config.test_environment}")
        print(f"   - Agent configurations: {len(config.agent_configs)}")
        print(f"   - Workflow tests: {len(config.workflow_tests)}")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def validate_test_data():
    """Validate that test data can be loaded."""
    print("\n🔍 Validating test data...")
    
    try:
        from tests.integration.test_config import TestDataManager
        data_manager = TestDataManager()
        datasets = data_manager.get_test_datasets()
        print(f"✅ Test data loaded successfully")
        print(f"   - Available datasets: {len(datasets)}")
        for name in list(datasets.keys())[:3]:  # Show first 3
            print(f"   - {name}")
        return True
        
    except Exception as e:
        print(f"❌ Test data error: {e}")
        return False

def validate_directories():
    """Validate that required directories exist."""
    print("\n🔍 Validating directories...")
    
    dirs_to_check = [
        "tests/integration",
        "tests/integration/config", 
        "tests/integration/data",
        "tests/integration/results"
    ]
    
    all_good = True
    for dir_path in dirs_to_check:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - Missing!")
            all_good = False
    
    return all_good

def main():
    """Main validation function."""
    print("B2BValue Integration Test Setup Validation")
    print("=" * 50)
    
    validations = [
        validate_directories,
        validate_imports,
        validate_config,
        validate_test_data
    ]
    
    results = []
    for validation in validations:
        try:
            result = validation()
            results.append(result)
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 All validations passed! Integration test framework is ready.")
        return 0
    else:
        print("⚠️  Some validations failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
