"""Task Pydantic schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str) -> str:
        """Validate title is not whitespace-only and trim whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or whitespace only")
        return stripped


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    is_completed: bool | None = None

    @field_validator("title")
    @classmethod
    def title_not_whitespace(cls, v: str | None) -> str | None:
        """Validate title is not whitespace-only and trim whitespace."""
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or whitespace only")
        return stripped


class TaskResponse(BaseModel):
    """Schema for task response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime
