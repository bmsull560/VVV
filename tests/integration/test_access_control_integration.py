import pytest
from memory.core import MemoryManager
from memory.memory_types import MemoryAccess, MemoryTier, MemoryEntity

@pytest.mark.asyncio
async def test_access_control_integration_unauthorized_read(memory_manager: MemoryManager):
    """Test that unauthorized users cannot read from protected memory."""
    # Create a protected entity
    entity_id = "test_protected_entity"
    await memory_manager.create_entity(
        entity_id=entity_id,
        entity_type="test_type",
        content={"data": "sensitive_info"},
        access_control={"read": ["role:unauthorized"]},
        user_id="system",
        role="system"
    )

    # Attempt to read with an unauthorized role
    with pytest.raises(PermissionError):
        await memory_manager.read_entity(
            entity_id=entity_id,
            access_level=MemoryAccess.READ,
            user_id="unauthorized_user",
            role="role:guest"
        )

@pytest.mark.asyncio
async def test_access_control_integration_authorized_read(memory_manager: MemoryManager):
    """Test that authorized users can read from protected memory."""
    # Create a protected entity
    entity_id = "test_authorized_entity"
    await memory_manager.create_entity(
        entity_id=entity_id,
        entity_type="test_type",
        content={"data": "sensitive_info"},
        access_control={"read": ["role:authorized"]},
        user_id="system",
        role="system"
    )

    # Attempt to read with an authorized role
    entity = await memory_manager.read_entity(
        entity_id=entity_id,
        access_level=MemoryAccess.READ,
        user_id="authorized_user",
        role="role:authorized"
    )
    assert entity.content["data"] == "sensitive_info"

@pytest.mark.asyncio
async def test_access_control_integration_unauthorized_write(memory_manager: MemoryManager):
    """Test that unauthorized users cannot write to protected memory.""" 
    # Create a protected entity
    entity_id = "test_protected_write_entity"
    await memory_manager.create_entity(
        entity_id=entity_id,
        entity_type="test_type",
        content={"data": "initial_info"},
        access_control={"write": ["role:authorized_writer"]},
        user_id="system",
        role="system"
    )

    # Attempt to update with an unauthorized role
    with pytest.raises(PermissionError):
        await memory_manager.update_entity(
            entity_id=entity_id,
            content={"data": "new_info"},
            access_level=MemoryAccess.WRITE,
            user_id="unauthorized_writer",
            role="role:guest"
        )

@pytest.mark.asyncio
async def test_access_control_integration_authorized_write(memory_manager: MemoryManager):
    """Test that authorized users can write to protected memory."""
    # Create a protected entity
    entity_id = "test_authorized_write_entity"
    await memory_manager.create_entity(
        entity_id=entity_id,
        entity_type="test_type",
        content={"data": "initial_info"},
        access_control={"write": ["role:authorized_writer"]},
        user_id="system",
        role="system"
    )

    # Attempt to update with an authorized role
    await memory_manager.update_entity(
        entity_id=entity_id,
        content={"data": "new_info"},
        access_level=MemoryAccess.WRITE,
        user_id="authorized_writer",
        role="role:authorized_writer"
    )

    # Verify the update
    updated_entity = await memory_manager.read_entity(
        entity_id=entity_id,
        access_level=MemoryAccess.READ, # Read access for verification
        user_id="system", # System can read all
        role="system"
    )
    assert updated_entity.content["data"] == "new_info"

# You would need a fixture for memory_manager that sets up a clean database for each test.
# For example, in conftest.py:
# @pytest.fixture
# async def memory_manager():
#     from memory.core import MemoryManager
#     from memory.episodic_memory import EpisodicStorageBackend
#     from memory.semantic_memory import SemanticMemory
#     from memory.knowledge_graph import KnowledgeGraph
#     from memory.database_models import Base, engine, SessionLocal
#     from sqlalchemy.orm import sessionmaker

#     # Use an in-memory SQLite database for testing
#     test_engine = create_engine("sqlite:///:memory:")
#     Base.metadata.create_all(test_engine)
#     TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

#     async def get_test_db():
#         db = TestingSessionLocal()
#         try:
#             yield db
#         finally:
#             db.close()

#     episodic_backend = EpisodicStorageBackend(get_test_db)
#     semantic_memory = SemanticMemory(episodic_backend) # SemanticMemory might also need a backend
#     knowledge_graph = KnowledgeGraph(episodic_backend) # KnowledgeGraph might also need a backend

#     manager = MemoryManager(
#         episodic_backend=episodic_backend,
#         semantic_memory=semantic_memory,
#         knowledge_graph=knowledge_graph
#     )
#     yield manager

#     # Clean up after test (optional for in-memory, but good practice)
#     Base.metadata.drop_all(test_engine)
