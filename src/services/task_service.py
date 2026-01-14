"""Task service for business logic."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import TaskNotFoundError
from src.models.task import Task
from src.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    """Service class for task operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task."""
        task = Task(
            title=task_data.title,
            description=task_data.description,
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_task(self, task_id: UUID) -> Task:
        """Get a task by ID. Raises TaskNotFoundError if not found."""
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)  # type: ignore[arg-type]
        )
        task = result.scalar_one_or_none()
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    async def list_tasks(self) -> list[Task]:
        """List all tasks ordered by created_at descending."""
        result = await self.session.execute(
            select(Task).order_by(Task.created_at.desc())  # type: ignore[attr-defined]
        )
        return list(result.scalars().all())

    async def update_task(self, task_id: UUID, task_data: TaskUpdate) -> Task:
        """Update an existing task."""
        task = await self.get_task(task_id)

        update_data = task_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        task.updated_at = datetime.utcnow()

        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete_task(self, task_id: UUID) -> None:
        """Delete a task by ID. Raises TaskNotFoundError if not found."""
        task = await self.get_task(task_id)
        await self.session.delete(task)
        await self.session.commit()
