"""Task API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from src.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    """Dependency to get TaskService with injected session."""
    return TaskService(session)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Create a new task."""
    task = await service.create_task(task_data)
    return TaskResponse.model_validate(task)


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    """List all tasks ordered by creation date (newest first)."""
    tasks = await service.list_tasks()
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Get a task by ID."""
    task = await service.get_task(task_id)
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Update an existing task."""
    task = await service.update_task(task_id, task_data)
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> None:
    """Delete a task by ID."""
    await service.delete_task(task_id)
