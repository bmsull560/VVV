import pytest

from memory.memory_types import MemoryAccess, MemoryAccessControl, ContextMemoryEntity, MemoryTier
from memory.core import MemoryManager


# Memory Manager Access Control Tests
from memory.core import MemoryManager
from memory.memory_types import ContextMemoryEntity, MemoryTier # Add other entities as needed

# Test data for MemoryManager tests
USER_AGENT = "agent_user_1"
USER_EDITOR = "editor_user_1"
USER_ADMIN = "admin_user_1"
USER_VIEWER = "viewer_user_1"

ROLE_AGENT_MM = "role:agent" # Key used in MemoryManager
ROLE_EDITOR_MM = "role:editor"
ROLE_VIEWER_MM = "role:viewer"


class TestMemoryManagerAccessControl:
    def setup_method(self):
        """Setup for each test method."""
        self.manager = MemoryManager()
        # Initialize with minimal in-memory tiers for these tests
        # More complex tests might need mocks or specific backend setups
        self.manager.initialize() 

    @pytest.mark.asyncio
    async def test_set_and_apply_default_role_acl_on_new_entity(self):
        """Test that default role ACLs are applied to new entities without their own policy."""
        # 1. Set default ACLs
        agent_acl = MemoryAccessControl(
            entity_id=ROLE_AGENT_MM, # The key used by MemoryManager
            roles={ "agent": [MemoryAccess.READ] } # The actual role name and its permissions
        )
        self.manager.set_default_access_control(ROLE_AGENT_MM, agent_acl)

        editor_acl = MemoryAccessControl(
            entity_id=ROLE_EDITOR_MM,
            roles={ "editor": [MemoryAccess.READ, MemoryAccess.WRITE] }
        )
        self.manager.set_default_access_control(ROLE_EDITOR_MM, editor_acl)

        # 2. Store a new entity (without its own access_policy)
        new_entity = ContextMemoryEntity(
            id="test_ctx_entity_001",
            workflow_id="wf_default_acl",
            creator_id="system_creator",
            tier=MemoryTier.WORKING,
            # No access_policy defined on the entity itself
        )
        
        entity_id = await self.manager.store(new_entity, user_id="system_creator", role="admin")
        assert entity_id == "test_ctx_entity_001"

        # 3. Retrieve the ACL for the new entity and check permissions
        # The MemoryManager stores the actual ACL under the entity_id
        entity_acl = self.manager._access_controls.get(entity_id)
        assert entity_acl is not None, f"No ACL found for entity {entity_id}"

        # Check agent permissions (role name is 'agent', not 'role:agent')
        assert entity_acl.can_access(USER_AGENT, "agent", MemoryAccess.READ), "Agent should have READ"
        assert not entity_acl.can_access(USER_AGENT, "agent", MemoryAccess.WRITE), "Agent should NOT have WRITE"
        assert not entity_acl.can_access(USER_AGENT, "agent", MemoryAccess.DELETE), "Agent should NOT have DELETE"

        # Check editor permissions
        assert entity_acl.can_access(USER_EDITOR, "editor", MemoryAccess.READ), "Editor should have READ"
        assert entity_acl.can_access(USER_EDITOR, "editor", MemoryAccess.WRITE), "Editor should have WRITE"
        assert not entity_acl.can_access(USER_EDITOR, "editor", MemoryAccess.DELETE), "Editor should NOT have DELETE"

        # Check admin permissions (admin always gets full access)
        assert entity_acl.can_access(USER_ADMIN, "admin", MemoryAccess.READ), "Admin should have READ"
        assert entity_acl.can_access(USER_ADMIN, "admin", MemoryAccess.WRITE), "Admin should have WRITE"
        assert entity_acl.can_access(USER_ADMIN, "admin", MemoryAccess.DELETE), "Admin should have DELETE"

        # Check unprivileged role (e.g., viewer, for whom no default was set here)
        assert not entity_acl.can_access(USER_VIEWER, "viewer", MemoryAccess.READ), "Viewer should NOT have READ"
