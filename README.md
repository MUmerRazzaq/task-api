# Task Management API

A RESTful API for managing tasks, built with FastAPI, SQLModel, and PostgreSQL.

## Demo Video

> **[Watch the Demo Video](https://www.loom.com/share/ad0db137d9944d128f6d59c44a6fc58f)**

## Features

- **Create Tasks**: Add new tasks with title and optional description
- **View Tasks**: List all tasks or get a specific task by ID
- **Update Tasks**: Modify task details or mark as completed
- **Delete Tasks**: Remove tasks permanently
- **Validation**: Title validation (1-200 characters, non-empty)
- **Error Handling**: Consistent error responses with error codes

## Tech Stack

- **Python 3.11+** - Modern Python with type hints
- **FastAPI** - High-performance async web framework
- **SQLModel** - SQL database ORM combining SQLAlchemy and Pydantic
- **PostgreSQL** - Production database (Neon serverless PostgreSQL)
- **uv** - Fast Python package manager
- **pytest** - Testing framework with 90%+ coverage

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL database (or Neon account)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd task-api

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### Environment Variables

Create a `.env` file with:

```env
# Database configuration
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname

# Application settings
LOG_LEVEL=INFO
```

### Run the Server

```bash
# Development mode with auto-reload
uv run uvicorn src.main:app --reload --port 8000

# Production mode
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Access the API

- **API**: http://localhost:8000
- **Interactive Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Endpoints

| Method | Endpoint      | Description         |
| ------ | ------------- | ------------------- |
| GET    | `/tasks`      | List all tasks      |
| POST   | `/tasks`      | Create a new task   |
| GET    | `/tasks/{id}` | Get a specific task |
| PUT    | `/tasks/{id}` | Update a task       |
| DELETE | `/tasks/{id}` | Delete a task       |
| GET    | `/health`     | Health check        |

### Example Requests

**Create a Task**

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Write documentation", "description": "Create API docs"}'
```

**List All Tasks**

```bash
curl http://localhost:8000/tasks
```

**Get a Task**

```bash
curl http://localhost:8000/tasks/{task_id}
```

**Update a Task**

```bash
curl -X PUT http://localhost:8000/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{"is_completed": true}'
```

**Delete a Task**

```bash
curl -X DELETE http://localhost:8000/tasks/{task_id}
```

## Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test directory
uv run pytest tests/unit/
uv run pytest tests/contract/
uv run pytest tests/integration/
```

## Code Quality

```bash
# Linting
uv run ruff check src/ tests/

# Auto-fix linting issues
uv run ruff check --fix src/ tests/

# Type checking
uv run mypy src/

# Format code
uv run ruff format src/ tests/
```

## Project Structure

```
task-api/
├── src/
│   ├── api/              # FastAPI routers
│   │   └── tasks.py      # Task endpoints
│   ├── models/           # SQLModel entities
│   │   └── task.py       # Task model
│   ├── schemas/          # Pydantic schemas
│   │   └── task.py       # Request/response schemas
│   ├── services/         # Business logic
│   │   └── task_service.py
│   ├── config.py         # Application settings
│   ├── database.py       # Database connection
│   ├── exceptions.py     # Custom exceptions
│   └── main.py           # FastAPI application
├── tests/
│   ├── contract/         # API contract tests
│   ├── integration/      # Integration tests
│   └── unit/             # Unit tests
├── specs/                # Design documents
│   └── 001-task-api/
│       ├── spec.md       # Requirements
│       ├── plan.md       # Architecture
│       └── tasks.md      # Implementation tasks
├── .env.example          # Environment template
├── pyproject.toml        # Project configuration
└── README.md             # This file
```

## Response Format

**Success Response (Task)**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Write documentation",
  "description": "Create API docs",
  "is_completed": false,
  "created_at": "2026-01-13T10:30:00Z",
  "updated_at": "2026-01-13T10:30:00Z"
}
```

**Error Response**

```json
{
  "detail": "Task with id 550e8400-... not found",
  "error_code": "TASK_NOT_FOUND"
}
```

**Validation Error Response**

```json
{
  "detail": "Validation error",
  "error_code": "VALIDATION_ERROR",
  "field_errors": {
    "title": ["Title cannot be empty or whitespace only"]
  }
}
```

## License

MIT License
