# Pytest Fixtures Reference

Comprehensive guide to pytest fixtures, scopes, parametrization, and built-in fixtures.

## Fixture Fundamentals

### Basic Fixture

```python
import pytest

@pytest.fixture
def user():
    """Provide a test user."""
    return {"id": 1, "name": "Test User", "email": "test@example.com"}

def test_user_has_email(user):
    assert "email" in user
    assert "@" in user["email"]
```

### Fixture with Setup and Teardown

```python
@pytest.fixture
def database_connection():
    """Create and teardown database connection."""
    # Setup
    conn = create_connection()
    conn.connect()

    yield conn  # Provide fixture value

    # Teardown (runs after test completes)
    conn.disconnect()
    conn.cleanup()
```

---

## Fixture Scopes

Control fixture lifetime with `scope` parameter:

```python
@pytest.fixture(scope="function")  # Default - new instance per test
def function_fixture():
    return "Fresh every test"

@pytest.fixture(scope="class")  # Shared within test class
def class_fixture():
    return "Shared by class tests"

@pytest.fixture(scope="module")  # Once per test file
def module_fixture():
    return "Shared by module"

@pytest.fixture(scope="session")  # Once per test run
def session_fixture():
    return "Shared by entire session"
```

### Scope Selection Strategy

| Scope      | Reuse | Isolation | Speed | Use When                                    |
| ---------- | ----- | --------- | ----- | ------------------------------------------- |
| `function` | None  | Maximum   | Slow  | Default - test needs fresh state            |
| `class`    | Class | High      | Fast  | Test class shares expensive setup           |
| `module`   | File  | Medium    | Faster| Test file shares database schema/connection |
| `session`  | Run   | Low       | Fastest| Test run shares read-only data/config      |

**Rule of Thumb**: Use narrowest scope possible. Start with `function`, widen only if needed.

---

## Parametrized Fixtures

### Simple Parametrization

```python
@pytest.fixture(params=["mysql", "postgresql", "sqlite"])
def database_type(request):
    """Test with multiple database types."""
    return request.param

def test_query_works_on_all_databases(database_type):
    # This test runs 3 times (once per param)
    assert database_type in ["mysql", "postgresql", "sqlite"]
```

### Parametrization with Setup

```python
@pytest.fixture(params=["mysql", "postgresql"])
def db_connection(request):
    """Create actual database connections."""
    if request.param == "mysql":
        conn = MySQLConnection()
    elif request.param == "postgresql":
        conn = PostgreSQLConnection()

    conn.connect()
    yield conn
    conn.disconnect()
```

### Complex Parameters

```python
@pytest.fixture(params=[
    {"driver": "mysql", "host": "localhost", "port": 3306},
    {"driver": "postgresql", "host": "localhost", "port": 5432},
])
def database_config(request):
    """Provide different database configurations."""
    return request.param

def test_connection(database_config):
    conn = connect(**database_config)
    assert conn.is_connected()
```

---

## Indirect Parametrization

Use `indirect=True` to parametrize fixture inputs via test parameters:

```python
@pytest.fixture
def user(request):
    """Create user with specified role."""
    role = request.param  # Comes from test parametrization
    return User(name=f"test_{role}", role=role)

@pytest.mark.parametrize("user", ["admin", "editor", "viewer"], indirect=True)
def test_user_permissions(user):
    # Test runs 3 times with different user roles
    assert user.role in ["admin", "editor", "viewer"]
```

### Indirect with Multiple Fixtures

```python
@pytest.fixture
def username(request):
    return request.param

@pytest.fixture
def user_role(request):
    return request.param

@pytest.mark.parametrize("username,user_role", [
    ("alice", "admin"),
    ("bob", "user"),
], indirect=["username", "user_role"])
def test_user_access(username, user_role):
    assert username and user_role
```

---

## Autouse Fixtures

Fixtures that run automatically without being explicitly requested:

```python
@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    global_state.reset()
    yield
    # Cleanup runs after test
    global_state.clear()

def test_something():
    # reset_state runs automatically
    assert global_state.is_clean()
```

### Class-Level Autouse

```python
@pytest.fixture(scope="class", autouse=True)
def setup_class_resources():
    """Setup resources once for entire test class."""
    resource = ExpensiveResource()
    resource.initialize()
    yield
    resource.cleanup()

class TestWithResource:
    def test_first(self):
        # setup_class_resources already ran
        pass

    def test_second(self):
        # Uses same resource instance
        pass
```

---

## Built-in Fixtures

### tmp_path (Recommended)

Provides a temporary directory unique to each test:

```python
def test_file_operations(tmp_path):
    """Test creates files in isolated temp directory."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")

    assert test_file.read_text() == "Hello World"
    # tmp_path automatically cleaned up after test
```

### monkeypatch

Safely modify objects, dictionaries, or environment variables:

```python
def test_environment_variable(monkeypatch):
    """Test with modified environment."""
    monkeypatch.setenv("API_KEY", "test-key-123")

    from app.config import get_api_key
    assert get_api_key() == "test-key-123"
    # Changes reverted after test

def test_mock_function(monkeypatch):
    """Mock a function."""
    def mock_api_call():
        return {"status": "ok"}

    monkeypatch.setattr("app.services.api.call_external_api", mock_api_call)

    result = call_external_api()
    assert result["status"] == "ok"
```

### capsys / capfd

Capture stdout/stderr output:

```python
def test_print_output(capsys):
    """Test function that prints to console."""
    print("Hello")
    print("World", file=sys.stderr)

    captured = capsys.readouterr()
    assert captured.out == "Hello\n"
    assert captured.err == "World\n"
```

### request

Access test request context (used in fixtures):

```python
@pytest.fixture
def resource(request):
    """Provide resource with test-specific configuration."""
    # Access test module
    module = request.module

    # Access test function
    test_name = request.node.name

    # Access markers
    markers = [m.name for m in request.node.iter_markers()]

    return Resource(test_name=test_name)
```

---

## Fixture Factories

Create multiple fixture instances within a single test:

```python
@pytest.fixture
def make_user():
    """Factory to create multiple users."""
    users = []

    def _make_user(name, role="user"):
        user = User(name=name, role=role)
        users.append(user)
        return user

    yield _make_user

    # Cleanup all created users
    for user in users:
        user.delete()

def test_multiple_users(make_user):
    admin = make_user("Alice", role="admin")
    user1 = make_user("Bob")
    user2 = make_user("Charlie")

    assert admin.role == "admin"
    assert user1.role == "user"
```

---

## Fixture Dependencies

Fixtures can depend on other fixtures:

```python
@pytest.fixture
def database():
    """Provide database connection."""
    db = Database()
    db.connect()
    yield db
    db.disconnect()

@pytest.fixture
def user_repository(database):
    """Repository depends on database fixture."""
    return UserRepository(database)

@pytest.fixture
def user_service(user_repository):
    """Service depends on repository."""
    return UserService(user_repository)

def test_user_service(user_service):
    # All dependent fixtures are automatically set up
    result = user_service.get_user(1)
    assert result is not None
```

---

## Dynamic Fixture Generation

Use `pytest_generate_tests` to dynamically create test parametrization:

```python
# In conftest.py
def pytest_generate_tests(metafunc):
    """Dynamically parametrize tests based on command-line option."""
    if "database_type" in metafunc.fixturenames:
        db_types = metafunc.config.getoption("--databases", default="sqlite").split(",")
        metafunc.parametrize("database_type", db_types)

# In test file
def test_query(database_type):
    # Number of runs depends on --databases option
    # pytest --databases=sqlite,mysql,postgresql
    assert database_type is not None
```

---

## Best Practices

### ✅ DO

- Use narrow scopes (function) by default
- Name fixtures as nouns describing what they provide
- Document fixtures with docstrings
- Use `tmp_path` for file operations
- Use `monkeypatch` for safe modifications
- Chain fixtures for complex dependencies
- Use fixture factories for multiple instances

### ❌ DON'T

- Don't use session scope unless truly read-only
- Don't modify mutable fixtures in tests
- Don't create fixtures that aren't reusable
- Don't use fixtures just to avoid imports
- Don't nest fixtures more than 3-4 levels deep
- Don't use autouse fixtures without clear need

---

## Common Patterns

### Database Session Fixture

```python
@pytest.fixture
def db_session():
    """Provide database session with automatic rollback."""
    session = Session(bind=engine)
    session.begin()

    yield session

    session.rollback()
    session.close()
```

### Authenticated Client Fixture

```python
@pytest.fixture
def authenticated_client(client, test_user):
    """Provide client with authentication token."""
    token = create_access_token(test_user.id)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client
```

### Test Data Fixture

```python
@pytest.fixture
def test_tasks(db_session):
    """Provide sample tasks for testing."""
    tasks = [
        Task(title="Task 1", status="todo"),
        Task(title="Task 2", status="in_progress"),
        Task(title="Task 3", status="done"),
    ]
    for task in tasks:
        db_session.add(task)
    db_session.commit()

    return tasks
```
