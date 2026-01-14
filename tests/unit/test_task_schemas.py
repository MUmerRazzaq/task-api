"""Unit tests for Task Pydantic schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.task import TaskCreate, TaskResponse


class TestTaskCreateSchema:
    """Tests for TaskCreate schema validation."""

    def test_valid_task_with_title_only(self):
        """TaskCreate should accept valid title."""
        task_data = TaskCreate(title="Valid title")

        assert task_data.title == "Valid title"
        assert task_data.description is None

    def test_valid_task_with_title_and_description(self):
        """TaskCreate should accept title and description."""
        task_data = TaskCreate(
            title="Valid title",
            description="A detailed description",
        )

        assert task_data.title == "Valid title"
        assert task_data.description == "A detailed description"

    def test_title_whitespace_is_trimmed(self):
        """TaskCreate should trim leading/trailing whitespace from title."""
        task_data = TaskCreate(title="  Padded title  ")

        assert task_data.title == "Padded title"

    def test_empty_title_raises_validation_error(self):
        """TaskCreate should reject empty string title."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="")

        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert any("title" in str(e["loc"]) for e in errors)

    def test_whitespace_only_title_raises_validation_error(self):
        """TaskCreate should reject whitespace-only title."""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title="   ")

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_title_max_length_200_allowed(self):
        """TaskCreate should accept title of exactly 200 characters."""
        title = "a" * 200
        task_data = TaskCreate(title=title)

        assert len(task_data.title) == 200

    def test_title_over_200_chars_raises_validation_error(self):
        """TaskCreate should reject title over 200 characters."""
        title = "a" * 201

        with pytest.raises(ValidationError) as exc_info:
            TaskCreate(title=title)

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_description_can_be_none(self):
        """TaskCreate should allow None description."""
        task_data = TaskCreate(title="Title", description=None)

        assert task_data.description is None

    def test_description_can_be_long(self):
        """TaskCreate should allow long descriptions."""
        long_description = "x" * 10000
        task_data = TaskCreate(title="Title", description=long_description)

        assert task_data.description == long_description


class TestTaskUpdateSchema:
    """Tests for TaskUpdate schema validation."""

    def test_update_all_fields_optional(self):
        """TaskUpdate should allow all fields to be optional."""
        from src.schemas.task import TaskUpdate

        update = TaskUpdate()
        assert update.title is None
        assert update.description is None
        assert update.is_completed is None

    def test_update_with_title_only(self):
        """TaskUpdate should accept title only."""
        from src.schemas.task import TaskUpdate

        update = TaskUpdate(title="New title")
        assert update.title == "New title"
        assert update.description is None
        assert update.is_completed is None

    def test_update_with_is_completed_only(self):
        """TaskUpdate should accept is_completed only."""
        from src.schemas.task import TaskUpdate

        update = TaskUpdate(is_completed=True)
        assert update.title is None
        assert update.is_completed is True

    def test_update_title_whitespace_is_trimmed(self):
        """TaskUpdate should trim title whitespace."""
        from src.schemas.task import TaskUpdate

        update = TaskUpdate(title="  Padded title  ")
        assert update.title == "Padded title"

    def test_update_empty_title_raises_error(self):
        """TaskUpdate should reject empty title."""
        from src.schemas.task import TaskUpdate

        with pytest.raises(ValidationError):
            TaskUpdate(title="")

    def test_update_whitespace_title_raises_error(self):
        """TaskUpdate should reject whitespace-only title."""
        from src.schemas.task import TaskUpdate

        with pytest.raises(ValidationError):
            TaskUpdate(title="   ")


class TestTaskResponseSchema:
    """Tests for TaskResponse schema."""

    def test_task_response_has_all_fields(self):
        """TaskResponse should have all required fields."""
        from datetime import datetime
        from uuid import uuid4

        response = TaskResponse(
            id=uuid4(),
            title="Test",
            description="Description",
            is_completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert response.id is not None
        assert response.title == "Test"
        assert response.description == "Description"
        assert response.is_completed is False
        assert response.created_at is not None
        assert response.updated_at is not None

    def test_task_response_from_orm_model(self):
        """TaskResponse should work with from_attributes=True."""
        from src.models.task import Task

        task = Task(title="Test task", description="Test description")
        response = TaskResponse.model_validate(task)

        assert response.id == task.id
        assert response.title == task.title
        assert response.description == task.description
        assert response.is_completed == task.is_completed
