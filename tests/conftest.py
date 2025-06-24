"""
Pytest configuration file for B2BValue tests.
"""

import pytest

def pytest_collection_modifyitems(items):
    """
    Modify the collected test items to exclude specific classes from test_runner_util.py
    that have __init__ constructors but are not actual test classes.
    """
    for item in list(items):
        if item.parent.name == "test_runner_util":
            if item.name.startswith(("TestResult", "TestSuiteResult", "TestExecutionReport", 
                                    "SystemMonitor", "IntegrationTestRunner")):
                items.remove(item)
