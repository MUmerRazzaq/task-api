# FastAPI Testing Reference

Comprehensive guide to testing FastAPI applications with TestClient, async tests, and dependency overrides.

## TestClient Basics

### Simple Synchronous Testing

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

# Create test client
client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```

### Testing Different HTTP Methods

```python
def test_create_item():
    """Test POST request."""
    response = client.post(
        "/items/",
        json={"name": "Laptop", "price": 999.99}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Laptop"
    assert "id" in data

def test_update_item():
    """Test PUT request."""
    response = client.put(
        "/items/1",
        json={"name": "Updated Laptop", "price": 899.99}
    )
    assert response.status_code == 200

def test_delete_item():
    """Test DELETE request."""
    response = client.delete("/items/1")
    assert response.status_code == 204
```

### Testing Query Parameters

```python
def test_search_items():
    """Test endpoint with query parameters."""
    response = client.get("/items/?q=laptop&limit=10")
    assert response.status_code == 200
    items = response.json()
    assert len(items) <= 10
```

### Testing Path Parameters

```python
def test_get_item_by_id():
    """Test endpoint with path parameter."""
    response = client.get("/items/42")
    assert response.status_code == 200
    assert response.json()["id"] == 42
```

### Testing Headers

```python
def test_authenticated_endpoint():
    """Test endpoint requiring authentication header."""
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer test-token-123"}
    )
    assert response.status_code == 200
```

---

## Async Testing with AsyncClient

### Basic Async Test Setup

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_read_root_async():
    """Async test using AsyncClient."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
```

### Async Client Fixture

```python
# conftest.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def async_client():
    """Provide async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# test file
@pytest.mark.asyncio
async def test_endpoint(async_client):
    response = await async_client.get("/items")
    assert response.status_code == 200
```

### Testing Async Endpoints

```python
@app.get("/async-data")
async def get_async_data():
    """Async endpoint that performs async operations."""
    data = await fetch_data_from_external_api()
    return {"data": data}

@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    """Test async endpoint."""
    response = await async_client.get("/async-data")
    assert response.status_code == 200
    assert "data" in response.json()
```

---

## Dependency Overrides

FastAPI's powerful dependency injection system can be overridden in tests.

### Basic Dependency Override

```python
# app/dependencies.py
from fastapi import Depends

def get_current_user():
    # Real implementation queries database
    return authenticate_user()

# app/main.py
@app.get("/me")
def read_current_user(user = Depends(get_current_user)):
    return user

# tests/test_api.py
def test_protected_endpoint():
    """Override authentication dependency."""
    def override_get_current_user():
        return {"id": 1, "username": "testuser"}

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/me")
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

    # Clean up
    app.dependency_overrides = {}
```

### Database Dependency Override

```python
# app/dependencies.py
def get_db():
    """Production database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# tests/conftest.py
@pytest.fixture
def test_db():
    """Test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client_with_db(test_db):
    """Client with test database override."""
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides = {}

# tests/test_api.py
def test_create_task(client_with_db):
    response = client_with_db.post("/tasks", json={"title": "Test"})
    assert response.status_code == 201
    # Changes rolled back after test
```

### Multiple Dependency Overrides

```python
def test_complex_endpoint(test_db):
    """Override multiple dependencies."""
    def override_get_current_user():
        return User(id=1, role="admin")

    def override_get_db():
        yield test_db

    def override_get_settings():
        return Settings(environment="test")

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as client:
        response = client.get("/admin/settings")
        assert response.status_code == 200

    app.dependency_overrides = {}
```

### Fixture-Based Override Pattern

```python
@pytest.fixture
def override_dependencies(test_db, test_user):
    """Fixture that overrides all common dependencies."""
    def override_get_db():
        yield test_db

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield

    app.dependency_overrides = {}

def test_with_overrides(client, override_dependencies):
    # All dependencies are overridden
    response = client.get("/tasks")
    assert response.status_code == 200
```

---

## Testing Validation and Error Responses

### Validation Errors (422)

```python
def test_create_task_missing_required_field():
    """Test validation error for missing field."""
    response = client.post("/tasks", json={"description": "No title"})
    assert response.status_code == 422
    error = response.json()
    assert "detail" in error
```

### Not Found (404)

```python
def test_get_nonexistent_task():
    """Test 404 response."""
    response = client.get("/tasks/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}
```

### Unauthorized (401) and Forbidden (403)

```python
def test_protected_endpoint_without_auth():
    """Test endpoint requires authentication."""
    response = client.get("/admin/users")
    assert response.status_code == 401

def test_admin_endpoint_without_permission():
    """Test endpoint requires admin role."""
    # Override with non-admin user
    def override_get_current_user():
        return User(id=1, role="user")

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/admin/users")
    assert response.status_code == 403
    app.dependency_overrides = {}
```

### Conflict (409)

```python
def test_create_duplicate_task():
    """Test conflict when creating duplicate."""
    task_data = {"title": "Unique Task"}

    # Create first task
    response1 = client.post("/tasks", json=task_data)
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = client.post("/tasks", json=task_data)
    assert response2.status_code == 409
```

---

## Testing File Uploads

```python
def test_upload_file():
    """Test file upload endpoint."""
    files = {"file": ("test.txt", b"file content", "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"

def test_upload_multiple_files():
    """Test multiple file uploads."""
    files = [
        ("files", ("file1.txt", b"content1", "text/plain")),
        ("files", ("file2.txt", b"content2", "text/plain")),
    ]
    response = client.post("/upload-multiple", files=files)
    assert response.status_code == 200
    assert len(response.json()["filenames"]) == 2
```

---

## Testing Response Models

```python
from pydantic import BaseModel

class TaskResponse(BaseModel):
    id: int
    title: str
    status: str
    created_at: str

def test_response_structure():
    """Test response matches expected model."""
    response = client.get("/tasks/1")
    assert response.status_code == 200

    # Validate against Pydantic model
    task = TaskResponse(**response.json())
    assert task.id == 1
    assert isinstance(task.title, str)
```

---

## Testing Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/send-email")
def send_email(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email_task, email)
    return {"message": "Email queued"}

def test_background_task_queued(monkeypatch):
    """Test that background task is queued."""
    called = []

    def mock_send_email(email):
        called.append(email)

    monkeypatch.setattr("app.tasks.send_email_task", mock_send_email)

    response = client.post("/send-email?email=test@example.com")
    assert response.status_code == 200
    # Background tasks execute during request
    assert "test@example.com" in called
```

---

## Testing WebSocket Endpoints

```python
def test_websocket():
    """Test WebSocket endpoint."""
    with client.websocket_connect("/ws") as websocket:
        # Send message
        websocket.send_text("Hello")

        # Receive response
        data = websocket.receive_text()
        assert data == "Hello"

def test_websocket_json():
    """Test WebSocket with JSON messages."""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "ping"})
        response = websocket.receive_json()
        assert response["type"] == "pong"
```

---

## Async Testing Best Practices

### Configure pytest-asyncio

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # Automatically detect async tests
asyncio_default_fixture_loop_scope = "function"  # Isolate event loops
```

### Async Fixture Patterns

```python
@pytest.fixture
async def async_db_session():
    """Async database session fixture."""
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            yield session
            await session.rollback()

@pytest.fixture
async def test_user(async_db_session):
    """Create test user in async context."""
    user = User(username="testuser", email="test@example.com")
    async_db_session.add(user)
    await async_db_session.flush()
    return user
```

### Testing Async Dependencies

```python
async def get_async_data():
    """Async dependency."""
    return await fetch_from_cache()

@pytest.mark.asyncio
async def test_async_dependency_override(async_client):
    """Override async dependency."""
    async def override_get_async_data():
        return {"test": "data"}

    app.dependency_overrides[get_async_data] = override_get_async_data

    response = await async_client.get("/data")
    assert response.status_code == 200
    app.dependency_overrides = {}
```

---

## Common Testing Patterns

### Setup and Teardown Pattern

```python
@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Run before and after each test."""
    # Setup
    clear_cache()
    yield
    # Teardown
    app.dependency_overrides = {}
```

### Parametrized API Tests

```python
@pytest.mark.parametrize("endpoint,expected_status", [
    ("/health", 200),
    ("/tasks", 200),
    ("/tasks/1", 200),
    ("/nonexistent", 404),
])
def test_endpoints(endpoint, expected_status):
    response = client.get(endpoint)
    assert response.status_code == expected_status
```

### Testing Pagination

```python
def test_pagination():
    """Test paginated endpoint."""
    # Create test data
    for i in range(25):
        client.post("/tasks", json={"title": f"Task {i}"})

    # Test first page
    response = client.get("/tasks?skip=0&limit=10")
    assert len(response.json()) == 10

    # Test second page
    response = client.get("/tasks?skip=10&limit=10")
    assert len(response.json()) == 10

    # Test last page
    response = client.get("/tasks?skip=20&limit=10")
    assert len(response.json()) == 5
```

---

## Best Practices

### ✅ DO

- Use `AsyncClient` for async endpoints
- Override dependencies for test isolation
- Test all HTTP status codes (200, 400, 404, 422, etc.)
- Validate response structure with Pydantic models
- Clean up `app.dependency_overrides` after tests
- Use fixtures for common test setup
- Test both success and error paths

### ❌ DON'T

- Don't use production dependencies in tests
- Don't forget to clean up dependency overrides
- Don't test implementation details
- Don't share mutable state between tests
- Don't use real external services
- Don't skip error case testing
