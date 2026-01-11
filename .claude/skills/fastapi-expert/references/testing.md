# Testing FastAPI Applications

## Setup

```bash
pip install pytest pytest-asyncio httpx
```

## TestClient (Sync)

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```

---

## Async Testing with httpx

```python
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/")
        assert response.status_code == 200
```

---

## Test Structure

```
tests/
├── conftest.py          # Fixtures
├── test_users.py        # User endpoint tests
├── test_items.py        # Item endpoint tests
└── test_auth.py         # Auth tests
```

### conftest.py

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.dependencies import get_db
from app.models.base import Base

# Test database
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create test client with overridden dependencies."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    from app.models.user import User
    user = User(email="test@example.com", username="testuser", hashed_password="hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create auth headers for authenticated requests."""
    from app.utils.security import create_access_token
    token = create_access_token({"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}
```

---

## Testing Patterns

### CRUD Endpoints

```python
# test_users.py
def test_create_user(client):
    response = client.post(
        "/users",
        json={"email": "new@example.com", "username": "newuser", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert "id" in data
    assert "password" not in data  # Password not exposed

def test_read_user(client, test_user):
    response = client.get(f"/users/{test_user.id}")
    assert response.status_code == 200
    assert response.json()["email"] == test_user.email

def test_read_user_not_found(client):
    response = client.get("/users/99999")
    assert response.status_code == 404

def test_list_users(client, test_user):
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_update_user(client, test_user, auth_headers):
    response = client.patch(
        f"/users/{test_user.id}",
        json={"username": "updated"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["username"] == "updated"

def test_delete_user(client, test_user, auth_headers):
    response = client.delete(f"/users/{test_user.id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/users/{test_user.id}")
    assert response.status_code == 404
```

### Authentication

```python
# test_auth.py
def test_login_success(client, test_user):
    response = client.post(
        "/auth/token",
        data={"username": test_user.username, "password": "correct_password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_wrong_password(client, test_user):
    response = client.post(
        "/auth/token",
        data={"username": test_user.username, "password": "wrong"}
    )
    assert response.status_code == 401

def test_protected_endpoint_without_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401

def test_protected_endpoint_with_token(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
```

### Validation Errors

```python
def test_create_user_invalid_email(client):
    response = client.post(
        "/users",
        json={"email": "not-an-email", "username": "test", "password": "password123"}
    )
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"] == ["body", "email"] for e in errors)

def test_create_user_missing_field(client):
    response = client.post("/users", json={"email": "test@example.com"})
    assert response.status_code == 422
```

### File Uploads

```python
def test_upload_file(client, auth_headers):
    response = client.post(
        "/files",
        files={"file": ("test.txt", b"file content", "text/plain")},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "id" in response.json()

def test_upload_invalid_type(client, auth_headers):
    response = client.post(
        "/files",
        files={"file": ("test.exe", b"content", "application/x-msdownload")},
        headers=auth_headers
    )
    assert response.status_code == 400
```

---

## Dependency Overrides

```python
from unittest.mock import Mock

def test_with_mocked_service(client):
    mock_service = Mock()
    mock_service.get_data.return_value = {"mocked": True}

    def override_service():
        return mock_service

    app.dependency_overrides[get_service] = override_service

    response = client.get("/data")
    assert response.json() == {"mocked": True}

    app.dependency_overrides.clear()
```

---

## Testing Background Tasks

```python
from unittest.mock import patch, MagicMock

def test_endpoint_with_background_task(client):
    with patch("app.routers.users.send_email") as mock_send:
        response = client.post(
            "/users",
            json={"email": "test@example.com", "username": "test", "password": "pass"}
        )
        assert response.status_code == 201

        # Background task was scheduled
        mock_send.assert_called_once()
```

---

## Testing Lifespan Events

```python
from fastapi.testclient import TestClient

def test_lifespan_startup_shutdown():
    startup_called = False
    shutdown_called = False

    @asynccontextmanager
    async def lifespan(app):
        nonlocal startup_called, shutdown_called
        startup_called = True
        yield
        shutdown_called = True

    app = FastAPI(lifespan=lifespan)

    with TestClient(app) as client:
        assert startup_called
        response = client.get("/health")

    assert shutdown_called
```

---

## Async Database Testing

```python
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

ASYNC_TEST_DB = "sqlite+aiosqlite:///./test.db"

@pytest.fixture
async def async_db():
    engine = create_async_engine(ASYNC_TEST_DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_async_endpoint(async_db):
    app.dependency_overrides[get_db] = lambda: async_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/items")
        assert response.status_code == 200
```

---

## Test Coverage

```bash
# Run with coverage
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short
```

---

## Best Practices

1. **Isolate tests** - Each test should be independent
2. **Use fixtures** - Share setup code via fixtures
3. **Test edge cases** - Invalid input, not found, unauthorized
4. **Mock external services** - Don't call real APIs in tests
5. **Use factories** - Create test data consistently
6. **Test response shape** - Not just status codes
7. **Keep tests fast** - Use in-memory databases
