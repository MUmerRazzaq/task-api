# Research: Task Management API

**Feature**: 001-task-api
**Date**: 2026-01-13
**Phase**: Phase 0 - Research & Discovery

## Purpose

This document consolidates research findings to resolve all NEEDS CLARIFICATION items from the Technical Context and establish best practices for the technology stack.

---

## 1. FastAPI Project Structure

### Decision: Layered Architecture with Clear Separation

**Rationale**:
- FastAPI best practices recommend separating concerns into distinct layers
- Models, schemas, services, and API routers each have single responsibility
- Easier to test each layer in isolation
- Aligns with constitution principle IV (Single Responsibility)

**Structure**:
```
src/
├── models/          # SQLModel database entities
├── schemas/         # Pydantic request/response models
├── services/        # Business logic layer
├── api/             # FastAPI routers (HTTP layer)
├── database.py      # DB connection and session management
└── main.py          # Application entry point
```

**Key Pattern**:
- **models/** contains SQLModel classes (both ORM and table definitions)
- **schemas/** contains Pydantic models for API contracts (separate from DB models to allow different validation rules and prevent exposing internal DB structure)
- **services/** contains business logic that's framework-agnostic
- **api/** contains FastAPI route handlers that delegate to services

**Alternatives Considered**:
- **Flat structure**: Rejected - harder to maintain as project grows, violates single responsibility
- **Feature-based structure**: Rejected - overkill for MVP with single entity type

**References**:
- FastAPI docs emphasize separation of path operations from business logic
- SQLModel docs show pattern of using separate models for API vs database

---

## 2. Async Patterns in FastAPI

### Decision: Use async/await for all database operations

**Rationale**:
- PostgreSQL operations are I/O-bound and benefit from async patterns
- FastAPI natively supports async endpoints
- Better performance under concurrent load (requirement: 100 concurrent users)
- SQLModel supports async via SQLAlchemy async engine

**Implementation Pattern**:
```python
# Async endpoint
@app.get("/tasks/{task_id}")
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    return task

# Async database session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
```

**Key Points**:
- Use `async def` for all endpoint functions
- Use `AsyncSession` from SQLAlchemy
- Use `await` for all database queries
- Use async context managers for session lifecycle

**Alternatives Considered**:
- **Sync-only**: Rejected - poorer performance under concurrent load, not aligned with FastAPI's strengths
- **Mixed sync/async**: Rejected - inconsistent patterns, harder to maintain

**References**:
- FastAPI docs show async pattern as default for modern applications
- SQLModel can work with SQLAlchemy's async engine

---

## 3. Database Session Management

### Decision: Dependency injection with FastAPI Depends()

**Rationale**:
- FastAPI's dependency injection system handles session lifecycle automatically
- Ensures proper session cleanup (commit/rollback) even on errors
- Makes testing easier (can override session dependency with test DB)
- Prevents common session management bugs

**Implementation Pattern**:
```python
# database.py
from sqlmodel import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# In router
from fastapi import Depends

@app.post("/tasks")
async def create_task(
    task_data: TaskCreate,
    session: AsyncSession = Depends(get_session)
):
    # session is automatically provided and cleaned up
    pass
```

**Key Points**:
- Use FastAPI's `Depends()` to inject session into endpoints
- Session automatically commits on success, rolls back on exception
- `expire_on_commit=False` prevents issues with accessing objects after commit
- Connection pooling handled by SQLAlchemy engine

**Alternatives Considered**:
- **Manual session management**: Rejected - error-prone, boilerplate-heavy
- **Global session**: Rejected - not thread-safe, causes test isolation issues

**References**:
- FastAPI dependency injection docs
- SQLModel integration with FastAPI patterns

---

## 4. Testing Strategy with pytest

### Decision: Three-tier test organization with fixtures

**Rationale**:
- Clear separation of test types (contract, integration, unit)
- Pytest fixtures provide clean setup/teardown
- Test database isolation prevents test interference
- Follows constitution testing requirements

**Test Organization**:
```
tests/
├── conftest.py              # Shared fixtures
├── contract/                # API endpoint tests
│   └── test_task_api.py
├── integration/             # Multi-component tests
│   └── test_task_flow.py
└── unit/                    # Business logic tests
    └── test_task_service.py
```

**Key Fixtures Pattern**:
```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine("postgresql+asyncpg://localhost/test_db")
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture
async def test_session(test_engine):
    """Provide test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture
def client(test_session):
    """Provide test client with overridden DB session."""
    def override_get_session():
        return test_session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()
```

**Key Points**:
- Use `TestClient` from FastAPI for contract tests
- Override database session dependency for test isolation
- Use `pytest-asyncio` for async test support
- Each test uses fresh database state (via transaction rollback or table recreation)

**Alternatives Considered**:
- **Single test directory**: Rejected - harder to run specific test types
- **Mock-heavy approach**: Rejected - doesn't test real database interactions
- **Shared test database**: Rejected - tests interfere with each other

**References**:
- pytest fixture documentation
- FastAPI testing guide with TestClient
- SQLModel testing patterns

---

## 5. Environment Configuration

### Decision: Use python-dotenv with .env files

**Rationale**:
- Simple and standard for Python projects
- Keeps secrets out of code
- Different configurations for dev/test/prod
- Widely supported tooling

**Implementation Pattern**:
```python
# .env (not committed)
DATABASE_URL=postgresql+asyncpg://user:pass@neon.tech/taskdb
LOG_LEVEL=INFO

# .env.test (for CI/testing)
DATABASE_URL=postgresql+asyncpg://localhost/test_taskdb
LOG_LEVEL=DEBUG

# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
```

**Key Points**:
- Use Pydantic `BaseSettings` for type-safe configuration
- Separate `.env` files for different environments
- Add `.env` to `.gitignore`
- Provide `.env.example` with dummy values for documentation

**Alternatives Considered**:
- **Config files (YAML/JSON)**: Rejected - more complex, secrets still need environment variables
- **Environment variables only**: Rejected - harder for local development

**References**:
- Pydantic settings management
- FastAPI configuration best practices

---

## 6. Error Handling Strategy

### Decision: Consistent error response format with custom exception handlers

**Rationale**:
- Constitution requires consistent error format
- FastAPI exception handlers provide centralized error handling
- Clear error codes help with debugging and client-side handling

**Implementation Pattern**:
```python
# errors.py
from fastapi import HTTPException

class TaskNotFoundError(HTTPException):
    def __init__(self, task_id: int):
        super().__init__(
            status_code=404,
            detail={
                "error_code": "TASK_NOT_FOUND",
                "message": f"Task with id {task_id} not found"
            }
        )

# Error handler
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "detail": exc.detail["message"],
            "error_code": exc.detail["error_code"]
        }
    )
```

**Error Response Format** (per constitution):
```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "field_errors": {}  // Optional for validation errors
}
```

**Key Points**:
- Custom exception classes for domain errors
- Centralized exception handlers in main.py
- Pydantic validation errors automatically formatted
- No stack traces in production (FastAPI handles this)

**Alternatives Considered**:
- **Status-only responses**: Rejected - insufficient information for debugging
- **Varied error formats**: Rejected - violates consistency requirement

**References**:
- FastAPI exception handling docs
- Constitution API Design Standards

---

## 7. Data Validation Strategy

### Decision: Pydantic models for request/response, SQLModel for database

**Rationale**:
- Separation allows different validation rules for API vs database
- API schemas can hide internal fields (e.g., soft-delete flags)
- Prevents exposing database implementation details
- Aligns with single responsibility principle

**Implementation Pattern**:
```python
# models/task.py (Database)
from sqlmodel import Field, SQLModel
from datetime import datetime
from uuid import UUID, uuid4

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    description: str | None = None
    is_completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# schemas/task.py (API)
from pydantic import BaseModel, Field, field_validator

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None

    @field_validator('title')
    def title_not_whitespace(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty or whitespace only')
        return v.strip()

class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows creation from ORM models
```

**Key Points**:
- Use `Field()` for constraints (min_length, max_length)
- Use `field_validator` for custom validation logic
- Separate create/update/response schemas
- `from_attributes=True` enables easy conversion from DB models

**Alternatives Considered**:
- **Single model for DB and API**: Rejected - couples API contract to database schema
- **Manual validation**: Rejected - error-prone, duplicates Pydantic functionality

**References**:
- Pydantic v2 validators
- SQLModel field constraints
- FastAPI request/response models

---

## 8. Database Migrations

### Decision: Use Alembic (defer until needed)

**Rationale**:
- For MVP, can use `SQLModel.metadata.create_all()` for initial setup
- Alembic required when schema changes in production
- SQLModel integrates with Alembic seamlessly
- Defer complexity until actually needed (simplicity principle)

**Initial Approach (MVP)**:
```python
# database.py
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

**Migration Strategy (when needed)**:
```bash
# Initialize Alembic
alembic init alembic

# Generate migration from model changes
alembic revision --autogenerate -m "Add tasks table"

# Apply migration
alembic upgrade head
```

**Key Points**:
- Start with `create_all()` for simplicity
- Add Alembic when first schema change needed in production
- Keep migrations in version control
- Test migrations on staging before production

**Alternatives Considered**:
- **Alembic from day one**: Rejected - premature for MVP
- **Manual SQL migrations**: Rejected - error-prone, no automation

**References**:
- SQLModel database initialization
- Alembic integration with SQLAlchemy

---

## 9. UUID vs Auto-increment IDs

### Decision: Use UUIDs for task identifiers

**Rationale**:
- Constitution specifies UUIDs (not auto-incrementing integers)
- Better for distributed systems (no coordination needed)
- No information leakage (can't guess next ID)
- PostgreSQL has native UUID support with good performance

**Implementation Pattern**:
```python
from uuid import UUID, uuid4
from sqlmodel import Field

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
```

**Key Points**:
- Use Python's `uuid4()` for generation
- PostgreSQL `uuid` type for storage
- String representation in API responses (automatic with Pydantic)

**Alternatives Considered**:
- **Auto-increment integers**: Rejected - violates constitution requirement
- **Custom ID generation**: Rejected - unnecessary complexity

**References**:
- Constitution API Design Standards
- SQLModel UUID field examples

---

## 10. Neon Postgres Configuration

### Decision: Use connection pooling with asyncpg driver

**Rationale**:
- Neon is serverless PostgreSQL (requires efficient connection management)
- asyncpg is fastest async PostgreSQL driver for Python
- Connection pooling reduces connection overhead
- Neon has connection limits that pooling helps manage

**Implementation Pattern**:
```python
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://user:pass@neon.tech/taskdb"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Logs SQL (disable in production)
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connection health
)
```

**Key Points**:
- Use `postgresql+asyncpg://` URL scheme
- Configure appropriate pool size (5-10 for single instance)
- Enable `pool_pre_ping` to handle stale connections
- Use separate connection string for test database

**Alternatives Considered**:
- **psycopg3**: Rejected - asyncpg has better async performance
- **No pooling**: Rejected - inefficient for Neon's connection model

**References**:
- Neon documentation on connection pooling
- SQLAlchemy async engine configuration
- asyncpg driver documentation

---

## Summary of Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| Project Structure | Layered (models/schemas/services/api) | Single responsibility, testability |
| Async Pattern | Async/await for all I/O | Performance under concurrent load |
| Session Management | FastAPI dependency injection | Automatic lifecycle, testability |
| Testing | Three-tier with pytest fixtures | Constitution compliance, isolation |
| Configuration | python-dotenv + Pydantic Settings | Simple, type-safe, standard |
| Error Handling | Custom exceptions with handlers | Consistent format, centralized |
| Validation | Separate Pydantic schemas | API/DB separation, flexibility |
| Migrations | Defer Alembic until needed | MVP simplicity |
| IDs | UUIDs | Constitution requirement |
| Database | Neon + asyncpg + pooling | Performance, serverless-friendly |

All NEEDS CLARIFICATION items from Technical Context are now resolved.
