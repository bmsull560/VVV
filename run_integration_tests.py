#!/usr/bin/env python3
"""
Integration test execution script for B2BValue agents.

This script provides a simple entry point to run all integration tests
and generate comprehensive reports.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add the tests directory to the Python path for local imports
tests_dir = project_root / "tests"
sys.path.insert(0, str(tests_dir))

# Change to the tests/integration directory for relative imports
integration_dir = tests_dir / "integration"
os.chdir(integration_dir)

from test_runner import main as run_integration_tests


def main():
    """Main entry point."""
    print("B2BValue Agent Integration Test Suite")
    print("="*50)
    print("Starting comprehensive integration testing...")
    print("This may take several minutes to complete.")
    print("")
    
    try:
        # Run integration tests
        asyncio.run(run_integration_tests())
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest execution failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
