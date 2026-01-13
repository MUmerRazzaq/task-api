---
name: pytest-expert
description: |
  Production-grade pytest test builder for FastAPI applications with SQLModel.
  This skill should be used when writing tests for API endpoints, business logic,
  database operations, or any Python code requiring comprehensive test coverage.
  Handles fixtures, mocking, async tests, database transactions, and dependency overrides.
---

# Pytest Expert

Writes production-grade tests using pytest for FastAPI applications with SQLModel databases.

## What This Skill Does

- Writes complete test files with proper structure and organization
- Creates appropriate fixtures for database sessions, test data, and dependencies
- Implements correct async/await patterns for FastAPI endpoint tests
- Sets up database transaction rollback patterns for test isolation
- Uses proper mocking and patching strategies
- Applies pytest best practices for parametrization and markers
- Ensures tests are isolated, repeatable, and maintainable

## What This Skill Does NOT Do

- Run tests (use bash directly: `pytest`)
- Fix application code (only writes tests)
- Test non-Python code
- Generate test data factories (writes inline test data)
- Configure pytest.ini or pyproject.toml (focuses on test code)

---

## Before Implementation

Gather context to ensure tests match the codebase:

| Source               | Gather                                                          |
| -------------------- | --------------------------------------------------------------- |
| **Code Under Test**  | Read the module/endpoint being tested to understand behavior    |
| **Codebase**         | Existing test structure (tests/ directory), fixture patterns in conftest.py, naming conventions, imports used |
| **Conversation**     | User's specific testing requirements and edge cases             |
| **Skill References** | Pytest patterns, FastAPI testing, database fixtures (in `references/`) |
| **User Guidelines**  | Project-specific test conventions if documented                 |

**Critical**: ALWAYS read the code being tested before writing tests. Never write tests for code you haven't seen.

---

## Required Clarifications

Before writing tests, determine:

1. **Test type**: Are you writing unit tests, integration tests, API endpoint tests, or a combination?
2. **Existing patterns**: Should tests follow existing test structure (check tests/ directory) or establish new patterns?

## Optional Clarifications

Ask if unclear from context:

3. **Coverage priorities**: Any specific edge cases, error scenarios, or workflows to emphasize?
4. **Mocking strategy**: Should external dependencies be fully mocked or are some real calls acceptable?
5. **Test data approach**: Use inline test data or need fixture factories for complex scenarios?

**Note**: Only ask questions that cannot be inferred from reading the code under test or existing test files.

---

## Expected Outputs

This skill creates:

- **Test file(s)**: `tests/test_<module>.py` or `tests/test_api_<resource>.py`
- **Fixtures** (if needed): Additions to `tests/conftest.py` or local fixtures in test file
- **Test functions**: Following pytest naming conventions with descriptive docstrings
- **Imports**: All necessary imports (pytest, models, clients, mocks)
- **Assertions**: Clear, specific assertions that verify expected behavior

---

## Test Writing Workflow

```
1. Read Code Under Test
   ├─ Understand function signatures, return types
   ├─ Identify dependencies (database, external services)
   └─ Note edge cases and error conditions

2. Determine Test Type
   ├─ API Endpoint Test → Use TestClient + async patterns
   ├─ Database Operation → Use transaction rollback fixture
   ├─ Business Logic → Use pure unit test with mocks
   └─ Integration → Combine multiple fixtures

3. Design Fixtures
   ├─ Database session (if needed)
   ├─ Test data (models, records)
   ├─ Dependency overrides (for FastAPI)
   └─ Mocks (for external calls)

4. Write Test Cases
   ├─ Happy path (expected behavior)
   ├─ Edge cases (empty, null, boundaries)
   ├─ Error cases (validation, not found, conflicts)
   └─ Use descriptive test names: test_<function>_<scenario>_<expected>

5. Apply Best Practices
   ├─ One assertion concept per test (multiple asserts OK if related)
   ├─ Use parametrize for similar cases
   ├─ Add markers (@pytest.mark.asyncio, @pytest.mark.slow)
   └─ Keep tests readable and maintainable
```

---

## Test Structure Guidelines

### File Organization

```
tests/
├── conftest.py              # Shared fixtures (db session, client)
├── test_<module>.py         # Unit tests for modules
├── test_api_<resource>.py   # API endpoint tests
└── test_integration_*.py    # Integration tests
```

### Test Function Naming

```python
# Pattern: test_<function>_<scenario>_<expected>
def test_create_task_with_valid_data_returns_201(): ...
def test_get_task_when_not_found_returns_404(): ...
def test_update_task_without_auth_returns_403(): ...
```

### Fixture Scope Strategy

| Scope       | Use When                                | Example                         |
| ----------- | --------------------------------------- | ------------------------------- |
| `function`  | Default - fresh state per test          | Database transactions, test data|
| `class`     | Shared setup for test class             | Expensive setup shared in class |
| `module`    | Once per test file                      | Database schema creation        |
| `session`   | Once per test run                       | Test database creation          |

---

## Common Test Patterns

### 1. FastAPI Endpoint Test (Async)

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_tasks_returns_all_tasks(async_client: AsyncClient, test_tasks):
    """Test that GET /tasks returns all tasks."""
    response = await async_client.get("/tasks")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(test_tasks)
```

### 2. Database Test with Transaction Rollback

```python
import pytest
from sqlmodel import Session, select

@pytest.mark.asyncio
async def test_create_task_persists_to_database(db_session: Session):
    """Test that creating a task saves to database."""
    task = Task(title="Test", description="Test desc")
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Query to verify
    result = db_session.exec(select(Task).where(Task.id == task.id)).first()
    assert result is not None
    assert result.title == "Test"
    # Transaction will rollback after test
```

### 3. Unit Test with Mocking

```python
from unittest.mock import patch, MagicMock

def test_send_notification_calls_external_service(mock_http_client):
    """Test that send_notification calls the notification service."""
    with patch('app.services.notifications.requests.post') as mock_post:
        mock_post.return_value.status_code = 200

        result = send_notification("user@example.com", "Hello")

        assert result is True
        mock_post.assert_called_once()
```

### 4. Parametrized Tests

```python
@pytest.mark.parametrize("input_data,expected_status", [
    ({"title": "Valid"}, 201),
    ({"title": ""}, 422),           # Empty title
    ({"title": None}, 422),          # Null title
    ({}, 422),                       # Missing title
])
async def test_create_task_validation(async_client, input_data, expected_status):
    """Test task creation with various inputs."""
    response = await async_client.post("/tasks", json=input_data)
    assert response.status_code == expected_status
```

---

## Key Testing Principles

1. **Test Behavior, Not Implementation**
   - Focus on what the function does, not how
   - Tests should not break when refactoring internals

2. **Isolation**
   - Each test is independent
   - Database changes rollback
   - No shared mutable state

3. **Clarity**
   - Test names describe what's being tested
   - Arrange-Act-Assert pattern
   - Comments explain "why", not "what"

4. **Completeness**
   - Happy path + edge cases + error cases
   - Cover validation logic
   - Test error messages and status codes

5. **Maintainability**
   - DRY principle with fixtures
   - Parametrize similar tests
   - Keep tests simple and readable

---

## Version Compatibility

This skill uses patterns compatible with:

- **pytest** 7.0+ (fixtures, markers, parametrization)
- **FastAPI** 0.100+ (TestClient, dependency overrides)
- **SQLModel** 0.0.14+ (Session, select patterns)
- **httpx** 0.24+ (AsyncClient for async tests)
- **pytest-asyncio** 0.21+ (async test support)

For latest patterns or version-specific features, consult official documentation linked in references.

---

## Reference Documentation

For detailed patterns and examples, see:

| Reference                        | Content                                                    |
| -------------------------------- | ---------------------------------------------------------- |
| `references/pytest-fixtures.md`  | Fixture scopes, parametrization, autouse, built-ins        |
| `references/fastapi-testing.md`  | TestClient, async tests, dependency overrides              |
| `references/database-testing.md` | SQLModel fixtures, transaction rollback, test data         |
| `references/mocking-patterns.md` | unittest.mock, pytest-mock, patching strategies            |
| `references/test-organization.md`| File structure, conftest.py, markers, running tests        |

---

## Implementation Checklist

Before delivering tests, verify:

- [ ] Read and understand code under test
- [ ] Test file created in correct location (`tests/test_*.py`)
- [ ] Appropriate fixtures imported or defined
- [ ] Test names follow `test_<function>_<scenario>_<expected>` pattern
- [ ] All test cases are async if testing async code
- [ ] Database tests use transaction rollback fixture
- [ ] Mocks used for external dependencies
- [ ] Parametrize used for similar test cases
- [ ] Assertions are clear and specific
- [ ] Tests verify both success and error cases
- [ ] Tests are independent and can run in any order
