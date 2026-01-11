# Exception Handling in FastAPI

## Custom Exception Classes

```python
# exceptions.py
from fastapi import HTTPException, status

class APIException(Exception):
    """Base exception for API errors."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str | None = None,
        headers: dict | None = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or self._default_error_code()
        self.headers = headers

    def _default_error_code(self) -> str:
        return self.__class__.__name__.upper()


class NotFoundError(APIException):
    """Resource not found."""
    def __init__(self, resource: str = "Resource", id: str | int | None = None):
        detail = f"{resource} not found" if not id else f"{resource} with id '{id}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="NOT_FOUND"
        )


class UnauthorizedError(APIException):
    """Authentication required or invalid."""
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenError(APIException):
    """Authenticated but not allowed."""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )


class ConflictError(APIException):
    """Resource conflict (duplicate, state conflict)."""
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT"
        )


class ValidationError(APIException):
    """Business logic validation failed."""
    def __init__(self, detail: str, field: str | None = None):
        error_detail = f"{field}: {detail}" if field else detail
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_detail,
            error_code="VALIDATION_ERROR"
        )


class RateLimitError(APIException):
    """Rate limit exceeded."""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            headers={"Retry-After": str(retry_after)}
        )


class ServiceUnavailableError(APIException):
    """External service unavailable."""
    def __init__(self, service: str = "Service"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} is temporarily unavailable",
            error_code="SERVICE_UNAVAILABLE"
        )
```

---

## Error Response Format

```python
# schemas/error.py
from pydantic import BaseModel
from datetime import datetime

class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    code: str | None = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    code: str
    details: list[ErrorDetail] | None = None
    timestamp: datetime
    path: str | None = None
    request_id: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": False,
                    "error": "User not found",
                    "code": "NOT_FOUND",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "path": "/users/999"
                }
            ]
        }
    }
```

---

## Global Exception Handlers

```python
# exceptions.py (continued)
import logging
import traceback
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):
    """Register all exception handlers."""

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "code": exc.error_code,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            },
            headers=exc.headers
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'
            errors.append({
                "field": field,
                "message": error["msg"],
                "code": error["type"]
            })

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "Validation failed",
                "code": "VALIDATION_ERROR",
                "details": errors,
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Log the full traceback
        logger.error(
            f"Unhandled exception: {exc}",
            extra={
                "path": str(request.url.path),
                "method": request.method,
                "traceback": traceback.format_exc()
            }
        )

        # Return generic error to client
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "timestamp": datetime.utcnow().isoformat(),
                "path": str(request.url.path)
            }
        )
```

---

## Logging Integration

### Structured Logging Setup

```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "traceback"):
            log_data["traceback"] = record.traceback

        # Include exception info
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(level: str = "INFO"):
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Reduce noise from uvicorn
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```

### Request Logging Middleware

```python
import time
import uuid
from fastapi import Request

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    start_time = time.time()

    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
        }
    )

    response = await call_next(request)

    # Log response
    duration = time.time() - start_time
    logger.info(
        f"Request completed: {response.status_code} in {duration:.3f}s",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "duration": duration,
        }
    )

    response.headers["X-Request-ID"] = request_id
    return response
```

---

## Development vs Production Errors

```python
from app.config import settings

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    content = {
        "success": False,
        "error": "Internal server error",
        "code": "INTERNAL_ERROR",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Include stack trace in development
    if settings.DEBUG:
        content["debug"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc().split("\n")
        }

    return JSONResponse(status_code=500, content=content)
```

---

## Usage Examples

```python
from app.exceptions import NotFoundError, ConflictError, ValidationError

@router.get("/users/{user_id}")
async def get_user(user_id: int, db: DB):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User", user_id)
    return user


@router.post("/users")
async def create_user(user: UserCreate, db: DB):
    # Check for duplicate email
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise ConflictError("Email already registered")

    # Business validation
    if not is_valid_domain(user.email):
        raise ValidationError("Email domain not allowed", field="email")

    return db.create(user)


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: CurrentUser, db: DB):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User", user_id)

    if user.id != current_user.id and not current_user.is_admin:
        raise ForbiddenError("Cannot delete other users")

    db.delete(user)
```

---

## HTTP Exception Shorthand

For simple cases, FastAPI's built-in HTTPException works fine:

```python
from fastapi import HTTPException, status

# Simple usage
raise HTTPException(status_code=404, detail="User not found")

# With custom headers
raise HTTPException(
    status_code=401,
    detail="Invalid token",
    headers={"WWW-Authenticate": "Bearer"}
)
```

Use custom exceptions when you need:
- Consistent error format across the API
- Error codes for client handling
- Automatic logging
- Request context in error responses
