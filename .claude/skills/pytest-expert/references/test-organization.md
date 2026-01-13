# Test Organization Reference

Comprehensive guide to organizing pytest test files, conftest.py usage, markers, and running tests efficiently.

## Test Discovery

Pytest automatically discovers tests based on naming conventions:

### File and Function Naming

```
tests/
├── test_*.py           ✅ Discovered
├── *_test.py           ✅ Discovered
├── test_*.txt          ❌ Not discovered (not .py)
└── tests.py            ❌ Not discovered (doesn't match pattern)

Within test files:
- test_*()              ✅ Discovered as test function
- Test* classes         ✅ Discovered as test class
  └── test_*() methods  ✅ Discovered as test method
```

### Example Structure

```python
# test_user.py

# ✅ Function-based test (discovered)
def test_create_user():
    ...

# ✅ Class-based test (discovered)
class TestUserAuthentication:
    def test_login(self):
        ...

    def test_logout(self):
        ...

# ❌ Not discovered (no test_ prefix)
def verify_user():
    ...

# ❌ Not discovered (starts with underscore)
def _test_helper():
    ...
```

---

## Directory Structure Patterns

### Small Project

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── services.py
└── tests/
    ├── __init__.py
    ├── conftest.py          # Shared fixtures
    ├── test_main.py
    ├── test_models.py
    └── test_services.py
```

### Medium Project

```
project/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── tasks.py
│   │   └── users.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── task.py
│   │   └── user.py
│   └── services/
│       ├── __init__.py
│       └── email.py
└── tests/
    ├── __init__.py
    ├── conftest.py          # Root fixtures
    ├── api/
    │   ├── conftest.py      # API-specific fixtures
    │   ├── test_tasks.py
    │   └── test_users.py
    ├── models/
    │   ├── test_task.py
    │   └── test_user.py
    └── services/
        └── test_email.py
```

### Large Project with Test Types

```
project/
├── app/
└── tests/
    ├── conftest.py                 # Global fixtures
    ├── unit/                       # Fast, isolated tests
    │   ├── conftest.py
    │   ├── test_models.py
    │   └── test_services.py
    ├── integration/                # Tests with dependencies
    │   ├── conftest.py
    │   ├── test_database.py
    │   └── test_api.py
    ├── e2e/                        # End-to-end tests
    │   ├── conftest.py
    │   └── test_workflows.py
    └── performance/                # Load/performance tests
        └── test_api_performance.py
```

---

## conftest.py

Central location for shared fixtures and configuration. Pytest automatically discovers `conftest.py` files.

### Fixture Scope

```python
# tests/conftest.py (root level)
import pytest

@pytest.fixture(scope="session")
def database_engine():
    """Available to all tests - created once per session."""
    engine = create_engine("sqlite:///test.db")
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(database_engine):
    """Available to all tests - created per test."""
    connection = database_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

### Hierarchical conftest.py

```python
# tests/conftest.py (root)
@pytest.fixture
def base_url():
    """Available to all tests."""
    return "http://testserver"

# tests/api/conftest.py (subdirectory)
@pytest.fixture
def api_client(base_url):
    """Available to tests in api/ directory."""
    return TestClient(base_url=base_url)

# tests/integration/conftest.py (subdirectory)
@pytest.fixture
def integration_client(base_url, db_session):
    """Available to tests in integration/ directory."""
    return TestClient(base_url=base_url, db=db_session)
```

### Common conftest.py Patterns

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from app.main import app
from app.database import get_db

# ============================================================
# Database Fixtures
# ============================================================

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine once per session."""
    engine = create_engine("sqlite:///./test.db")
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_engine):
    """Provide isolated database session per test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

# ============================================================
# API Client Fixtures
# ============================================================

@pytest.fixture
def client(db_session):
    """Provide test client with database override."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides = {}

@pytest.fixture
async def async_client(db_session):
    """Provide async test client."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides = {}

# ============================================================
# Test Data Fixtures
# ============================================================

@pytest.fixture
def test_user(db_session):
    """Provide test user."""
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_tasks(db_session):
    """Provide multiple test tasks."""
    tasks = [
        Task(title="Task 1", status="todo"),
        Task(title="Task 2", status="in_progress"),
        Task(title="Task 3", status="done"),
    ]
    for task in tasks:
        db_session.add(task)
    db_session.commit()
    return tasks

# ============================================================
# Authentication Fixtures
# ============================================================

@pytest.fixture
def auth_token(test_user):
    """Provide authentication token."""
    return create_access_token(test_user.id)

@pytest.fixture
def authenticated_client(client, auth_token):
    """Provide authenticated client."""
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    return client
```

---

## Pytest Markers

Markers categorize and control test execution.

### Built-in Markers

```python
import pytest

# Skip test
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    ...

# Skip conditionally
@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
def test_new_syntax():
    ...

# Expected to fail
@pytest.mark.xfail(reason="Known bug #123")
def test_with_known_issue():
    ...

# Parametrize
@pytest.mark.parametrize("input,expected", [(1, 2), (2, 3)])
def test_increment(input, expected):
    assert input + 1 == expected
```

### Custom Markers

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "api: marks tests for API endpoints",
    "database: marks tests that require database",
]

# Usage in tests
import pytest

@pytest.mark.unit
def test_pure_logic():
    ...

@pytest.mark.integration
@pytest.mark.database
def test_database_operation():
    ...

@pytest.mark.slow
def test_expensive_operation():
    ...

@pytest.mark.api
async def test_api_endpoint():
    ...
```

### Running Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run everything except slow tests
pytest -m "not slow"

# Run integration tests that use database
pytest -m "integration and database"

# Run unit or api tests
pytest -m "unit or api"
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_users.py

# Run specific test
pytest tests/test_users.py::test_create_user

# Run tests matching pattern
pytest tests/test_users.py::test_create*

# Run tests in directory
pytest tests/api/
```

### Useful Options

```bash
# Verbose output
pytest -v

# Very verbose (show full diff)
pytest -vv

# Stop after first failure
pytest -x

# Stop after N failures
pytest --maxfail=3

# Run last failed tests
pytest --lf

# Run failed tests first, then others
pytest --ff

# Show local variables in tracebacks
pytest -l

# Run in parallel (requires pytest-xdist)
pytest -n auto

# Show print statements
pytest -s

# Show test durations
pytest --durations=10
```

### Filtering Tests

```bash
# Run by keyword expression
pytest -k "test_create or test_update"

# Exclude by keyword
pytest -k "not slow"

# Run by marker
pytest -m "integration"

# Combine marker and keyword
pytest -m "integration" -k "user"
```

### Coverage

```bash
# Run with coverage (requires pytest-cov)
pytest --cov=app tests/

# Coverage with missing lines
pytest --cov=app --cov-report=term-missing tests/

# HTML coverage report
pytest --cov=app --cov-report=html tests/
```

---

## Test Naming Conventions

### Function-Based Tests

```python
# Pattern: test_<function>_<scenario>_<expected>

def test_create_user_with_valid_data_returns_user():
    """Test that creating user with valid data returns User object."""
    ...

def test_create_user_with_duplicate_email_raises_error():
    """Test that duplicate email raises ValueError."""
    ...

def test_get_user_when_not_found_returns_none():
    """Test that get_user returns None when user doesn't exist."""
    ...

def test_update_user_updates_all_fields():
    """Test that update_user modifies all provided fields."""
    ...
```

### Class-Based Tests

```python
# Group related tests in classes

class TestUserCreation:
    """Tests for user creation functionality."""

    def test_with_valid_data_creates_user(self):
        ...

    def test_with_duplicate_email_raises_error(self):
        ...

    def test_with_invalid_email_raises_validation_error(self):
        ...

class TestUserAuthentication:
    """Tests for user authentication."""

    def test_login_with_valid_credentials_returns_token(self):
        ...

    def test_login_with_invalid_credentials_returns_401(self):
        ...

    def test_logout_invalidates_token(self):
        ...
```

---

## Configuration Files

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Minimum Python version
minversion = 7.0

# Add options by default
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing

# Custom markers
markers =
    slow: marks tests as slow
    integration: marks integration tests
    unit: marks unit tests
    api: marks API tests

# Async configuration
asyncio_mode = auto
```

### pyproject.toml (Recommended)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=app",
    "--cov-report=term-missing",
]

markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "api: marks tests for API endpoints",
    "database: marks tests that require database",
]

# pytest-asyncio configuration
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"

# Coverage configuration
[tool.coverage.run]
source = ["app"]
omit = ["tests/*", "**/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

## Test Isolation Best Practices

### Use Fixtures for Setup/Teardown

```python
# ❌ Bad - manual setup/teardown
def test_user_creation():
    # Setup
    db = create_database()
    clear_data()

    # Test
    user = create_user("test")
    assert user is not None

    # Teardown
    clear_data()
    db.close()

# ✅ Good - use fixtures
@pytest.fixture
def clean_db():
    """Provide clean database."""
    db = create_database()
    clear_data()
    yield db
    clear_data()
    db.close()

def test_user_creation(clean_db):
    user = create_user("test")
    assert user is not None
```

### Avoid Test Dependencies

```python
# ❌ Bad - tests depend on each other
def test_1_create_user():
    global created_user
    created_user = create_user("test")

def test_2_update_user():
    # Depends on test_1
    created_user.name = "Updated"
    ...

# ✅ Good - independent tests
@pytest.fixture
def test_user():
    return create_user("test")

def test_create_user():
    user = create_user("test")
    assert user is not None

def test_update_user(test_user):
    test_user.name = "Updated"
    assert test_user.name == "Updated"
```

---

## Performance Tips

### Use Appropriate Fixture Scopes

```python
# Expensive operation - use session scope
@pytest.fixture(scope="session")
def database_schema():
    """Create schema once for all tests."""
    create_all_tables()
    yield
    drop_all_tables()

# Per-test isolation - use function scope
@pytest.fixture
def db_session():
    """Fresh session per test."""
    session = create_session()
    yield session
    session.rollback()
```

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto  # Auto-detect CPU cores
pytest -n 4     # Use 4 workers
```

### Use Markers to Skip Slow Tests

```python
@pytest.mark.slow
def test_expensive_operation():
    ...

# Development: skip slow tests
pytest -m "not slow"

# CI: run all tests
pytest
```

---

## Best Practices Summary

### ✅ DO

- Mirror source structure in test directory
- Use descriptive test names that explain intent
- Use conftest.py for shared fixtures
- Use markers to categorize tests
- Configure pytest in pyproject.toml
- Use fixtures for setup/teardown
- Keep tests independent and isolated
- Run fast tests frequently, slow tests in CI

### ❌ DON'T

- Don't create test dependencies (test order matters)
- Don't use global state
- Don't put business logic in conftest.py
- Don't create massive test files (split by feature)
- Don't skip teardown (use fixtures)
- Don't commit test databases
- Don't run slow tests on every save
