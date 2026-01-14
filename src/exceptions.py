"""Custom exceptions for the Task API."""

from uuid import UUID


class TaskNotFoundError(Exception):
    """Raised when a task is not found in the database."""

    def __init__(self, task_id: UUID):
        self.task_id = task_id
        self.message = f"Task with id {task_id} not found"
        super().__init__(self.message)
