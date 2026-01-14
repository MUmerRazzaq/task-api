"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.tasks import router as tasks_router
from src.database import close_db, init_db
from src.exceptions import TaskNotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="Task Management API",
    description="RESTful API for managing tasks",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(
    request: Request, exc: TaskNotFoundError
) -> JSONResponse:
    """Handle TaskNotFoundError with consistent error format."""
    return JSONResponse(
        status_code=404,
        content={
            "detail": exc.message,
            "error_code": "TASK_NOT_FOUND",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors with consistent error format."""
    field_errors: dict[str, list[str]] = {}
    for error in exc.errors():
        # Get the field name from the location tuple
        loc = error.get("loc", ())
        field = str(loc[-1]) if loc else "unknown"
        if field not in field_errors:
            field_errors[field] = []
        field_errors[field].append(str(error["msg"]))

    return JSONResponse(
        status_code=400,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "field_errors": field_errors,
        },
    )


# Register routers
app.include_router(tasks_router)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy"}
