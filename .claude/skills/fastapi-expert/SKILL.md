---
name: fastapi-expert
description: |
  Comprehensive FastAPI development guide for building production-grade REST APIs.
  This skill should be used when building FastAPI applications from hello world to
  production-ready APIs, implementing CRUD operations, handling exceptions, configuring
  CORS, rate limiting, authentication, file uploads, and API design patterns.
---

# FastAPI Expert

Build production-grade REST APIs with FastAPI from zero to deployment.

## Official Documentation

| Resource | URL | Use For |
|----------|-----|---------|
| FastAPI Docs | https://fastapi.tiangolo.com | Core patterns, advanced features |
| Pydantic Docs | https://docs.pydantic.dev | Validation, models, migration |
| Starlette Docs | https://www.starlette.io | Middleware, requests, responses |
| Pydantic Migration | https://docs.pydantic.dev/latest/migration/ | v1 to v2 changes |

---

## Version Notes

Patterns use **Pydantic v2** syntax. Key differences from v1:

| v1 Syntax | v2 Syntax |
|-----------|-----------|
| `.dict()` | `.model_dump()` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes = True` |

For migration: Use `bump-pydantic` tool, then test thoroughly.

---

## Clarifications

### Required (Ask User)
- **Database/ORM**: SQLAlchemy sync, SQLAlchemy async, SQLModel, or other?
- **Project Type**: New project or adding to existing codebase?

### Optional (If Relevant)
- **Auth Method**: JWT, API keys, OAuth2 with external provider?
- **Deployment**: Docker, serverless, traditional server?

---

## Not Covered

- GraphQL (use Strawberry or Ariadne)
- WebSocket implementations (see Starlette docs)
- Database migrations (use Alembic)
- Frontend integration details

---

## Before Implementation

| Source | Gather |
|--------|--------|
| **Codebase** | Existing project structure, patterns, dependencies |
| **Conversation** | User's specific requirements, constraints |
| **Skill References** | Patterns from `references/` (see below) |
| **User Guidelines** | Project-specific conventions |

## Quick Start

```python
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    version="1.0.0",
    description="Production-ready API"
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

Run: `uvicorn main:app --reload`

---

## Decision Trees

### HTTP Method Selection

```
Create resource?      → POST   (201 Created)
Read resource?        → GET    (200 OK)
Full update?          → PUT    (200 OK)
Partial update?       → PATCH  (200 OK)
Delete resource?      → DELETE (204 No Content)
```

### Status Code Selection

```
Success:
├─ Created new resource?     → 201 Created
├─ No content to return?     → 204 No Content
└─ Returning data?           → 200 OK

Client Error:
├─ Bad request format?       → 400 Bad Request
├─ Not authenticated?        → 401 Unauthorized
├─ Authenticated but denied? → 403 Forbidden
├─ Resource not found?       → 404 Not Found
├─ Validation failed?        → 422 Unprocessable Entity
└─ Rate limit exceeded?      → 429 Too Many Requests

Server Error:
└─ Unexpected error?         → 500 Internal Server Error
```

---

## Core Patterns

### Project Structure (Production)

```
app/
├── main.py              # FastAPI app, lifespan, middleware
├── config.py            # Settings with pydantic-settings
├── dependencies.py      # Shared dependencies (db, auth)
├── exceptions.py        # Custom exceptions + handlers
├── routers/
│   ├── __init__.py
│   ├── users.py
│   └── items.py
├── schemas/             # Pydantic models (request/response)
│   ├── __init__.py
│   ├── user.py
│   └── item.py
├── models/              # Database models (SQLAlchemy/etc)
├── services/            # Business logic
└── tests/
    ├── conftest.py
    └── test_*.py
```

### Router Pattern

```python
# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Annotated[Session, Depends(get_db)]
):
    return db.query(User).offset(skip).limit(limit).all()

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

### Request/Response Models

```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# Input model - what client sends
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

# Output model - what API returns (no password!)
class UserOut(BaseModel):
    model_config = {"from_attributes": True}  # For ORM compatibility

    id: int
    username: str
    email: EmailStr
    created_at: datetime
```

### Dependency Injection

```python
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    user = decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Reusable dependency
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/me")
async def get_me(user: CurrentUser):
    return user
```

---

## Reference Files

| Topic | File | When to Read |
|-------|------|--------------|
| Project structure | `references/project-structure.md` | Starting new project |
| REST API design | `references/rest-api-design.md` | Designing endpoints |
| Exception handling | `references/exception-handling.md` | Error management |
| CORS configuration | `references/cors-config.md` | Cross-origin setup |
| Rate limiting | `references/rate-limiting.md` | API protection |
| Pydantic patterns | `references/pydantic-patterns.md` | Request/response models |
| Authentication | `references/authentication.md` | OAuth2/JWT setup |
| Background tasks | `references/background-tasks.md` | Async processing |
| File uploads | `references/file-uploads.md` | Handling files |
| Testing | `references/testing.md` | Test patterns |

---

## Common Tasks Quick Reference

### Add CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Or ["*"] for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Global Exception Handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )
```

### Background Task

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Email logic here
    pass

@router.post("/notify")
async def notify(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "Welcome!")
    return {"message": "Notification scheduled"}
```

### File Upload

```python
from fastapi import File, UploadFile
from typing import Annotated

@router.post("/upload")
async def upload_file(
    file: Annotated[UploadFile, File(description="File to upload")]
):
    contents = await file.read()
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents)
    }
```

### Pagination

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

@router.get("/items", response_model=PaginatedResponse[ItemOut])
async def list_items(page: int = 1, page_size: int = 20):
    offset = (page - 1) * page_size
    items = db.query(Item).offset(offset).limit(page_size).all()
    total = db.query(Item).count()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }
```

### Rate Limiting (SlowAPI)

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request):
    pass
```

---

## Checklist: Production Ready

- [ ] Environment-based configuration (pydantic-settings)
- [ ] Structured logging (structlog or python-json-logger)
- [ ] Exception handlers registered
- [ ] CORS configured appropriately
- [ ] Rate limiting on sensitive endpoints
- [ ] Input validation (Pydantic models)
- [ ] Response models (no data leakage)
- [ ] Health check endpoint
- [ ] OpenAPI documentation complete
- [ ] Tests with good coverage
