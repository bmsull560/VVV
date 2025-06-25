"""
Pytest configuration file for B2BValue tests.
"""

import pytest
import pytest_asyncio
import os
import sys

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

@pytest_asyncio.fixture
async def memory_manager():
    """Provides a MemoryManager instance with an in-memory SQLite backend for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from VVV.memory.database_models import Base
    from VVV.memory.episodic_storage_backend import EpisodicStorageBackend
    from VVV.memory.semantic import SemanticMemory
    from VVV.memory.knowledge_graph import KnowledgeGraph
    from VVV.memory.core import MemoryManager

    # Use an in-memory SQLite database for testing
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    async def get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    episodic_backend = EpisodicStorageBackend("sqlite+aiosqlite:///:memory:")
    semantic_memory = SemanticMemory(episodic_backend) # SemanticMemory might also need a backend
    knowledge_graph = KnowledgeGraph(episodic_backend) # KnowledgeGraph might also need a backend

    manager = MemoryManager()
    # Set up the memory components manually since MemoryManager doesn't accept constructor parameters
    manager._episodic_memory = episodic_backend
    manager._semantic_memory = semantic_memory
    manager._knowledge_graph = knowledge_graph
    
    yield manager

    # Clean up after test (optional for in-memory, but good practice)
    Base.metadata.drop_all(test_engine)
