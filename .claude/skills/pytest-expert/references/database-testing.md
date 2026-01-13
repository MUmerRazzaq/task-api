# Database Testing Reference

Comprehensive guide to testing SQLModel database operations with transaction rollback, fixtures, and isolation patterns.

## Core Principles

1. **Test Isolation**: Each test operates on a clean database state
2. **Transaction Rollback**: Changes made during tests are rolled back
3. **No Side Effects**: Tests don't affect each other or production data
4. **Repeatable**: Tests produce same results on every run

---

## Database Test Fixtures

### Basic Session Fixture with Rollback

```python
# conftest.py
import pytest
from sqlmodel import Session, create_engine
from app.database import get_engine

@pytest.fixture(scope="session")
def engine():
    """Create test database engine once per session."""
    # Use test database
    test_engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False}
    )
    # Create all tables
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    # Drop all tables after tests
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture
def db_session(engine):
    """Provide database session with automatic rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

### Transaction Rollback Pattern Explained

```python
# This pattern ensures test isolation:
# 1. Create connection from engine
connection = engine.connect()

# 2. Begin transaction (outer transaction)
transaction = connection.begin()

# 3. Create session bound to connection
session = Session(bind=connection)

# 4. Test runs, makes changes to database
# Even if test calls session.commit(), changes stay in transaction

# 5. After test completes, rollback everything
transaction.rollback()  # Reverts ALL changes
connection.close()
```

### Advanced: Nested Transaction Pattern

For tests that need to handle rollbacks within the test:

```python
from sqlalchemy import event
from sqlalchemy.orm import Session as SQLASession

@pytest.fixture
def db_session(engine):
    """Session with nested transaction support."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Start nested transaction (savepoint)
    nested = connection.begin_nested()

    # Restart savepoint after each commit/rollback
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.expire_all()
            session.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

---

## Testing CRUD Operations

### Create Operations

```python
from sqlmodel import select
from app.models import Task

def test_create_task(db_session):
    """Test creating a task persists to database."""
    # Arrange
    task = Task(title="Test Task", description="Test description")

    # Act
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    # Assert
    assert task.id is not None
    result = db_session.exec(select(Task).where(Task.id == task.id)).first()
    assert result is not None
    assert result.title == "Test Task"
```

### Read Operations

```python
def test_get_task_by_id(db_session, test_task):
    """Test retrieving task by ID."""
    # test_task is a fixture that creates a task
    result = db_session.exec(
        select(Task).where(Task.id == test_task.id)
    ).first()

    assert result is not None
    assert result.id == test_task.id
    assert result.title == test_task.title
```

### Update Operations

```python
def test_update_task(db_session, test_task):
    """Test updating a task."""
    # Update
    test_task.title = "Updated Title"
    test_task.status = "completed"
    db_session.add(test_task)
    db_session.commit()
    db_session.refresh(test_task)

    # Verify
    result = db_session.exec(
        select(Task).where(Task.id == test_task.id)
    ).first()
    assert result.title == "Updated Title"
    assert result.status == "completed"
```

### Delete Operations

```python
def test_delete_task(db_session, test_task):
    """Test deleting a task."""
    task_id = test_task.id

    # Delete
    db_session.delete(test_task)
    db_session.commit()

    # Verify deletion
    result = db_session.exec(
        select(Task).where(Task.id == task_id)
    ).first()
    assert result is None
```

---

## Test Data Fixtures

### Simple Test Data

```python
@pytest.fixture
def test_task(db_session):
    """Provide a single test task."""
    task = Task(
        title="Test Task",
        description="Test description",
        status="todo"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task
```

### Multiple Test Records

```python
@pytest.fixture
def test_tasks(db_session):
    """Provide multiple test tasks."""
    tasks = [
        Task(title="Task 1", status="todo"),
        Task(title="Task 2", status="in_progress"),
        Task(title="Task 3", status="done"),
        Task(title="Task 4", status="todo"),
    ]
    for task in tasks:
        db_session.add(task)
    db_session.commit()

    # Refresh to get IDs
    for task in tasks:
        db_session.refresh(task)

    return tasks
```

### Related Models

```python
@pytest.fixture
def test_user_with_tasks(db_session):
    """Provide user with associated tasks."""
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    tasks = [
        Task(title="User Task 1", user_id=user.id),
        Task(title="User Task 2", user_id=user.id),
    ]
    for task in tasks:
        db_session.add(task)
    db_session.commit()

    return user
```

### Factory Fixture Pattern

```python
@pytest.fixture
def task_factory(db_session):
    """Factory for creating tasks."""
    def create_task(**kwargs):
        defaults = {
            "title": "Default Task",
            "description": "Default description",
            "status": "todo",
        }
        defaults.update(kwargs)
        task = Task(**defaults)
        db_session.add(task)
        db_session.commit()
        db_session.refresh(task)
        return task

    return create_task

def test_multiple_tasks(task_factory):
    task1 = task_factory(title="Task 1")
    task2 = task_factory(title="Task 2", status="done")
    assert task1.status == "todo"
    assert task2.status == "done"
```

---

## Testing Queries

### Simple Queries

```python
def test_get_all_tasks(db_session, test_tasks):
    """Test retrieving all tasks."""
    results = db_session.exec(select(Task)).all()
    assert len(results) == len(test_tasks)
```

### Filtered Queries

```python
def test_get_tasks_by_status(db_session, test_tasks):
    """Test filtering tasks by status."""
    todo_tasks = db_session.exec(
        select(Task).where(Task.status == "todo")
    ).all()

    assert len(todo_tasks) == 2
    assert all(task.status == "todo" for task in todo_tasks)
```

### Queries with Joins

```python
def test_get_user_tasks(db_session, test_user_with_tasks):
    """Test querying tasks with user join."""
    from sqlmodel import select

    statement = (
        select(Task, User)
        .join(User)
        .where(User.id == test_user_with_tasks.id)
    )
    results = db_session.exec(statement).all()

    assert len(results) > 0
    for task, user in results:
        assert user.id == test_user_with_tasks.id
```

### Pagination

```python
def test_pagination(db_session, test_tasks):
    """Test paginated query."""
    # Get first page
    page1 = db_session.exec(
        select(Task).offset(0).limit(2)
    ).all()
    assert len(page1) == 2

    # Get second page
    page2 = db_session.exec(
        select(Task).offset(2).limit(2)
    ).all()
    assert len(page2) == 2

    # Ensure different results
    assert page1[0].id != page2[0].id
```

### Aggregations

```python
def test_count_tasks(db_session, test_tasks):
    """Test counting tasks."""
    from sqlmodel import func

    count = db_session.exec(
        select(func.count()).select_from(Task)
    ).one()

    assert count == len(test_tasks)
```

---

## Testing Relationships

### One-to-Many

```python
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    tasks: List["Task"] = Relationship(back_populates="user")

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    user_id: Optional[int] = Field(foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="tasks")

def test_user_tasks_relationship(db_session):
    """Test one-to-many relationship."""
    user = User(username="testuser")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    task1 = Task(title="Task 1", user_id=user.id)
    task2 = Task(title="Task 2", user_id=user.id)
    db_session.add(task1)
    db_session.add(task2)
    db_session.commit()

    # Refresh to load relationship
    db_session.refresh(user)

    assert len(user.tasks) == 2
    assert all(task.user_id == user.id for task in user.tasks)
```

### Many-to-Many

```python
class TaskTag(SQLModel, table=True):
    """Link table for many-to-many."""
    task_id: int = Field(foreign_key="task.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    tasks: List[Task] = Relationship(back_populates="tags", link_model=TaskTag)

def test_many_to_many_relationship(db_session):
    """Test many-to-many relationship."""
    tag1 = Tag(name="urgent")
    tag2 = Tag(name="backend")
    db_session.add(tag1)
    db_session.add(tag2)
    db_session.commit()

    task = Task(title="Test Task")
    task.tags = [tag1, tag2]
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert len(task.tags) == 2
    assert tag1.name in [tag.name for tag in task.tags]
```

---

## Testing Constraints and Validation

### Unique Constraints

```python
from sqlalchemy.exc import IntegrityError

def test_unique_constraint(db_session):
    """Test unique constraint violation."""
    user1 = User(username="uniqueuser", email="test@example.com")
    db_session.add(user1)
    db_session.commit()

    # Try to create duplicate
    user2 = User(username="uniqueuser", email="other@example.com")
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        db_session.commit()
```

### Foreign Key Constraints

```python
def test_foreign_key_constraint(db_session):
    """Test foreign key constraint."""
    # Try to create task with non-existent user_id
    task = Task(title="Test", user_id=99999)
    db_session.add(task)

    with pytest.raises(IntegrityError):
        db_session.commit()
```

### Nullable Fields

```python
def test_nullable_field(db_session):
    """Test optional field can be null."""
    task = Task(title="Test Task", description=None)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.description is None
```

---

## Async Database Testing

### Async Session Fixture

```python
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.fixture(scope="session")
def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test_async.db",
        connect_args={"check_same_thread": False}
    )
    yield engine
    engine.sync_engine.dispose()

@pytest.fixture
async def async_db_session(async_engine):
    """Provide async database session with rollback."""
    async with async_engine.connect() as connection:
        async with connection.begin() as transaction:
            session = AsyncSession(bind=connection)
            yield session
            await session.close()
            await transaction.rollback()
```

### Async CRUD Tests

```python
@pytest.mark.asyncio
async def test_async_create_task(async_db_session):
    """Test creating task with async session."""
    task = Task(title="Async Task", description="Test")
    async_db_session.add(task)
    await async_db_session.commit()
    await async_db_session.refresh(task)

    assert task.id is not None

@pytest.mark.asyncio
async def test_async_query(async_db_session, test_task):
    """Test async query."""
    result = await async_db_session.exec(
        select(Task).where(Task.id == test_task.id)
    )
    task = result.first()
    assert task is not None
```

---

## Integration with FastAPI

### Complete Test Setup

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from app.main import app
from app.database import get_db

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///./test.db")
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_engine):
    """Provide database session with rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Provide test client with test database."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides = {}

# Test file
def test_create_task_endpoint(client):
    """Test POST /tasks endpoint."""
    response = client.post(
        "/tasks",
        json={"title": "New Task", "description": "Test"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Task"
    # Changes rolled back after test
```

---

## Best Practices

### ✅ DO

- Use transaction rollback for test isolation
- Create fresh test data for each test
- Test constraints and validation
- Use fixtures for common test data
- Test both successful and error cases
- Refresh objects after commit to get updated fields
- Use factories for flexible test data creation

### ❌ DON'T

- Don't use production database for tests
- Don't rely on test execution order
- Don't share mutable database state between tests
- Don't forget to commit when testing reads
- Don't test ORM internals (test your business logic)
- Don't create massive test datasets unless needed
- Don't forget to handle async properly with pytest-asyncio

---

## Common Patterns

### Testing Cascade Deletes

```python
def test_cascade_delete(db_session):
    """Test that deleting user deletes their tasks."""
    user = User(username="testuser")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    task = Task(title="User Task", user_id=user.id)
    db_session.add(task)
    db_session.commit()
    task_id = task.id

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify task was deleted
    result = db_session.exec(select(Task).where(Task.id == task_id)).first()
    assert result is None
```

### Testing Soft Deletes

```python
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    is_deleted: bool = Field(default=False)

def test_soft_delete(db_session, test_task):
    """Test soft delete marks record as deleted."""
    test_task.is_deleted = True
    db_session.add(test_task)
    db_session.commit()

    # Record still exists but marked deleted
    result = db_session.exec(
        select(Task).where(Task.id == test_task.id)
    ).first()
    assert result is not None
    assert result.is_deleted is True
```
