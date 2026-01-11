# Pydantic Patterns for FastAPI

## Basic Models

```python
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Annotated

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None

class UserOut(UserBase):
    model_config = {"from_attributes": True}  # For ORM models

    id: int
    is_active: bool
    created_at: datetime
```

---

## Field Validation

### Built-in Validators

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description="Price must be positive")
    quantity: int = Field(default=0, ge=0)
    sku: str = Field(..., pattern=r"^[A-Z]{3}-\d{4}$")  # Regex
    tags: list[str] = Field(default_factory=list, max_length=10)
```

### Custom Validators

```python
from pydantic import BaseModel, field_validator, model_validator

class Order(BaseModel):
    items: list[str]
    discount: float = 0
    total: float

    @field_validator("discount")
    @classmethod
    def validate_discount(cls, v: float) -> float:
        if v < 0 or v > 100:
            raise ValueError("Discount must be between 0 and 100")
        return v

    @field_validator("items")
    @classmethod
    def validate_items(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Order must have at least one item")
        return v

    @model_validator(mode="after")
    def validate_total(self) -> "Order":
        if self.total < 0:
            raise ValueError("Total cannot be negative")
        return self
```

---

## Request/Response Separation

### Input Models (Create/Update)

```python
class ItemCreate(BaseModel):
    """What the client sends to create an item."""
    name: str
    description: str | None = None
    price: float
    category_id: int

class ItemUpdate(BaseModel):
    """Partial update - all fields optional."""
    name: str | None = None
    description: str | None = None
    price: float | None = None
    category_id: int | None = None
```

### Output Models (Response)

```python
class ItemOut(BaseModel):
    """What the API returns - includes server-generated fields."""
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    price: float
    category_id: int
    created_at: datetime
    updated_at: datetime
```

### Why Separate?

```python
# Input: no id, no timestamps
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Output: id, no password, timestamps
class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    # No password field - not exposed
```

---

## Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class Company(BaseModel):
    name: str
    website: str | None = None

class UserProfile(BaseModel):
    id: int
    email: EmailStr
    address: Address | None = None
    company: Company | None = None
    tags: list[str] = []
```

---

## Generic Response Models

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

# Usage in endpoint
@router.get("/users", response_model=PaginatedResponse[UserOut])
async def list_users():
    pass

@router.get("/users/{id}", response_model=APIResponse[UserOut])
async def get_user(id: int):
    pass
```

---

## Discriminated Unions

```python
from typing import Literal, Union
from pydantic import BaseModel

class EmailNotification(BaseModel):
    type: Literal["email"]
    recipient: EmailStr
    subject: str
    body: str

class SMSNotification(BaseModel):
    type: Literal["sms"]
    phone_number: str
    message: str

class PushNotification(BaseModel):
    type: Literal["push"]
    device_token: str
    title: str
    body: str

Notification = Union[EmailNotification, SMSNotification, PushNotification]

@router.post("/notifications")
async def send_notification(notification: Notification):
    match notification.type:
        case "email":
            send_email(notification)
        case "sms":
            send_sms(notification)
        case "push":
            send_push(notification)
```

---

## Computed Fields

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

class Order(BaseModel):
    items: list[dict]
    tax_rate: float = 0.1

    @computed_field
    @property
    def subtotal(self) -> float:
        return sum(item["price"] * item["quantity"] for item in self.items)

    @computed_field
    @property
    def tax(self) -> float:
        return self.subtotal * self.tax_rate

    @computed_field
    @property
    def total(self) -> float:
        return self.subtotal + self.tax
```

---

## Model Configuration

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,        # ORM mode
        str_strip_whitespace=True,   # Strip strings
        validate_assignment=True,    # Validate on assignment
        extra="forbid",              # No extra fields allowed
        json_schema_extra={
            "examples": [
                {"email": "user@example.com", "username": "johndoe"}
            ]
        }
    )

    email: EmailStr
    username: str
```

---

## Serialization Control

```python
from pydantic import BaseModel, field_serializer
from datetime import datetime

class Event(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime

    @field_serializer("start_time", "end_time")
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

class UserWithSecrets(BaseModel):
    id: int
    email: str
    hashed_password: str
    api_key: str

    # Exclude sensitive fields from serialization
    model_config = ConfigDict(
        json_schema_extra={"exclude": {"hashed_password", "api_key"}}
    )
```

---

## Common Patterns

### Optional with Default

```python
# Optional field with None default
description: str | None = None

# Optional field with non-None default
status: str = "pending"

# Required field (no default)
name: str
```

### Constrained Types

```python
from pydantic import conint, constr, confloat

class Product(BaseModel):
    name: constr(min_length=1, max_length=100)
    price: confloat(gt=0, le=1000000)
    quantity: conint(ge=0, le=10000)
```

### Enums

```python
from enum import Enum

class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"

class Order(BaseModel):
    id: int
    status: OrderStatus = OrderStatus.pending
```

### Date/Time Fields

```python
from datetime import datetime, date, time
from pydantic import BaseModel

class Event(BaseModel):
    name: str
    event_date: date
    start_time: time
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## FastAPI Response Model Usage

```python
from fastapi import FastAPI

app = FastAPI()

@router.get("/users/{id}", response_model=UserOut)
async def get_user(id: int):
    # Returns UserInDB but FastAPI filters to UserOut
    return db.get_user(id)

@router.get("/users", response_model=list[UserOut])
async def list_users():
    return db.get_users()

# Exclude fields dynamically
@router.get("/users/{id}/public")
async def get_user_public(id: int):
    user = db.get_user(id)
    return user.model_dump(exclude={"email", "phone"})
```
