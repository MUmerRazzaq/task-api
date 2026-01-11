# SQLModel Field Configuration

## Field Basics

```python
from sqlmodel import Field, SQLModel

class Hero(SQLModel, table=True):
    # Primary key - always Optional with default=None
    id: int | None = Field(default=None, primary_key=True)

    # Required field (no default)
    name: str

    # Optional field with None default
    age: int | None = None

    # Optional field with Field()
    nickname: str | None = Field(default=None)

    # Required with constraints
    email: str = Field(max_length=255)
```

---

## Common Field Parameters

```python
Field(
    # Default value
    default=None,              # Static default
    default_factory=list,      # Dynamic default (for mutable types)

    # Database constraints
    primary_key=True,          # Primary key
    foreign_key="table.column", # Foreign key reference
    unique=True,               # Unique constraint
    nullable=True,             # Allow NULL (inferred from type hint)
    index=True,                # Create database index

    # Validation (Pydantic)
    max_length=100,            # String max length
    min_length=1,              # String min length
    gt=0,                      # Greater than
    ge=0,                      # Greater than or equal
    lt=100,                    # Less than
    le=100,                    # Less than or equal
    regex=r"^[a-z]+$",         # Regex pattern

    # Documentation
    title="Hero Name",         # OpenAPI title
    description="The hero's public name",  # OpenAPI description

    # SQLAlchemy pass-through
    sa_column=Column(...),     # Full SQLAlchemy Column control
    sa_column_kwargs={...},    # Additional Column kwargs
)
```

---

## Primary Keys

### Integer Auto-increment (Default)

```python
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
```

### UUID Primary Key

```python
from uuid import UUID, uuid4

class Hero(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
```

### Composite Primary Key

```python
class HeroTeamLink(SQLModel, table=True):
    hero_id: int = Field(foreign_key="hero.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)
```

---

## Foreign Keys

```python
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    # Basic foreign key - ALWAYS add index
    team_id: int | None = Field(default=None, foreign_key="team.id", index=True)

    # Required foreign key (not nullable)
    category_id: int = Field(foreign_key="category.id", index=True)

    # UUID foreign key
    owner_id: UUID = Field(foreign_key="user.id", index=True)
```

**Always index foreign keys** - Critical for JOIN performance.

---

## Indexes

### Single Column Index

```python
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Single column index
    email: str = Field(unique=True, index=True)  # Unique index
```

### Composite Index

```python
from sqlalchemy import Index

class Hero(SQLModel, table=True):
    __table_args__ = (
        Index("ix_hero_team_name", "team_id", "name"),  # Composite index
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str
    team_id: int | None = Field(default=None, foreign_key="team.id")
```

### When to Add Indexes

| Column Type | Index? | Reason |
|-------------|--------|--------|
| Primary key | Auto | Always indexed |
| Foreign key | **YES** | Critical for JOINs |
| Frequently filtered | YES | WHERE clause performance |
| Frequently sorted | YES | ORDER BY performance |
| Unique constraint | Auto | Unique implies index |
| Rarely queried | NO | Slows writes, wastes space |

---

## Constraints

### Unique Constraint

```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)  # Single column unique
```

### Composite Unique Constraint

```python
from sqlalchemy import UniqueConstraint

class Hero(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("name", "team_id", name="uq_hero_name_team"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str
    team_id: int | None = Field(default=None, foreign_key="team.id")
```

### Check Constraint

```python
from sqlalchemy import CheckConstraint

class Hero(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("age >= 0", name="ck_hero_age_positive"),
    )

    id: int | None = Field(default=None, primary_key=True)
    age: int | None = None
```

---

## String Fields

```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    # With max_length (recommended for all strings)
    name: str = Field(max_length=100)

    # With validation
    email: str = Field(
        max_length=255,
        regex=r"^[\w\.-]+@[\w\.-]+\.\w+$"
    )

    # Text field (unlimited length)
    bio: str | None = Field(default=None, sa_column=Column(Text))
```

---

## Numeric Fields

```python
from decimal import Decimal
from sqlalchemy import Column, Numeric

class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    # Integer with validation
    quantity: int = Field(ge=0)  # Must be >= 0

    # Decimal for money (NEVER use float for money)
    price: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2))  # 10 digits, 2 decimal places
    )

    # Float (for non-financial decimals)
    rating: float | None = Field(default=None, ge=0, le=5)
```

---

## Date/Time Fields

```python
from datetime import datetime, date, time
from sqlalchemy import Column, DateTime, func

class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    # Date only
    event_date: date

    # Time only
    start_time: time

    # DateTime with Python default
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # DateTime with database default
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )
```

---

## Enum Fields

```python
from enum import Enum

class HeroStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    status: HeroStatus = Field(default=HeroStatus.ACTIVE)
```

---

## JSON Fields

```python
from sqlalchemy import Column, JSON

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    # JSON field for flexible data
    metadata: dict | None = Field(default=None, sa_column=Column(JSON))

    # JSON with default empty dict
    settings: dict = Field(default_factory=dict, sa_column=Column(JSON))
```

---

## Excluding Fields from API

```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str
    hashed_password: str = Field(exclude=True)  # Excluded from .model_dump()

class UserPublic(SQLModel):
    """Response model without sensitive fields"""
    id: int
    email: str
    # hashed_password not included
```
