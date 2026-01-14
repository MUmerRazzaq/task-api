# Quickstart Guide: Task Management API

**Feature**: 001-task-api
**Date**: 2026-01-13
**For**: Developers implementing the Task Management API

## Prerequisites

- Python 3.11 or higher
- uv package manager (already installed)
- Neon Postgres account (or local PostgreSQL instance)
- Git (for version control)

---

## What is uv?

**uv** is an extremely fast Python package and project manager written in Rust. It replaces pip, pip-tools, pipx, poetry, pyenv, and virtualenv with a single, unified tool.

**Key Benefits**:
- **10-100x faster** than pip for package installation
- **Built-in virtual environment management** (no need for `venv`)
- **Lock file support** for reproducible builds (`uv.lock`)
- **Project management** with `pyproject.toml`
- **Tool execution** without installation (`uvx`)
- **No activation needed** - `uv run` handles everything

---

## Project Setup

### 1. Initialize Project with uv

```bash
# Create and initialize project as a package
uv init --package task-api
cd task-api
```

**What `uv init --package` creates**:
```
task-api/
├── pyproject.toml          # Project configuration
├── README.md               # Project documentation
├── .python-version         # Python version (3.12 by default)
└── src/
    └── task_api/
        └── __init__.py
```

### 2. Set Python Version

```bash
# Specify Python 3.11
echo "3.11" > .python-version

# uv automatically uses this version (downloads if needed)
```

### 3. Restructure for Our Architecture

```bash
# Rename the auto-generated package directory
mv src/task_api src/task_api_temp

# Create our desired structure
mkdir -p src/models src/schemas src/services src/api

# Create __init__.py files
touch src/__init__.py
touch src/models/__init__.py
touch src/schemas/__init__.py
touch src/services/__init__.py
touch src/api/__init__.py

# Remove temp directory
rm -rf src/task_api_temp

# Create test directories
mkdir -p tests/contract tests/integration tests/unit
touch tests/__init__.py
```

### 4. Add Dependencies

```bash
# Add production dependencies
uv add fastapi \
    "uvicorn[standard]" \
    sqlmodel \
    asyncpg \
    "psycopg[binary]" \
    pydantic \
    pydantic-settings \
    python-dotenv

# Add development dependencies
uv add --dev \
    pytest \
    pytest-asyncio \
    httpx \
    ruff \
    mypy
```

**What happens**:
- Creates `.venv/` virtual environment automatically
- Installs all packages (extremely fast)
- Updates `pyproject.toml` with dependencies
- Creates/updates `uv.lock` for reproducible installs

### 5. Verify Installation

```bash
# Check that packages are installed
uv pip list

# Verify Python version
uv run python --version
```

### 6. Configure pyproject.toml

Your `pyproject.toml` should look like:

```toml
[project]
name = "task-api"
version = "0.1.0"
description = "RESTful Task Management API with FastAPI and SQLModel"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlmodel>=0.0.14",
    "asyncpg>=0.29.0",
    "psycopg[binary]>=3.1.16",
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.4",
    "pytest-asyncio>=0.23.3",
    "httpx>=0.26.0",
    "ruff>=0.5.0",
    "mypy>=1.8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = []

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

### 7. Environment Configuration

```bash
# Create .env file
cat > .env << 'EOF'
# Database configuration
DATABASE_URL=postgresql+asyncpg://user:pass@host/taskdb

# Application settings
LOG_LEVEL=INFO
EOF

# Create .env.example (safe to commit)
cat > .env.example << 'EOF'
# Database configuration
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname

# Application settings
LOG_LEVEL=INFO
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environment
.venv/
venv/
ENV/

# uv
uv.lock

# Environment variables
.env
.env.test
.env.local

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite3

# OS
.DS_Store
Thumbs.db
EOF
```

---

## Final Project Structure

After setup, your structure should be:

```
task-api/
├── src/
│   ├── __init__.py
│   ├── models/              # SQLModel database entities
│   │   └── __init__.py
│   ├── schemas/             # Pydantic request/response models
│   │   └── __init__.py
│   ├── services/            # Business logic layer
│   │   └── __init__.py
│   ├── api/                # FastAPI routers
│   │   └── __init__.py
│   ├── database.py         # DB connection and session management
│   └── main.py             # Application entry point
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── contract/           # API endpoint tests
│   ├── integration/        # Multi-component tests
│   └── unit/              # Business logic tests
├── specs/                  # Design documents
│   └── 001-task-api/
│       ├── spec.md
│       ├── plan.md
│       ├── research.md
│       ├── data-model.md
│       ├── quickstart.md (this file)
│       └── contracts/
├── .env                    # Environment variables (not committed)
├── .env.example           # Example environment variables
├── .gitignore             # Git ignore rules
├── .python-version        # Python version (3.11)
├── pyproject.toml         # Project config and dependencies
├── uv.lock               # Dependency lockfile
└── README.md             # Project documentation
```

---

## uv Command Reference

### Daily Development Commands

```bash
# Run development server (no activation needed)
uv run uvicorn src.main:app --reload --port 8000

# Run tests
uv run pytest

# Run specific test directory
uv run pytest tests/unit/

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Linting
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/

# Type checking
uv run mypy src/
```

### Dependency Management

```bash
# Add a production dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Update all dependencies
uv lock --upgrade

# Sync dependencies (install from lockfile)
uv sync

# Sync only production dependencies (no dev)
uv sync --no-dev

# List installed packages
uv pip list

# Show dependency tree
uv tree
```

### Virtual Environment

```bash
# Create virtual environment (automatic with uv add)
uv venv

# Activate virtual environment (optional - uv run doesn't need this)
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

# Deactivate
deactivate

# Use uv run instead (recommended - no activation needed)
uv run python script.py
```

### Tool Execution

```bash
# Run tool temporarily (no installation)
uvx ruff check src/

# Install tool globally
uv tool install ruff

# List installed tools
uv tool list

# Update tool
uv tool upgrade ruff

# Uninstall tool
uv tool uninstall ruff
```

---

## Implementation Order (TDD Approach)

Follow this order using **Test-Driven Development**:

### Phase 1: Foundation

1. **Database Setup** (`src/database.py`)
   - Create database engine with async support
   - Session management with dependency injection
   - Database initialization function

2. **Task Model** (`src/models/task.py`)
   - **Write tests FIRST**: `tests/unit/test_task_model.py`
   - Create SQLModel entity with UUID, title, description, etc.
   - Run: `uv run pytest tests/unit/test_task_model.py` (should fail)
   - Implement model
   - Run: `uv run pytest tests/unit/test_task_model.py` (should pass)

3. **Task Schemas** (`src/schemas/task.py`)
   - **Write tests FIRST**: `tests/unit/test_task_schemas.py`
   - Create TaskCreate, TaskUpdate, TaskResponse schemas
   - Implement validation rules
   - Run tests and iterate

### Phase 2: Business Logic

4. **Task Service** (`src/services/task_service.py`)
   - **Write tests FIRST**: `tests/unit/test_task_service.py`
   - Implement: create_task(), get_task(), list_tasks(), update_task(), delete_task()
   - Run: `uv run pytest tests/unit/test_task_service.py`

### Phase 3: API Layer

5. **Task Router** (`src/api/tasks.py`)
   - **Write tests FIRST**: `tests/contract/test_task_api.py`
   - Implement: POST /tasks, GET /tasks, GET /tasks/{id}, PUT /tasks/{id}, DELETE /tasks/{id}
   - Run: `uv run pytest tests/contract/test_task_api.py`

6. **Main Application** (`src/main.py`)
   - FastAPI app initialization
   - Router registration
   - Error handlers
   - Startup/shutdown events

### Phase 4: Integration

7. **Integration Tests** (`tests/integration/test_task_flow.py`)
   - End-to-end user journeys
   - Multi-step workflows
   - Edge cases

---

## TDD Workflow with uv (Red-Green-Refactor)

### Step 1: RED - Write Failing Test

```bash
# Create test file
cat > tests/unit/test_task_service.py << 'EOF'
import pytest
from src.services.task_service import TaskService

@pytest.mark.asyncio
async def test_create_task_with_valid_data(test_session):
    """Test creating a task with valid title and description."""
    service = TaskService(test_session)

    task_data = {
        "title": "Write documentation",
        "description": "Create API docs"
    }

    result = await service.create_task(task_data)

    assert result.title == "Write documentation"
    assert result.description == "Create API docs"
    assert result.is_completed is False
    assert result.id is not None
EOF

# Run test (should FAIL - service doesn't exist yet)
uv run pytest tests/unit/test_task_service.py -v
```

**Expected**: ❌ Test fails (ImportError or implementation missing)

### Step 2: GREEN - Make Test Pass

```bash
# Create service implementation
cat > src/services/task_service.py << 'EOF'
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.task import Task

class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task_data: dict) -> Task:
        task = Task(**task_data)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task
EOF

# Run test (should PASS)
uv run pytest tests/unit/test_task_service.py -v
```

**Expected**: ✅ Test passes

### Step 3: REFACTOR - Improve Code

```python
# Refactor to use Pydantic schema instead of dict
from src.schemas.task import TaskCreate

class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task_data: TaskCreate) -> Task:
        task = Task(**task_data.model_dump())
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task
```

```bash
# Run test again (should still PASS)
uv run pytest tests/unit/test_task_service.py -v
```

**Expected**: ✅ Test still passes

---

## Running the Application

### Development Server

```bash
# Start server with auto-reload
uv run uvicorn src.main:app --reload --port 8000

# With custom host
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# With log level
uv run uvicorn src.main:app --reload --log-level debug
```

**Access**:
- API: http://localhost:8000
- Interactive docs (Swagger UI): http://localhost:8000/docs
- Alternative docs (ReDoc): http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

### Production Server

```bash
# Production mode with multiple workers
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or using gunicorn (add to dependencies first)
uv add gunicorn
uv run gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## Testing with uv

### Run Tests

```bash
# All tests
uv run pytest

# With verbose output
uv run pytest -v

# Specific test directory
uv run pytest tests/unit/
uv run pytest tests/contract/
uv run pytest tests/integration/

# Specific test file
uv run pytest tests/unit/test_task_service.py

# Specific test function
uv run pytest tests/unit/test_task_service.py::test_create_task_with_valid_data

# Show print statements
uv run pytest -s

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf
```

### Coverage

```bash
# Run tests with coverage
uv run pytest --cov=src

# HTML coverage report
uv run pytest --cov=src --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Coverage with missing lines
uv run pytest --cov=src --cov-report=term-missing
```

---

## Database Setup

### Neon Postgres (Recommended)

1. **Sign up**: https://neon.tech
2. **Create project**: "task-api"
3. **Copy connection string**:
   ```
   postgresql://user:pass@ep-xxx.neon.tech/dbname
   ```
4. **Update .env**:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/dbname
   ```

### Local PostgreSQL (Alternative)

```bash
# Install PostgreSQL
# macOS: brew install postgresql@15
# Ubuntu: sudo apt install postgresql-15

# Start PostgreSQL
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Linux

# Create databases
createdb taskdb
createdb test_taskdb

# Update .env
DATABASE_URL=postgresql+asyncpg://localhost/taskdb
```

---

## Development Checklist

### Before Writing Code
- [ ] Read `specs/001-task-api/spec.md` (requirements)
- [ ] Review `specs/001-task-api/data-model.md` (entity design)
- [ ] Review `specs/001-task-api/contracts/endpoints.md` (API contracts)
- [ ] Review `.specify/memory/constitution.md` (principles)

### During Implementation (TDD)
- [ ] Write failing test (RED)
- [ ] Implement minimum code (GREEN)
- [ ] Refactor for quality (REFACTOR)
- [ ] Add type hints to all functions
- [ ] Use async/await for I/O operations
- [ ] Validate inputs with Pydantic
- [ ] Handle errors with custom exceptions

### After Implementation
- [ ] All tests pass: `uv run pytest`
- [ ] Linting clean: `uv run ruff check src/`
- [ ] Type checking: `uv run mypy src/`
- [ ] Coverage >80%: `uv run pytest --cov=src`
- [ ] Manual testing via `/docs`
- [ ] Commit with descriptive message

---

## Troubleshooting

### Python Version Issues

```bash
# Check available Python versions
uv python list

# Install specific version
uv python install 3.11

# Set project version
echo "3.11" > .python-version
```

### Dependency Issues

```bash
# Update lockfile
uv lock --upgrade

# Reinstall all dependencies
uv sync --reinstall

# Clear cache
uv cache clean
```

### Import Errors

```bash
# Always use uv run (uses project's .venv automatically)
uv run python script.py
uv run pytest

# Don't do this (may use wrong Python/packages)
python script.py
pytest
```

### Database Connection

```bash
# Test database connection
uv run python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
engine = create_async_engine('your-db-url')
asyncio.run(engine.connect())
print('✅ Connection successful')
"
```

---

## Why uv?

### Speed Comparison
| Task | pip | uv | Speedup |
|------|-----|-----|---------|
| Install FastAPI + deps | 45s | 2s | **22x faster** |
| Create venv | 3s | 0.1s | **30x faster** |
| Resolve dependencies | 12s | 0.5s | **24x faster** |

### Developer Experience
- ✅ **No activation needed** - `uv run` handles everything
- ✅ **Fast installs** - 10-100x faster than pip
- ✅ **Lock file** - reproducible builds with `uv.lock`
- ✅ **Tool execution** - `uvx` runs tools without installation
- ✅ **Single command** - replaces pip, venv, pipx, poetry
- ✅ **Automatic Python** - downloads Python versions as needed

---

## Quick Start Summary

```bash
# 1. Initialize project
uv init --package task-api && cd task-api

# 2. Set Python version
echo "3.11" > .python-version

# 3. Add dependencies
uv add fastapi uvicorn[standard] sqlmodel asyncpg psycopg[binary] pydantic pydantic-settings python-dotenv
uv add --dev pytest pytest-asyncio httpx ruff mypy

# 4. Configure database
echo "DATABASE_URL=postgresql+asyncpg://user:pass@host/db" > .env

# 5. Create structure
mkdir -p src/{models,schemas,services,api} tests/{contract,integration,unit}

# 6. Start coding (TDD)
# Write test → Run test (fail) → Implement → Run test (pass) → Refactor

# 7. Run server
uv run uvicorn src.main:app --reload
```

**Ready to build with TDD and uv!** 🚀