"""
Stakeholder Coordinator Agent

This agent manages multi-user collaboration workflows, permissions, and handoffs
between AI and human roles in the business case creation process.
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timezone

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient
from memory.memory_types import KnowledgeEntity

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """Status of a collaboration task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    """Priority level for collaboration tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UserRole(str, Enum):
    """User roles in the collaboration workflow."""
    OWNER = "owner"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"
    ADMIN = "admin"

class StakeholderCoordinatorAgent(BaseAgent):
    """
    Production-ready agent for managing multi-user collaboration workflows,
    permissions, and handoffs between AI and human roles.
    """

    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        # Set up validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['action'],
                'field_types': {
                    'action': 'string',
                    'project_id': 'string',
                    'user_id': 'string',
                    'task_id': 'string',
                    'task_data': 'object',
                    'user_data': 'object',
                    'notification_data': 'object'
                },
                'field_constraints': {
                    'action': {'allowed_values': [
                        'create_task', 'update_task', 'assign_task', 'complete_task',
                        'add_user', 'remove_user', 'update_permissions', 'send_notification',
                        'get_project_status', 'get_user_tasks'
                    ]}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Initialize collaboration state
        self.notification_channels = self.config.get('notification_channels', ['email', 'in_app'])
        self.default_task_timeout = self.config.get('default_task_timeout_hours', 48)
        self.auto_reminder_hours = self.config.get('auto_reminder_hours', 24)

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Perform stakeholder coordinator-specific validations."""
        errors = []
        
        action = inputs.get('action', '')
        
        # Validate required fields based on action
        if action == 'create_task':
            if 'project_id' not in inputs:
                errors.append("project_id is required for create_task action")
            if 'task_data' not in inputs or not isinstance(inputs['task_data'], dict):
                errors.append("task_data object is required for create_task action")
            else:
                task_data = inputs['task_data']
                if 'title' not in task_data:
                    errors.append("task_data.title is required")
                if 'description' not in task_data:
                    errors.append("task_data.description is required")
        
        elif action == 'update_task':
            if 'task_id' not in inputs:
                errors.append("task_id is required for update_task action")
            if 'task_data' not in inputs or not isinstance(inputs['task_data'], dict):
                errors.append("task_data object is required for update_task action")
        
        elif action == 'assign_task':
            if 'task_id' not in inputs:
                errors.append("task_id is required for assign_task action")
            if 'user_id' not in inputs:
                errors.append("user_id is required for assign_task action")
        
        elif action == 'complete_task':
            if 'task_id' not in inputs:
                errors.append("task_id is required for complete_task action")
        
        elif action == 'add_user' or action == 'remove_user' or action == 'update_permissions':
            if 'project_id' not in inputs:
                errors.append(f"project_id is required for {action} action")
            if 'user_id' not in inputs:
                errors.append(f"user_id is required for {action} action")
            if action == 'add_user' or action == 'update_permissions':
                if 'user_data' not in inputs or not isinstance(inputs['user_data'], dict):
                    errors.append(f"user_data object is required for {action} action")
                elif 'role' not in inputs['user_data']:
                    errors.append("user_data.role is required")
        
        elif action == 'send_notification':
            if 'user_id' not in inputs:
                errors.append("user_id is required for send_notification action")
            if 'notification_data' not in inputs or not isinstance(inputs['notification_data'], dict):
                errors.append("notification_data object is required for send_notification action")
            else:
                notification_data = inputs['notification_data']
                if 'message' not in notification_data:
                    errors.append("notification_data.message is required")
                if 'type' not in notification_data:
                    errors.append("notification_data.type is required")
        
        elif action == 'get_project_status':
            if 'project_id' not in inputs:
                errors.append("project_id is required for get_project_status action")
        
        elif action == 'get_user_tasks':
            if 'user_id' not in inputs:
                errors.append("user_id is required for get_user_tasks action")
        
        return errors

    async def _create_task(self, project_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collaboration task."""
        task_id = f"task_{int(time.time())}_{hash(task_data['title']) % 10000}"
        
        # Set default values
        task = {
            'task_id': task_id,
            'project_id': project_id,
            'title': task_data['title'],
            'description': task_data['description'],
            'status': TaskStatus.PENDING.value,
            'priority': task_data.get('priority', TaskPriority.MEDIUM.value),
            'assignee': task_data.get('assignee'),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'due_date': task_data.get('due_date'),
            'tags': task_data.get('tags', []),
            'dependencies': task_data.get('dependencies', []),
            'metadata': task_data.get('metadata', {})
        }
        
        # Store task in MCP
        await self._store_task(task)
        
        # Send notification if assignee is specified
        if task.get('assignee'):
            await self._send_task_notification(
                user_id=task['assignee'],
                task_id=task_id,
                notification_type='task_assigned',
                message=f"You have been assigned a new task: {task['title']}"
            )
        
        return task

    async def _update_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task."""
        # Retrieve existing task
        existing_task = await self._get_task(task_id)
        if not existing_task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update fields
        updated_task = {**existing_task}
        for key, value in task_data.items():
            if key not in ['task_id', 'project_id', 'created_at']:
                updated_task[key] = value
        
        updated_task['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Store updated task
        await self._store_task(updated_task)
        
        # Send notifications for status changes
        if 'status' in task_data and task_data['status'] != existing_task['status']:
            if task_data['status'] == TaskStatus.COMPLETED.value:
                await self._send_task_notification(
                    user_id=existing_task.get('assignee'),
                    task_id=task_id,
                    notification_type='task_completed',
                    message=f"Task completed: {existing_task['title']}"
                )
            elif task_data['status'] == TaskStatus.BLOCKED.value:
                await self._send_task_notification(
                    user_id=existing_task.get('assignee'),
                    task_id=task_id,
                    notification_type='task_blocked',
                    message=f"Task blocked: {existing_task['title']}"
                )
        
        # Send notification for assignee changes
        if 'assignee' in task_data and task_data['assignee'] != existing_task.get('assignee'):
            if task_data['assignee']:
                await self._send_task_notification(
                    user_id=task_data['assignee'],
                    task_id=task_id,
                    notification_type='task_assigned',
                    message=f"You have been assigned a task: {existing_task['title']}"
                )
        
        return updated_task

    async def _assign_task(self, task_id: str, user_id: str) -> Dict[str, Any]:
        """Assign a task to a user."""
        # Retrieve existing task
        existing_task = await self._get_task(task_id)
        if not existing_task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update assignee
        updated_task = {**existing_task, 'assignee': user_id, 'updated_at': datetime.now(timezone.utc).isoformat()}
        
        # Store updated task
        await self._store_task(updated_task)
        
        # Send notification to new assignee
        await self._send_task_notification(
            user_id=user_id,
            task_id=task_id,
            notification_type='task_assigned',
            message=f"You have been assigned a task: {existing_task['title']}"
        )
        
        return updated_task

    async def _complete_task(self, task_id: str) -> Dict[str, Any]:
        """Mark a task as completed."""
        # Retrieve existing task
        existing_task = await self._get_task(task_id)
        if not existing_task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update status
        updated_task = {
            **existing_task,
            'status': TaskStatus.COMPLETED.value,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Store updated task
        await self._store_task(updated_task)
        
        # Check for dependent tasks and update their status
        await self._update_dependent_tasks(task_id)
        
        # Send notification to project stakeholders
        await self._send_task_notification(
            user_id=existing_task.get('assignee'),
            task_id=task_id,
            notification_type='task_completed',
            message=f"Task completed: {existing_task['title']}"
        )
        
        return updated_task

    async def _add_user(self, project_id: str, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a user to a project with specified role and permissions."""
        # Get project
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Create user entry
        user_entry = {
            'user_id': user_id,
            'project_id': project_id,
            'role': user_data.get('role', UserRole.VIEWER.value),
            'permissions': user_data.get('permissions', []),
            'added_at': datetime.now(timezone.utc).isoformat(),
            'added_by': user_data.get('added_by', 'system'),
            'metadata': user_data.get('metadata', {})
        }
        
        # Store user entry
        await self._store_project_user(user_entry)
        
        # Send notification to user
        await self._send_notification(
            user_id=user_id,
            notification_type='project_invitation',
            message=f"You have been added to project: {project.get('name', project_id)}",
            data={'project_id': project_id, 'role': user_entry['role']}
        )
        
        return user_entry

    async def _remove_user(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Remove a user from a project."""
        # Get project
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get user entry
        user_entry = await self._get_project_user(project_id, user_id)
        if not user_entry:
            raise ValueError(f"User {user_id} not found in project {project_id}")
        
        # Mark user as removed
        updated_entry = {
            **user_entry,
            'removed_at': datetime.now(timezone.utc).isoformat(),
            'active': False
        }
        
        # Store updated entry
        await self._store_project_user(updated_entry)
        
        # Reassign user's tasks
        await self._reassign_user_tasks(project_id, user_id)
        
        # Send notification to user
        await self._send_notification(
            user_id=user_id,
            notification_type='project_removal',
            message=f"You have been removed from project: {project.get('name', project_id)}",
            data={'project_id': project_id}
        )
        
        return updated_entry

    async def _update_permissions(self, project_id: str, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user's role and permissions in a project."""
        # Get project
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get user entry
        user_entry = await self._get_project_user(project_id, user_id)
        if not user_entry:
            raise ValueError(f"User {user_id} not found in project {project_id}")
        
        # Update role and permissions
        updated_entry = {
            **user_entry,
            'role': user_data.get('role', user_entry.get('role')),
            'permissions': user_data.get('permissions', user_entry.get('permissions', [])),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Store updated entry
        await self._store_project_user(updated_entry)
        
        # Send notification to user
        await self._send_notification(
            user_id=user_id,
            notification_type='permissions_updated',
            message=f"Your permissions have been updated in project: {project.get('name', project_id)}",
            data={'project_id': project_id, 'role': updated_entry['role']}
        )
        
        return updated_entry

    async def _send_notification(self, user_id: str, notification_type: str, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a notification to a user."""
        notification = {
            'notification_id': f"notif_{int(time.time())}_{hash(message) % 10000}",
            'user_id': user_id,
            'type': notification_type,
            'message': message,
            'data': data or {},
            'created_at': datetime.now(timezone.utc).isoformat(),
            'read': False,
            'channels': self.notification_channels
        }
        
        # Store notification in MCP
        await self._store_notification(notification)
        
        # Deliver notification through configured channels
        for channel in self.notification_channels:
            await self._deliver_notification(notification, channel)
        
        return notification

    async def _get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get the current status of a project, including tasks and users."""
        # Get project
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Get tasks
        tasks = await self._get_project_tasks(project_id)
        
        # Get users
        users = await self._get_project_users(project_id)
        
        # Calculate statistics
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.get('status') == TaskStatus.COMPLETED.value)
        blocked_tasks = sum(1 for task in tasks if task.get('status') == TaskStatus.BLOCKED.value)
        
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Get recent activity
        recent_activity = await self._get_project_activity(project_id, limit=10)
        
        return {
            'project_id': project_id,
            'project_name': project.get('name', 'Unknown Project'),
            'status': project.get('status', 'active'),
            'task_stats': {
                'total': total_tasks,
                'completed': completed_tasks,
                'in_progress': sum(1 for task in tasks if task.get('status') == TaskStatus.IN_PROGRESS.value),
                'pending': sum(1 for task in tasks if task.get('status') == TaskStatus.PENDING.value),
                'blocked': blocked_tasks,
                'completion_percentage': completion_percentage
            },
            'users': [
                {
                    'user_id': user.get('user_id'),
                    'role': user.get('role'),
                    'active': user.get('active', True)
                }
                for user in users
            ],
            'recent_activity': recent_activity,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

    async def _get_user_tasks(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks assigned to a user, optionally filtered by status."""
        # Query for tasks assigned to the user
        query = {'assignee': user_id}
        if status:
            query['status'] = status
        
        tasks = await self._search_tasks(query)
        
        # Sort tasks by priority and due date
        tasks.sort(key=lambda t: (
            self._priority_sort_key(t.get('priority', TaskPriority.MEDIUM.value)),
            t.get('due_date', '9999-12-31')
        ))
        
        return tasks

    def _priority_sort_key(self, priority: str) -> int:
        """Convert priority string to sort key (lower number = higher priority)."""
        priority_map = {
            TaskPriority.CRITICAL.value: 0,
            TaskPriority.HIGH.value: 1,
            TaskPriority.MEDIUM.value: 2,
            TaskPriority.LOW.value: 3
        }
        return priority_map.get(priority, 999)

    async def _update_dependent_tasks(self, completed_task_id: str) -> None:
        """Update tasks that depend on a completed task."""
        # Find tasks that depend on the completed task
        dependent_tasks = await self._search_tasks({'dependencies': completed_task_id})
        
        for task in dependent_tasks:
            # Check if all dependencies are completed
            dependencies = task.get('dependencies', [])
            all_completed = True
            
            for dep_id in dependencies:
                if dep_id == completed_task_id:
                    continue  # We know this one is completed
                
                dep_task = await self._get_task(dep_id)
                if not dep_task or dep_task.get('status') != TaskStatus.COMPLETED.value:
                    all_completed = False
                    break
            
            # If all dependencies are completed, update task status
            if all_completed and task.get('status') == TaskStatus.BLOCKED.value:
                updated_task = {
                    **task,
                    'status': TaskStatus.PENDING.value,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                
                await self._store_task(updated_task)
                
                # Send notification to assignee
                if updated_task.get('assignee'):
                    await self._send_task_notification(
                        user_id=updated_task['assignee'],
                        task_id=updated_task['task_id'],
                        notification_type='task_unblocked',
                        message=f"Task is now unblocked: {updated_task['title']}"
                    )

    async def _reassign_user_tasks(self, project_id: str, user_id: str) -> None:
        """Reassign tasks from a removed user to other project members."""
        # Get tasks assigned to the user in this project
        user_tasks = await self._search_tasks({'assignee': user_id, 'project_id': project_id})
        
        if not user_tasks:
            return  # No tasks to reassign
        
        # Get active project users (excluding the removed user)
        project_users = await self._get_project_users(project_id)
        active_users = [u for u in project_users if u.get('active', True) and u.get('user_id') != user_id]
        
        if not active_users:
            # No active users to reassign to, mark tasks as unassigned
            for task in user_tasks:
                updated_task = {
                    **task,
                    'assignee': None,
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                    'status': TaskStatus.PENDING.value
                }
                await self._store_task(updated_task)
            return
        
        # Simple round-robin reassignment
        for i, task in enumerate(user_tasks):
            new_assignee = active_users[i % len(active_users)]
            updated_task = {
                **task,
                'assignee': new_assignee['user_id'],
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            await self._store_task(updated_task)
            
            # Send notification to new assignee
            await self._send_task_notification(
                user_id=new_assignee['user_id'],
                task_id=task['task_id'],
                notification_type='task_reassigned',
                message=f"Task reassigned to you: {task['title']}"
            )

    async def _send_task_notification(self, user_id: str, task_id: str, notification_type: str, message: str) -> None:
        """Send a task-related notification to a user."""
        task = await self._get_task(task_id)
        if not task:
            logger.warning(f"Attempted to send notification for non-existent task {task_id}")
            return
        
        await self._send_notification(
            user_id=user_id,
            notification_type=notification_type,
            message=message,
            data={'task_id': task_id, 'project_id': task.get('project_id')}
        )

    async def _deliver_notification(self, notification: Dict[str, Any], channel: str) -> None:
        """Deliver a notification through a specific channel."""
        # This would integrate with actual notification services in production
        logger.info(f"Delivering notification {notification['notification_id']} via {channel} to user {notification['user_id']}")
        
        if channel == 'email':
            # Simulate email delivery
            logger.info(f"Email notification: {notification['message']}")
            # In production: await email_service.send_email(...)
        
        elif channel == 'in_app':
            # Simulate in-app notification
            logger.info(f"In-app notification: {notification['message']}")
            # In production: await notification_service.push_notification(...)
        
        elif channel == 'sms':
            # Simulate SMS notification
            logger.info(f"SMS notification: {notification['message']}")
            # In production: await sms_service.send_sms(...)

    # --- MCP Storage Methods ---

    async def _store_task(self, task: Dict[str, Any]) -> None:
        """Store a task in MCP."""
        entity = KnowledgeEntity(
            entity_type="collaboration_task",
            data=task,
            metadata={
                'agent_id': self.agent_id,
                'project_id': task['project_id'],
                'task_id': task['task_id'],
                'timestamp': time.time()
            }
        )
        await self.mcp_client.create_entities([entity])

    async def _get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a task from MCP."""
        results = await self.mcp_client.search_knowledge_graph_nodes(
            query={'data.task_id': task_id, 'entity_type': 'collaboration_task'}
        )
        if results and len(results) > 0:
            return results[0].data
        return None

    async def _search_tasks(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for tasks in MCP."""
        search_query = {'entity_type': 'collaboration_task'}
        for key, value in query.items():
            search_query[f'data.{key}'] = value
        
        results = await self.mcp_client.search_knowledge_graph_nodes(search_query)
        return [result.data for result in results]

    async def _store_project_user(self, user_entry: Dict[str, Any]) -> None:
        """Store a project user entry in MCP."""
        entity = KnowledgeEntity(
            entity_type="project_user",
            data=user_entry,
            metadata={
                'agent_id': self.agent_id,
                'project_id': user_entry['project_id'],
                'user_id': user_entry['user_id'],
                'timestamp': time.time()
            }
        )
        await self.mcp_client.create_entities([entity])

    async def _get_project_user(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a project user entry from MCP."""
        results = await self.mcp_client.search_knowledge_graph_nodes(
            query={
                'entity_type': 'project_user',
                'data.project_id': project_id,
                'data.user_id': user_id
            }
        )
        if results and len(results) > 0:
            return results[0].data
        return None

    async def _get_project_users(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all users for a project from MCP."""
        results = await self.mcp_client.search_knowledge_graph_nodes(
            query={'entity_type': 'project_user', 'data.project_id': project_id}
        )
        return [result.data for result in results]

    async def _get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a project from MCP."""
        results = await self.mcp_client.search_knowledge_graph_nodes(
            query={'entity_type': 'project', 'data.project_id': project_id}
        )
        if results and len(results) > 0:
            return results[0].data
        return None

    async def _get_project_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """Retrieve all tasks for a project from MCP."""
        results = await self.mcp_client.search_knowledge_graph_nodes(
            query={'entity_type': 'collaboration_task', 'data.project_id': project_id}
        )
        return [result.data for result in results]

    async def _get_project_activity(self, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent activity for a project from MCP."""
        results = await self.mcp_client.search_knowledge_graph_nodes(
            query={'entity_type': 'project_activity', 'data.project_id': project_id}
        )
        
        # Sort by timestamp (descending) and limit
        activities = [result.data for result in results]
        activities.sort(key=lambda a: a.get('timestamp', 0), reverse=True)
        
        return activities[:limit]

    async def _store_notification(self, notification: Dict[str, Any]) -> None:
        """Store a notification in MCP."""
        entity = KnowledgeEntity(
            entity_type="notification",
            data=notification,
            metadata={
                'agent_id': self.agent_id,
                'user_id': notification['user_id'],
                'notification_id': notification['notification_id'],
                'timestamp': time.time()
            }
        )
        await self.mcp_client.create_entities([entity])

    async def _store_activity(self, project_id: str, activity_type: str, description: str, user_id: str, data: Dict[str, Any] = None) -> None:
        """Store a project activity in MCP."""
        activity = {
            'activity_id': f"activity_{int(time.time())}_{hash(description) % 10000}",
            'project_id': project_id,
            'type': activity_type,
            'description': description,
            'user_id': user_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': data or {}
        }
        
        entity = KnowledgeEntity(
            entity_type="project_activity",
            data=activity,
            metadata={
                'agent_id': self.agent_id,
                'project_id': project_id,
                'timestamp': time.time()
            }
        )
        await self.mcp_client.create_entities([entity])

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute the stakeholder coordination action based on the input.
        
        Args:
            inputs: Dictionary containing:
                - action: Type of coordination action to perform
                - Additional parameters based on the action type
                
        Returns:
            AgentResult with the result of the coordination action
        """
        start_time = time.monotonic()
        
        try:
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": "Input validation failed", "details": validation_result.errors},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Extract action
            action = inputs['action']
            
            # Dispatch to appropriate handler based on action
            if action == 'create_task':
                result = await self._create_task(
                    project_id=inputs['project_id'],
                    task_data=inputs['task_data']
                )
                
                # Log activity
                await self._store_activity(
                    project_id=inputs['project_id'],
                    activity_type='task_created',
                    description=f"Task created: {result['title']}",
                    user_id=inputs.get('user_id', 'system'),
                    data={'task_id': result['task_id']}
                )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"task": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            elif action == 'update_task':
                result = await self._update_task(
                    task_id=inputs['task_id'],
                    task_data=inputs['task_data']
                )
                
                # Get project ID from task
                project_id = result.get('project_id')
                
                # Log activity
                if project_id:
                    await self._store_activity(
                        project_id=project_id,
                        activity_type='task_updated',
                        description=f"Task updated: {result['title']}",
                        user_id=inputs.get('user_id', 'system'),
                        data={'task_id': result['task_id']}
                    )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"task": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            elif action == 'assign_task':
                result = await self._assign_task(
                    task_id=inputs['task_id'],
                    user_id=inputs['user_id']
                )
                
                # Get project ID from task
                project_id = result.get('project_id')
                
                # Log activity
                if project_id:
                    await self._store_activity(
                        project_id=project_id,
                        activity_type='task_assigned',
                        description=f"Task assigned: {result['title']} to user {inputs['user_id']}",
                        user_id=inputs.get('assigner_id', 'system'),
                        data={'task_id': result['task_id'], 'assignee': inputs['user_id']}
                    )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"task": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            elif action == 'complete_task':
                result = await self._complete_task(
                    task_id=inputs['task_id']
                )
                
                # Get project ID from task
                project_id = result.get('project_id')
                
                # Log activity
                if project_id:
                    await self._store_activity(
                        project_id=project_id,
                        activity_type='task_completed',
                        description=f"Task completed: {result['title']}",
                        user_id=inputs.get('user_id', 'system'),
                        data={'task_id': result['task_id']}
                    )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"task": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            elif action == 'add_user':
                result = await self._add_user(
                    project_id=inputs['project_id'],
                    user_id=inputs['user_id'],
                    user_data=inputs['user_data']
                )
                
                # Log activity
                await self._store_activity(
                    project_id=inputs['project_id'],
                    activity_type='user_added',
                    description=f"User added: {inputs['user_id']}",
                    user_id=inputs.get('added_by', 'system'),
                    data={'user_id': inputs['user_id'], 'role': result['role']}
                )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"user": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            elif action == 'remove_user':
                result = await self._remove_user(
                    project_id=inputs['project_id'],
                    user_id=inputs['user_id']
                )
                
                # Log activity
                await self._store_activity(
                    project_id=inputs['project_id'],
                    activity_type='user_removed',
                    description=f"User removed: {inputs['user_id']}",
                    user_id=inputs.get('removed_by', 'system'),
                    data={'user_id': inputs['user_id']}
                )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"user": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            elif action == 'update_permissions':
                result = await self._update_permissions(
                    project_id=inputs['project_id'],
                    user_id=inputs['user_id'],
                    user_data=inputs['user_data']
                )
                
                # Log activity
                await self._store_activity(
                    project_id=inputs['project_id'],
                    activity_type='permissions_updated',
                    description=f"Permissions updated for user: {inputs['user_id']}",
                    user_id=inputs.get('updated_by', 'system'),
                    data={'user_id': inputs['user_id'], 'role': result['role']}
                )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"user": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            elif action == 'send_notification':
                result = await self._send_notification(
                    user_id=inputs['user_id'],
                    notification_type=inputs['notification_data']['type'],
                    message=inputs['notification_data']['message'],
                    data=inputs['notification_data'].get('data')
                )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"notification": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            elif action == 'get_project_status':
                result = await self._get_project_status(
                    project_id=inputs['project_id']
                )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"project_status": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            elif action == 'get_user_tasks':
                result = await self._get_user_tasks(
                    user_id=inputs['user_id'],
                    status=inputs.get('status')
                )
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"tasks": result},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
            else:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Unsupported action: {action}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
                
        except ValueError as e:
            # Handle expected errors (e.g., task not found)
            logger.warning(f"Value error in StakeholderCoordinatorAgent: {e}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": str(e)},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Error in StakeholderCoordinatorAgent: {e}", exc_info=True)
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"An unexpected error occurred: {str(e)}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )