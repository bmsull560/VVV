"""
Tests for the PostgreSQL-backed EpisodicMemory.
"""

import pytest
import asyncio
from datetime import datetime, timezone
import uuid

from memory.episodic import EpisodicMemory
from memory.types import WorkflowMemoryEntity, DataSensitivity, MemoryTier

# Use an in-memory SQLite database for testing
TEST_DSN = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def episodic_memory():
    """Provides an initialized EpisodicMemory instance with an in-memory DB."""
    memory = EpisodicMemory(dsn=TEST_DSN)
    # We need to initialize the schema for the in-memory database
    await memory._backend.initialize_schema()
    await memory.initialize()
    return memory

@pytest.fixture
def sample_workflow_entity():
    """Provides a sample WorkflowMemoryEntity for testing."""
    return WorkflowMemoryEntity(
        id=str(uuid.uuid4()),
        workflow_id=str(uuid.uuid4()),
        workflow_name="Test Workflow",
        workflow_status="completed",
        start_time=datetime.now(timezone.utc),
        creator_id="test-user",
        user_id=None, # Cannot link to a user in a test without a user fixture
        sensitivity=DataSensitivity.INTERNAL,
        tier=MemoryTier.EPISODIC,
        version=1
    )

@pytest.mark.asyncio
async def test_store_and_retrieve_entity(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test storing and retrieving a single entity."""
    # Store the entity
    stored_id = await episodic_memory.store(sample_workflow_entity)
    assert stored_id == sample_workflow_entity.id

    # Retrieve the entity
    retrieved_entity = await episodic_memory.retrieve(sample_workflow_entity.id)

    # Assertions
    assert retrieved_entity is not None
    assert retrieved_entity.id == sample_workflow_entity.id
    assert retrieved_entity.workflow_id == sample_workflow_entity.workflow_id
    assert retrieved_entity.workflow_name == "Test Workflow"

@pytest.mark.asyncio
async def test_retrieve_non_existent_entity(episodic_memory: EpisodicMemory):
    """Test that retrieving a non-existent entity returns None."""
    retrieved_entity = await episodic_memory.retrieve(str(uuid.uuid4()))
    assert retrieved_entity is None

@pytest.mark.asyncio
async def test_delete_entity(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test deleting an entity."""
    # Store and verify it's there
    await episodic_memory.store(sample_workflow_entity)
    assert await episodic_memory.retrieve(sample_workflow_entity.id) is not None

    # Delete it
    delete_success = await episodic_memory.delete(sample_workflow_entity.id)
    assert delete_success is True

    # Verify it's gone
    assert await episodic_memory.retrieve(sample_workflow_entity.id) is None

@pytest.mark.asyncio
async def test_delete_non_existent_entity(episodic_memory: EpisodicMemory):
    """Test that deleting a non-existent entity returns False."""
    delete_success = await episodic_memory.delete(str(uuid.uuid4()))
    assert delete_success is False

@pytest.mark.asyncio
async def test_search_entity(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test searching for an entity."""
    await episodic_memory.store(sample_workflow_entity)

    # Search by workflow_name
    search_results = await episodic_memory.search({"workflow_name": "Test Workflow"})
    assert len(search_results) == 1
    assert search_results[0].id == sample_workflow_entity.id

    # Search by a non-matching criterion
    search_results_fail = await episodic_memory.search({"workflow_name": "Non-Existent Workflow"})
    assert len(search_results_fail) == 0

    # Search by workflow_id
    search_results_wf_id = await episodic_memory.search({"workflow_id": sample_workflow_entity.workflow_id})
    assert len(search_results_wf_id) == 1
    assert search_results_wf_id[0].id == sample_workflow_entity.id
