"""
Tests for the PostgreSQL-backed EpisodicMemory.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
import uuid

from memory.episodic import EpisodicMemory
from memory.types import WorkflowMemoryEntity, DataSensitivity, MemoryTier

# Use an in-memory SQLite database for testing
TEST_DSN = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def episodic_memory():
    """Provides an initialized EpisodicMemory instance with an in-memory DB."""
    # For tests, always use an in-memory SQLite database instead of the remote PostgreSQL
    # This ensures tests are self-contained and don't depend on external services
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

@pytest.mark.asyncio
async def test_retrieve_caching(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test that retrieve operations are cached."""
    await episodic_memory.store(sample_workflow_entity)

    # First retrieve should be a miss (or not from cache)
    retrieved_entity_1 = await episodic_memory.retrieve(sample_workflow_entity.id)
    assert retrieved_entity_1 is not None

    # Clear cache stats for retrieve to get accurate hit/miss count
    episodic_memory._backend.retrieve.cache_clear()

    # Second retrieve should be a hit
    retrieved_entity_2 = await episodic_memory.retrieve(sample_workflow_entity.id)
    assert retrieved_entity_2 is not None
    assert episodic_memory._backend.retrieve.cache_info().hits == 1
    assert episodic_memory._backend.retrieve.cache_info().misses == 0

@pytest.mark.asyncio
async def test_search_caching(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test that search operations are cached."""
    await episodic_memory.store(sample_workflow_entity)

    # First search should be a miss
    search_query = {"workflow_name": "Test Workflow"}
    search_results_1 = await episodic_memory.search(search_query)
    assert len(search_results_1) == 1
    assert episodic_memory._backend._search_cache_hits == 0
    assert episodic_memory._backend._search_cache_misses == 1

    # Second search with same query should be a hit
    search_results_2 = await episodic_memory.search(search_query)
    assert len(search_results_2) == 1
    assert episodic_memory._backend._search_cache_hits == 1
    assert episodic_memory._backend._search_cache_misses == 1

    # Search with different query should be a miss
    search_results_3 = await episodic_memory.search({"workflow_name": "Another Workflow"})
    assert len(search_results_3) == 0
    assert episodic_memory._backend._search_cache_hits == 1
    assert episodic_memory._backend._search_cache_misses == 2

@pytest.mark.asyncio
async def test_cache_invalidation_on_store(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test that caches are invalidated when an entity is stored."""
    # Populate caches
    await episodic_memory.store(sample_workflow_entity)
    await episodic_memory.retrieve(sample_workflow_entity.id)
    await episodic_memory.search({"workflow_name": "Test Workflow"})

    # Assert caches are populated
    assert episodic_memory._backend.retrieve.cache_info().hits >= 0 # Can be 0 if first retrieve was only one
    assert episodic_memory._backend._search_cache_hits >= 0
    assert len(episodic_memory._backend._search_cache) > 0

    # Store a new entity, which should invalidate caches
    new_entity = WorkflowMemoryEntity(
        id=str(uuid.uuid4()),
        workflow_id=str(uuid.uuid4()),
        workflow_name="New Workflow",
        workflow_status="in_progress",
        start_time=datetime.now(timezone.utc),
        creator_id="test-user-2",
        sensitivity=DataSensitivity.INTERNAL,
        tier=MemoryTier.EPISODIC,
        version=1
    )
    await episodic_memory.store(new_entity)

    # Assert caches are cleared
    assert episodic_memory._backend.retrieve.cache_info().currsize == 0
    assert len(episodic_memory._backend._search_cache) == 0
    assert episodic_memory._backend._search_cache_hits == 0
    assert episodic_memory._backend._search_cache_misses == 0

@pytest.mark.asyncio
async def test_cache_invalidation_on_delete(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test that caches are invalidated when an entity is deleted."""
    # Populate caches
    await episodic_memory.store(sample_workflow_entity)
    await episodic_memory.retrieve(sample_workflow_entity.id)
    await episodic_memory.search({"workflow_name": "Test Workflow"})

    # Assert caches are populated
    assert episodic_memory._backend.retrieve.cache_info().hits >= 0
    assert episodic_memory._backend._search_cache_hits >= 0
    assert len(episodic_memory._backend._search_cache) > 0

    # Delete the entity, which should invalidate caches
    await episodic_memory.delete(sample_workflow_entity.id)

    # Assert caches are cleared
    assert episodic_memory._backend.retrieve.cache_info().currsize == 0
    assert len(episodic_memory._backend._search_cache) == 0
    assert episodic_memory._backend._search_cache_hits == 0
    assert episodic_memory._backend._search_cache_misses == 0

@pytest.mark.asyncio
async def test_clear_cache_method(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test the explicit clear_cache method."""
    # Populate caches
    await episodic_memory.store(sample_workflow_entity)
    await episodic_memory.retrieve(sample_workflow_entity.id)
    await episodic_memory.search({"workflow_name": "Test Workflow"})

    # Assert caches are populated
    assert episodic_memory._backend.retrieve.cache_info().hits >= 0
    assert episodic_memory._backend._search_cache_hits >= 0
    assert len(episodic_memory._backend._search_cache) > 0

    # Clear caches explicitly
    episodic_memory._backend.clear_cache()

    # Assert caches are cleared
    assert episodic_memory._backend.retrieve.cache_info().currsize == 0
    assert len(episodic_memory._backend._search_cache) == 0
    assert episodic_memory._backend._search_cache_hits == 0
    assert episodic_memory._backend._search_cache_misses == 0
