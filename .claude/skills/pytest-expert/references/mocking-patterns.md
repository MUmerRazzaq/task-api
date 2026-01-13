# Mocking Patterns Reference

Comprehensive guide to mocking in pytest using unittest.mock, pytest-mock, and patching strategies.

## Why Mock?

Mocking isolates the code under test from external dependencies:

- **External APIs**: HTTP requests, third-party services
- **Databases**: When testing non-database logic
- **File System**: Reading/writing files
- **Time**: datetime.now(), time.sleep()
- **Random**: random numbers for deterministic tests
- **Environment**: System state, configuration

---

## unittest.mock Basics

### Mock Objects

```python
from unittest.mock import Mock

def test_basic_mock():
    """Mock objects track calls and can be configured."""
    mock = Mock()

    # Configure return value
    mock.return_value = 42
    assert mock() == 42

    # Track calls
    mock("arg1", "arg2", key="value")
    mock.assert_called_once_with("arg1", "arg2", key="value")
```

### MagicMock (Recommended)

```python
from unittest.mock import MagicMock

def test_magic_mock():
    """MagicMock supports magic methods like __len__, __str__, etc."""
    mock = MagicMock()

    # Supports attribute access
    mock.method.return_value = "result"
    assert mock.method() == "result"

    # Supports magic methods
    mock.__len__.return_value = 5
    assert len(mock) == 5
```

---

## Patching with unittest.mock

### patch Decorator

```python
from unittest.mock import patch

@patch('requests.get')
def test_api_call(mock_get):
    """Patch external HTTP call."""
    # Configure mock
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": "value"}

    # Call function that uses requests.get
    from app.services import fetch_data
    result = fetch_data("https://api.example.com")

    # Verify
    assert result == {"data": "value"}
    mock_get.assert_called_once_with("https://api.example.com")
```

### patch Context Manager

```python
def test_api_call_with_context():
    """Use patch as context manager."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": "value"}

        result = fetch_data("https://api.example.com")
        assert result == {"data": "value"}
```

### Patching Multiple Targets

```python
@patch('app.services.send_email')
@patch('app.services.requests.post')
def test_multiple_patches(mock_post, mock_send_email):
    """Patch multiple functions (note reversed order)."""
    mock_post.return_value.status_code = 200
    mock_send_email.return_value = True

    result = process_order()
    assert result is True
    mock_post.assert_called_once()
    mock_send_email.assert_called_once()
```

### patch.object

```python
from app.services import EmailService

@patch.object(EmailService, 'send')
def test_email_service(mock_send):
    """Patch method on a class."""
    mock_send.return_value = True

    service = EmailService()
    result = service.send("test@example.com", "Hello")

    assert result is True
    mock_send.assert_called_once()
```

---

## Return Values and Side Effects

### Simple Return Values

```python
mock = Mock(return_value=42)
assert mock() == 42

# Or configure after creation
mock.return_value = 100
assert mock() == 100
```

### Multiple Return Values

```python
mock = Mock(side_effect=[1, 2, 3])
assert mock() == 1
assert mock() == 2
assert mock() == 3
```

### side_effect with Function

```python
def custom_behavior(arg):
    if arg == "special":
        return "special_result"
    return "default"

mock = Mock(side_effect=custom_behavior)
assert mock("special") == "special_result"
assert mock("other") == "default"
```

### Raising Exceptions

```python
mock = Mock(side_effect=ValueError("Invalid input"))

with pytest.raises(ValueError, match="Invalid input"):
    mock()
```

---

## Assertions on Mocks

### Call Assertions

```python
mock = Mock()
mock("arg1", key="value")

# Check if called
assert mock.called
assert mock.call_count == 1

# Check call arguments
mock.assert_called_once()
mock.assert_called_once_with("arg1", key="value")
mock.assert_called_with("arg1", key="value")

# Multiple calls
mock("arg2")
mock.assert_called_with("arg2")  # Last call
assert mock.call_count == 2
```

### Advanced Assertions

```python
mock = Mock()
mock("call1")
mock("call2")
mock("call3")

# Check any call
mock.assert_any_call("call2")

# Check all calls
from unittest.mock import call
mock.assert_has_calls([
    call("call1"),
    call("call2"),
    call("call3"),
])

# Check if NOT called
mock.reset_mock()
mock.assert_not_called()
```

---

## pytest.monkeypatch

Pytest's built-in fixture for safe patching:

### Basic Patching

```python
def test_environment_variable(monkeypatch):
    """Patch environment variable."""
    monkeypatch.setenv("API_KEY", "test-key-123")

    from app.config import get_api_key
    assert get_api_key() == "test-key-123"
    # Automatically restored after test
```

### Patching Attributes

```python
def test_patch_attribute(monkeypatch):
    """Patch module or class attribute."""
    import app.config
    monkeypatch.setattr(app.config, "DEBUG", True)

    assert app.config.DEBUG is True
```

### Patching Functions

```python
def test_patch_function(monkeypatch):
    """Patch function with mock."""
    def mock_send_email(to, subject, body):
        return {"status": "mocked"}

    monkeypatch.setattr("app.services.email.send_email", mock_send_email)

    result = send_notification("user@example.com")
    assert result["status"] == "mocked"
```

### Patching Dictionary Items

```python
def test_patch_dict(monkeypatch):
    """Patch dictionary item."""
    import app.config
    monkeypatch.setitem(app.config.SETTINGS, "max_retries", 10)

    assert app.config.SETTINGS["max_retries"] == 10
```

### Deleting Attributes

```python
def test_delete_attribute(monkeypatch):
    """Remove attribute for testing."""
    monkeypatch.delattr("app.config.OPTIONAL_FEATURE", raising=False)

    # Code handles missing attribute
    result = check_optional_feature()
    assert result is None
```

---

## pytest-mock Plugin

Enhanced mocking with pytest-mock (install: `pip install pytest-mock`):

### Using mocker Fixture

```python
def test_with_mocker(mocker):
    """Use mocker fixture (cleaner syntax)."""
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.status_code = 200

    result = fetch_data("https://api.example.com")
    assert result is not None
```

### Spying (Partial Mocking)

```python
def test_spy_on_function(mocker):
    """Spy allows real function to run while tracking calls."""
    spy = mocker.spy(app.services, 'process_data')

    # Real function executes
    result = process_data([1, 2, 3])

    # But we can verify it was called
    spy.assert_called_once()
    assert result == [2, 4, 6]  # Real result
```

### Mocking Class Methods

```python
def test_mock_class_method(mocker):
    """Mock method on a class."""
    mock_method = mocker.patch.object(
        UserService,
        'get_user',
        return_value=User(id=1, name="Test")
    )

    service = UserService()
    user = service.get_user(1)

    assert user.name == "Test"
    mock_method.assert_called_once_with(1)
```

---

## Common Mocking Patterns

### Mock External HTTP Requests

```python
@patch('requests.get')
def test_fetch_user_data(mock_get):
    """Mock HTTP GET request."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com"
    }
    mock_get.return_value = mock_response

    user = fetch_user_from_api(1)

    assert user["name"] == "John Doe"
    mock_get.assert_called_once_with("https://api.example.com/users/1")
```

### Mock HTTP POST with Error Handling

```python
@patch('requests.post')
def test_api_error_handling(mock_post):
    """Test handling of API errors."""
    mock_post.side_effect = requests.RequestException("Network error")

    with pytest.raises(requests.RequestException):
        send_webhook("https://webhook.example.com", {"data": "value"})
```

### Mock Database Operations

```python
@patch('app.database.session')
def test_create_user_without_db(mock_session):
    """Test user creation logic without real database."""
    mock_session.add = Mock()
    mock_session.commit = Mock()

    user = create_user("testuser", "test@example.com")

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    assert user.username == "testuser"
```

### Mock File Operations

```python
from unittest.mock import mock_open

@patch('builtins.open', new_callable=mock_open, read_data='file content')
def test_read_file(mock_file):
    """Mock file reading."""
    content = read_config_file('/path/to/config.txt')

    assert content == 'file content'
    mock_file.assert_called_once_with('/path/to/config.txt', 'r')
```

### Mock datetime

```python
from datetime import datetime

@patch('app.services.datetime')
def test_time_based_logic(mock_datetime):
    """Mock datetime.now()."""
    mock_datetime.now.return_value = datetime(2024, 1, 15, 10, 30)

    result = get_current_timestamp()

    assert result == "2024-01-15 10:30:00"
```

### Mock Random Numbers

```python
@patch('random.randint')
def test_random_behavior(mock_randint):
    """Make random behavior deterministic."""
    mock_randint.return_value = 42

    result = generate_random_id()

    assert result == 42
    mock_randint.assert_called_once()
```

---

## Async Mocking

### Mock Async Functions

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_function():
    """Mock async function."""
    mock = AsyncMock(return_value={"data": "value"})

    result = await mock()

    assert result == {"data": "value"}
    mock.assert_awaited_once()
```

### Patch Async Functions

```python
@pytest.mark.asyncio
@patch('app.services.fetch_async_data', new_callable=AsyncMock)
async def test_async_service(mock_fetch):
    """Patch async function."""
    mock_fetch.return_value = {"status": "success"}

    result = await process_async_data()

    assert result["status"] == "success"
    mock_fetch.assert_awaited_once()
```

### Mock Async Context Manager

```python
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_async_context_manager():
    """Mock async context manager."""
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock()
    mock_session.execute = AsyncMock(return_value="result")

    async with mock_session as session:
        result = await session.execute("query")

    assert result == "result"
```

---

## Dependency Injection Alternative

Sometimes dependency injection is cleaner than mocking:

### Before (with mocking)

```python
# Hard to test
def process_order(order_id):
    user = fetch_user_from_api(order_id)  # External call
    email = send_email(user.email)  # External call
    return email

@patch('app.services.send_email')
@patch('app.services.fetch_user_from_api')
def test_process_order(mock_fetch, mock_email):
    # Complex setup
    ...
```

### After (with dependency injection)

```python
# Easy to test
def process_order(order_id, user_fetcher, email_sender):
    user = user_fetcher(order_id)
    email = email_sender(user.email)
    return email

def test_process_order():
    """Test with fake implementations."""
    def fake_fetcher(order_id):
        return User(id=order_id, email="test@example.com")

    def fake_sender(email):
        return {"status": "sent"}

    result = process_order(1, fake_fetcher, fake_sender)
    assert result["status"] == "sent"
```

---

## Best Practices

### ✅ DO

- Mock at the boundary (external APIs, not internal functions)
- Use `MagicMock` over `Mock` (more flexible)
- Use `monkeypatch` for simple attribute/env changes
- Use `AsyncMock` for async functions
- Configure return values clearly
- Assert on mock calls to verify behavior
- Use dependency injection when possible
- Reset mocks between tests if reused

### ❌ DON'T

- Don't mock everything (test real code paths)
- Don't mock code under test (only dependencies)
- Don't create overly complex mock setups
- Don't forget to assert mock was called
- Don't use mocks when fixtures would be cleaner
- Don't mock internal implementation details
- Don't share mock objects between tests

---

## Common Pitfalls

### Pitfall 1: Wrong Patch Target

```python
# app/services.py
from requests import get

def fetch_data():
    return get("https://api.example.com")

# ❌ Wrong - patches requests module, not imported name
@patch('requests.get')
def test_wrong(mock_get):
    ...

# ✅ Correct - patches where it's used
@patch('app.services.get')
def test_correct(mock_get):
    ...
```

### Pitfall 2: Forgot to Configure Mock

```python
# ❌ Wrong - mock returns another mock by default
@patch('requests.get')
def test_wrong(mock_get):
    result = fetch_data()
    assert result == {"data": "value"}  # Fails!

# ✅ Correct - configure return value
@patch('requests.get')
def test_correct(mock_get):
    mock_get.return_value.json.return_value = {"data": "value"}
    result = fetch_data()
    assert result == {"data": "value"}
```

### Pitfall 3: Multiple Decorators Order

```python
# ❌ Wrong order
@patch('app.services.func_a')
@patch('app.services.func_b')
def test_wrong(mock_a, mock_b):  # Order is reversed!
    ...

# ✅ Correct - decorators apply bottom-to-top
@patch('app.services.func_a')
@patch('app.services.func_b')
def test_correct(mock_b, mock_a):  # Parameters match decorator order (reversed)
    ...
```

---

## Quick Reference

| Task                         | Tool              | Example                                      |
| ---------------------------- | ----------------- | -------------------------------------------- |
| Patch function               | `@patch`          | `@patch('module.function')`                  |
| Patch class method           | `@patch.object`   | `@patch.object(Class, 'method')`             |
| Patch env variable           | `monkeypatch`     | `monkeypatch.setenv('KEY', 'value')`         |
| Patch attribute              | `monkeypatch`     | `monkeypatch.setattr(obj, 'attr', value)`    |
| Mock async function          | `AsyncMock`       | `mock = AsyncMock(return_value=...)`         |
| Spy on function              | `mocker.spy`      | `spy = mocker.spy(module, 'function')`       |
| Configure return value       | `return_value`    | `mock.return_value = 42`                     |
| Raise exception              | `side_effect`     | `mock.side_effect = ValueError()`            |
| Multiple return values       | `side_effect`     | `mock.side_effect = [1, 2, 3]`               |
| Check if called              | `assert_called`   | `mock.assert_called_once()`                  |
| Check call arguments         | `assert_called_with` | `mock.assert_called_once_with(arg)`       |
