"""Unit tests for Task model validation."""

from datetime import datetime
from uuid import UUID

from src.models.task import Task


class TestTaskModel:
    """Tests for Task SQLModel entity."""

    def test_task_has_all_required_fields(self):
        """Task should have id, title, description, is_completed, created_at, updated_at."""
        task = Task(title="Test task")

        assert hasattr(task, "id")
        assert hasattr(task, "title")
        assert hasattr(task, "description")
        assert hasattr(task, "is_completed")
        assert hasattr(task, "created_at")
        assert hasattr(task, "updated_at")

    def test_task_id_is_uuid(self):
        """Task ID should be a UUID."""
        task = Task(title="Test task")

        assert isinstance(task.id, UUID)

    def test_task_id_is_auto_generated(self):
        """Task ID should be auto-generated if not provided."""
        task1 = Task(title="Task 1")
        task2 = Task(title="Task 2")

        assert task1.id is not None
        assert task2.id is not None
        assert task1.id != task2.id

    def test_task_title_is_required(self):
        """Task should store title correctly."""
        task = Task(title="Write documentation")

        assert task.title == "Write documentation"

    def test_task_description_is_optional(self):
        """Task description should be optional and default to None."""
        task = Task(title="Test task")

        assert task.description is None

    def test_task_description_can_be_set(self):
        """Task description can be set."""
        task = Task(title="Test task", description="Detailed description")

        assert task.description == "Detailed description"

    def test_task_is_completed_defaults_to_false(self):
        """Task is_completed should default to False."""
        task = Task(title="Test task")

        assert task.is_completed is False

    def test_task_is_completed_can_be_set_true(self):
        """Task is_completed can be set to True."""
        task = Task(title="Test task", is_completed=True)

        assert task.is_completed is True

    def test_task_created_at_is_auto_set(self):
        """Task created_at should be auto-set to current time."""
        task = Task(title="Test task")

        assert task.created_at is not None
        assert isinstance(task.created_at, datetime)

    def test_task_updated_at_is_auto_set(self):
        """Task updated_at should be auto-set to current time."""
        task = Task(title="Test task")

        assert task.updated_at is not None
        assert isinstance(task.updated_at, datetime)

    def test_task_timestamps_are_close_to_creation(self):
        """Task timestamps should be close to the time of creation."""
        before = datetime.utcnow()
        task = Task(title="Test task")
        after = datetime.utcnow()

        assert before <= task.created_at <= after
        assert before <= task.updated_at <= after
