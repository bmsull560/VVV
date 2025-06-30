"""
Tests for the PostgreSQL-backed EpisodicMemory.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
import uuid

from memory.episodic import EpisodicMemory
from memory.memory_types import WorkflowMemoryEntity, DataSensitivity, MemoryTier

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
async def test_search_caching(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test that search operations are cached, and verify hit/miss counts."""
    # Clear cache before test to ensure clean state
    episodic_memory._backend.clear_cache()

    await episodic_memory.store(sample_workflow_entity)

    search_query_1 = {"workflow_name": "Test Workflow"}
    search_query_2 = {"workflow_name": "Another Workflow"}

    # First search for query 1: should be a miss
    search_results_1 = await episodic_memory.search(search_query_1)
    assert len(search_results_1) == 1
    assert episodic_memory._backend._search_cache_hits == 0
    assert episodic_memory._backend._search_cache_misses == 1

    # Second search for query 1: should be a hit
    search_results_1_hit = await episodic_memory.search(search_query_1)
    assert len(search_results_1_hit) == 1
    assert episodic_memory._backend._search_cache_hits == 1
    assert episodic_memory._backend._search_cache_misses == 1

    # First search for query 2: should be a miss
    search_results_2 = await episodic_memory.search(search_query_2)
    assert len(search_results_2) == 0 # Assuming no entity for 'Another Workflow'
    assert episodic_memory._backend._search_cache_hits == 1
    assert episodic_memory._backend._search_cache_misses == 2

    # Second search for query 2: should be a hit
    search_results_2_hit = await episodic_memory.search(search_query_2)
    assert len(search_results_2_hit) == 0
    assert episodic_memory._backend._search_cache_hits == 2
    assert episodic_memory._backend._search_cache_misses == 2

@pytest.mark.asyncio
async def test_search_cache_maxsize(episodic_memory: EpisodicMemory):
    """Test that the search cache respects maxsize and evicts old entries."""
    # Temporarily set a small maxsize for testing eviction
    original_maxsize = episodic_memory._backend._search_cache_maxsize
    episodic_memory._backend._search_cache_maxsize = 2
    episodic_memory._backend.clear_cache()

    # Store all entities first
    entities = []
    for i in range(5):
        entity = WorkflowMemoryEntity(
            id=str(uuid.uuid4()),
            workflow_id=str(uuid.uuid4()),
            workflow_name=f"Workflow {i}",
            workflow_status="completed",
            start_time=datetime.now(timezone.utc),
            creator_id="test-user",
            sensitivity=DataSensitivity.INTERNAL,
            tier=MemoryTier.EPISODIC,
            version=1
        )
        await episodic_memory.store(entity)
        entities.append(entity)

    # Now perform searches to fill the cache beyond maxsize
    # The cache should be cleared after the last store operation, so it's empty here.
    # We expect 5 cache misses and 2 items in cache at the end.
    for i in range(5):
        await episodic_memory.search({"workflow_name": f"Workflow {i}"})

    # The cache should now contain only the most recent entries up to maxsize
    assert len(episodic_memory._backend._search_cache) == episodic_memory._backend._search_cache_maxsize

    # Verify that older entries are evicted (e.g., Workflow 0, 1, 2 should be gone if maxsize is 2)
    # The cache should contain Workflow 3 and Workflow 4's search results.
    first_query_key = (frozenset({"workflow_name": "Workflow 0"}.items()), 10) # Default limit is 10
    assert first_query_key not in episodic_memory._backend._search_cache

    second_query_key = (frozenset({"workflow_name": "Workflow 1"}.items()), 10)
    assert second_query_key not in episodic_memory._backend._search_cache

    third_query_key = (frozenset({"workflow_name": "Workflow 2"}.items()), 10)
    assert third_query_key not in episodic_memory._backend._search_cache

    fourth_query_key = (frozenset({"workflow_name": "Workflow 3"}.items()), 10)
    assert fourth_query_key in episodic_memory._backend._search_cache

    fifth_query_key = (frozenset({"workflow_name": "Workflow 4"}.items()), 10)
    assert fifth_query_key in episodic_memory._backend._search_cache

    # Restore original maxsize
    episodic_memory._backend._search_cache_maxsize = original_maxsize


@pytest.mark.asyncio
async def test_cache_invalidation_on_store(episodic_memory: EpisodicMemory, sample_workflow_entity: WorkflowMemoryEntity):
    """Test that caches are invalidated when an entity is stored."""
    # Populate caches
    await episodic_memory.store(sample_workflow_entity)
    await episodic_memory.retrieve(sample_workflow_entity.id)
    await episodic_memory.search({"workflow_name": "Test Workflow"})

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

    # Assert caches are cleared and stats reset

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

    # Delete the entity, which should invalidate caches
    await episodic_memory.delete(sample_workflow_entity.id)



    # Assert caches are cleared and stats reset
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

    # Assert caches are populated (at least one hit/miss for retrieve, and search cache has entries)

    assert len(episodic_memory._backend._search_cache) > 0

    # Clear caches explicitly
    episodic_memory._backend.clear_cache()
