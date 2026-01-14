"""Task SQLModel entity."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Task(SQLModel, table=True):
    """Task entity for tracking work items."""

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
        description="Unique task identifier",
    )

    title: str = Field(
        max_length=200,
        nullable=False,
        description="Brief description of the work (1-200 chars)",
    )

    description: str | None = Field(
        default=None,
        nullable=True,
        description="Detailed information about the task",
    )

    is_completed: bool = Field(
        default=False,
        nullable=False,
        description="Completion status (false = not done, true = done)",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="UTC timestamp when task was created",
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="UTC timestamp of last modification",
    )
