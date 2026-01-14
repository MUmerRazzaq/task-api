"""Unit tests for TaskService."""

from uuid import uuid4

import pytest

from src.exceptions import TaskNotFoundError
from src.schemas.task import TaskCreate, TaskUpdate
from src.services.task_service import TaskService


class TestTaskServiceCreate:
    """Tests for TaskService.create_task method."""

    async def test_create_task_with_valid_data(self, test_session):
        """TaskService should create a task with valid data."""
        service = TaskService(test_session)
        task_data = TaskCreate(
            title="Write documentation",
            description="Create API docs",
        )

        result = await service.create_task(task_data)

        assert result.title == "Write documentation"
        assert result.description == "Create API docs"
        assert result.is_completed is False
        assert result.id is not None

    async def test_create_task_title_only(self, test_session):
        """TaskService should create a task with title only."""
        service = TaskService(test_session)
        task_data = TaskCreate(title="Simple task")

        result = await service.create_task(task_data)

        assert result.title == "Simple task"
        assert result.description is None

    async def test_create_task_persists_to_database(self, test_session):
        """Created task should be persisted to the database."""
        service = TaskService(test_session)
        task_data = TaskCreate(title="Persistent task")

        created = await service.create_task(task_data)
        retrieved = await service.get_task(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Persistent task"


class TestTaskServiceGet:
    """Tests for TaskService.get_task method."""

    async def test_get_existing_task(self, test_session):
        """TaskService should retrieve an existing task by ID."""
        service = TaskService(test_session)
        task_data = TaskCreate(title="Existing task")
        created = await service.create_task(task_data)

        result = await service.get_task(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.title == "Existing task"

    async def test_get_nonexistent_task_raises_error(self, test_session):
        """TaskService should raise TaskNotFoundError for non-existent task."""
        service = TaskService(test_session)
        fake_id = uuid4()

        with pytest.raises(TaskNotFoundError) as exc_info:
            await service.get_task(fake_id)

        assert exc_info.value.task_id == fake_id


class TestTaskServiceList:
    """Tests for TaskService.list_tasks method."""

    async def test_list_tasks_empty(self, test_session):
        """TaskService should return empty list when no tasks exist."""
        service = TaskService(test_session)

        result = await service.list_tasks()

        assert result == []

    async def test_list_tasks_returns_all_tasks(self, test_session):
        """TaskService should return all tasks."""
        service = TaskService(test_session)
        await service.create_task(TaskCreate(title="Task 1"))
        await service.create_task(TaskCreate(title="Task 2"))
        await service.create_task(TaskCreate(title="Task 3"))

        result = await service.list_tasks()

        assert len(result) == 3
        titles = [t.title for t in result]
        assert "Task 1" in titles
        assert "Task 2" in titles
        assert "Task 3" in titles

    async def test_list_tasks_ordered_by_created_at_desc(self, test_session):
        """TaskService should return tasks ordered by created_at descending."""
        import asyncio

        service = TaskService(test_session)

        # Create tasks with small delays to ensure different timestamps
        await service.create_task(TaskCreate(title="First"))
        await asyncio.sleep(0.01)
        await service.create_task(TaskCreate(title="Second"))
        await asyncio.sleep(0.01)
        await service.create_task(TaskCreate(title="Third"))

        result = await service.list_tasks()

        # Newest first
        assert result[0].title == "Third"
        assert result[1].title == "Second"
        assert result[2].title == "First"


class TestTaskServiceUpdate:
    """Tests for TaskService.update_task method."""

    async def test_update_task_full(self, test_session):
        """TaskService should update all task fields."""
        service = TaskService(test_session)
        created = await service.create_task(
            TaskCreate(title="Original", description="Original desc")
        )

        update_data = TaskUpdate(
            title="Updated",
            description="Updated desc",
            is_completed=True,
        )
        result = await service.update_task(created.id, update_data)

        assert result.title == "Updated"
        assert result.description == "Updated desc"
        assert result.is_completed is True

    async def test_update_task_partial(self, test_session):
        """TaskService should support partial updates."""
        service = TaskService(test_session)
        created = await service.create_task(
            TaskCreate(title="Original", description="Keep this")
        )

        result = await service.update_task(
            created.id,
            TaskUpdate(title="New title"),
        )

        assert result.title == "New title"
        assert result.description == "Keep this"
        assert result.is_completed is False

    async def test_update_task_updates_timestamp(self, test_session):
        """TaskService should update updated_at on changes."""
        import asyncio

        service = TaskService(test_session)
        created = await service.create_task(TaskCreate(title="Test"))
        original_updated = created.updated_at

        await asyncio.sleep(0.01)

        result = await service.update_task(
            created.id,
            TaskUpdate(title="Updated"),
        )

        assert result.updated_at > original_updated
        assert result.created_at == created.created_at

    async def test_update_nonexistent_task_raises_error(self, test_session):
        """TaskService should raise TaskNotFoundError for non-existent task."""
        service = TaskService(test_session)
        fake_id = uuid4()

        with pytest.raises(TaskNotFoundError):
            await service.update_task(fake_id, TaskUpdate(title="Test"))


class TestTaskServiceDelete:
    """Tests for TaskService.delete_task method."""

    async def test_delete_existing_task(self, test_session):
        """TaskService should delete an existing task."""
        service = TaskService(test_session)
        created = await service.create_task(TaskCreate(title="To delete"))

        await service.delete_task(created.id)

        with pytest.raises(TaskNotFoundError):
            await service.get_task(created.id)

    async def test_delete_nonexistent_task_raises_error(self, test_session):
        """TaskService should raise TaskNotFoundError for non-existent task."""
        service = TaskService(test_session)
        fake_id = uuid4()

        with pytest.raises(TaskNotFoundError):
            await service.delete_task(fake_id)

    async def test_delete_only_removes_specified_task(self, test_session):
        """TaskService delete should only remove the specified task."""
        service = TaskService(test_session)
        task1 = await service.create_task(TaskCreate(title="Task 1"))
        task2 = await service.create_task(TaskCreate(title="Task 2"))

        await service.delete_task(task1.id)

        # task2 should still exist
        remaining = await service.get_task(task2.id)
        assert remaining.title == "Task 2"

        # task1 should be gone
        with pytest.raises(TaskNotFoundError):
            await service.get_task(task1.id)
