# REST API Design Patterns

## Endpoint Naming Conventions

### Use Plural Nouns for Resources

```
✅ GET  /users          # List users
✅ GET  /users/123      # Get user 123
✅ POST /users          # Create user
✅ PUT  /users/123      # Update user 123

❌ GET  /user           # Avoid singular
❌ GET  /getUsers       # Avoid verbs
❌ GET  /user-list      # Avoid action words
```

### Use Lowercase with Hyphens

```
✅ /user-profiles
✅ /order-items
❌ /userProfiles       # No camelCase
❌ /user_profiles      # No underscores
```

### Nested Resources for Relationships

```
# User's orders (parent-child)
GET  /users/123/orders          # List user's orders
POST /users/123/orders          # Create order for user

# Order's items
GET  /orders/456/items          # List order items
POST /orders/456/items          # Add item to order

# Max 2 levels deep, then use query params
❌ /users/123/orders/456/items/789/details  # Too deep
✅ /order-items/789?include=details         # Better
```

### Actions as Sub-resources (When Needed)

```
POST /users/123/activate       # Non-CRUD action
POST /orders/456/cancel        # State change
POST /payments/789/refund      # Process action
```

---

## HTTP Methods

| Method | Purpose | Request Body | Idempotent | Safe |
|--------|---------|--------------|------------|------|
| GET | Read resource(s) | No | Yes | Yes |
| POST | Create resource | Yes | No | No |
| PUT | Replace resource | Yes | Yes | No |
| PATCH | Partial update | Yes | No | No |
| DELETE | Remove resource | No | Yes | No |

### When to Use Each

```python
# GET - Retrieve (safe, cacheable)
@router.get("/items/{item_id}")
async def get_item(item_id: int):
    return db.get(item_id)

# POST - Create (not idempotent)
@router.post("/items", status_code=201)
async def create_item(item: ItemCreate):
    return db.create(item)

# PUT - Full replace (idempotent)
@router.put("/items/{item_id}")
async def replace_item(item_id: int, item: ItemCreate):
    return db.replace(item_id, item)

# PATCH - Partial update (use for sparse updates)
@router.patch("/items/{item_id}")
async def update_item(item_id: int, item: ItemUpdate):
    return db.update(item_id, item)

# DELETE - Remove
@router.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int):
    db.delete(item_id)
```

---

## Status Codes Decision Tree

### Success (2xx)

| Code | When | Example |
|------|------|---------|
| 200 OK | Successful GET/PUT/PATCH | Return updated resource |
| 201 Created | Successful POST | Return created resource + Location header |
| 204 No Content | Successful DELETE | No response body |

### Client Errors (4xx)

| Code | When | Example |
|------|------|---------|
| 400 Bad Request | Malformed request | Invalid JSON syntax |
| 401 Unauthorized | No/invalid credentials | Missing or expired token |
| 403 Forbidden | Authenticated but not allowed | Access denied |
| 404 Not Found | Resource doesn't exist | User ID not in database |
| 405 Method Not Allowed | Wrong HTTP method | POST to read-only endpoint |
| 409 Conflict | Business rule violation | Duplicate email |
| 422 Unprocessable Entity | Validation failed | Email format invalid |
| 429 Too Many Requests | Rate limit exceeded | Add Retry-After header |

### Server Errors (5xx)

| Code | When | Example |
|------|------|---------|
| 500 Internal Server Error | Unexpected error | Database connection failed |
| 502 Bad Gateway | Upstream error | Third-party API down |
| 503 Service Unavailable | Temporarily unavailable | Maintenance mode |

### FastAPI Examples

```python
from fastapi import HTTPException, status

# 201 Created
@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    return {"id": 1, **user.model_dump()}

# 204 No Content
@router.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(id: int):
    db.delete(id)
    # No return statement needed

# 400 Bad Request
raise HTTPException(status_code=400, detail="Invalid request format")

# 401 Unauthorized
raise HTTPException(
    status_code=401,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"}
)

# 404 Not Found
raise HTTPException(status_code=404, detail="User not found")

# 409 Conflict
raise HTTPException(status_code=409, detail="Email already registered")

# 422 is automatic for Pydantic validation errors
```

---

## API Versioning Strategies

### 1. URL Path Versioning (Recommended)

```python
# Most explicit, easily cacheable
from fastapi import APIRouter

router_v1 = APIRouter(prefix="/api/v1")
router_v2 = APIRouter(prefix="/api/v2")

@router_v1.get("/users")
async def get_users_v1():
    return {"version": "v1", "users": [...]}

@router_v2.get("/users")
async def get_users_v2():
    return {"version": "v2", "data": {"users": [...]}}

# main.py
app.include_router(router_v1)
app.include_router(router_v2)
```

### 2. Header Versioning

```python
from fastapi import Header, HTTPException

@router.get("/users")
async def get_users(
    api_version: str = Header(default="v1", alias="X-API-Version")
):
    if api_version == "v2":
        return {"version": "v2", "data": {...}}
    return {"version": "v1", ...}
```

### 3. Query Parameter Versioning

```python
@router.get("/users")
async def get_users(version: str = "v1"):
    if version == "v2":
        return {"version": "v2", ...}
    return {"version": "v1", ...}
```

### 4. Content Negotiation (Accept Header)

```python
from fastapi import Request

@router.get("/users")
async def get_users(request: Request):
    accept = request.headers.get("accept", "")
    if "application/vnd.api.v2+json" in accept:
        return {"version": "v2", ...}
    return {"version": "v1", ...}
```

**Recommendation**: Use URL path versioning (`/api/v1/...`) for clarity.

---

## Request/Response Patterns

### Standard Response Envelope

```python
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None

class APIError(BaseModel):
    success: bool = False
    error: str
    code: str
    details: dict | None = None

# Usage
@router.get("/users/{id}", response_model=APIResponse[UserOut])
async def get_user(id: int):
    user = db.get(id)
    return APIResponse(data=user)
```

### Pagination

```python
class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams):
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=(total + params.page_size - 1) // params.page_size
        )

@router.get("/items", response_model=PaginatedResponse[ItemOut])
async def list_items(page: int = 1, page_size: int = 20, db: DB):
    params = PaginationParams(page=page, page_size=page_size)
    items = db.query(Item).offset(params.offset).limit(params.page_size).all()
    total = db.query(Item).count()
    return PaginatedResponse.create(items, total, params)
```

### Filtering

```python
from typing import Annotated
from fastapi import Query

@router.get("/items")
async def list_items(
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    category: Annotated[list[str] | None, Query()] = None,
    search: str | None = None,
):
    query = db.query(Item)
    if status:
        query = query.filter(Item.status == status)
    if min_price is not None:
        query = query.filter(Item.price >= min_price)
    if max_price is not None:
        query = query.filter(Item.price <= max_price)
    if category:
        query = query.filter(Item.category.in_(category))
    if search:
        query = query.filter(Item.name.ilike(f"%{search}%"))
    return query.all()
```

### Sorting

```python
from enum import Enum

class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

@router.get("/items")
async def list_items(
    sort_by: str = "created_at",
    order: SortOrder = SortOrder.desc,
):
    allowed_sort_fields = {"created_at", "name", "price"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(400, f"Invalid sort field. Allowed: {allowed_sort_fields}")

    query = db.query(Item)
    column = getattr(Item, sort_by)
    if order == SortOrder.desc:
        query = query.order_by(column.desc())
    else:
        query = query.order_by(column.asc())
    return query.all()
```

---

## OpenAPI/Swagger Customization

### Endpoint Documentation

```python
@router.post(
    "/users",
    response_model=UserOut,
    status_code=201,
    summary="Create a new user",
    description="Create a new user with email and password. Returns the created user.",
    response_description="The created user",
    responses={
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
    tags=["users"],
)
async def create_user(user: UserCreate):
    """
    Create a new user with the following information:

    - **email**: valid email address (required)
    - **username**: unique username (required)
    - **password**: strong password (required)
    """
    pass

# Schema examples
class UserCreate(BaseModel):
    email: EmailStr
    username: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "username": "johndoe"
                }
            ]
        }
    }
```

### Custom OpenAPI Schema

```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="Production API documentation",
        routes=app.routes,
    )

    # Add logo
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```
