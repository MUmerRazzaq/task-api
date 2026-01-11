# SQLModel Model Patterns

## The Four Model Pattern (Recommended)

SQLModel combines SQLAlchemy (database) and Pydantic (validation). Use separate models for different purposes:

```python
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel

# ============================================
# 1. BASE MODEL - Shared fields, NO table=True
# ============================================
class HeroBase(SQLModel):
    """Fields shared between all Hero models"""
    name: str = Field(max_length=100, index=True)
    secret_name: str = Field(max_length=255)
    age: int | None = Field(default=None, index=True)
    team_id: int | None = Field(default=None, foreign_key="team.id")


# ============================================
# 2. TABLE MODEL - Database table, table=True
# ============================================
class Hero(HeroBase, table=True):
    """Actual database table"""
    __tablename__ = "heroes"  # Optional: explicit table name

    id: int | None = Field(default=None, primary_key=True)

    # Relationships defined here
    team: "Team | None" = Relationship(back_populates="heroes")


# ============================================
# 3. CREATE MODEL - Input for POST endpoints
# ============================================
class HeroCreate(HeroBase):
    """For creating new heroes - inherits all Base fields"""
    pass  # Or add create-specific fields


# ============================================
# 4. READ/PUBLIC MODEL - Output for responses
# ============================================
class HeroPublic(HeroBase):
    """For API responses - includes id"""
    id: int


# ============================================
# 5. UPDATE MODEL - Partial updates (all Optional)
# ============================================
class HeroUpdate(SQLModel):
    """For PATCH endpoints - all fields optional"""
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None
    team_id: int | None = None
```

---

## Production Base Model with Audit Fields

```python
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime, func

class BaseModel(SQLModel):
    """Base model with audit fields for all tables"""
    pass


class TimestampMixin(SQLModel):
    """Mixin for created_at and updated_at"""
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now())
    )


class SoftDeleteMixin(SQLModel):
    """Mixin for soft delete functionality"""
    is_deleted: bool = Field(default=False, index=True)
    deleted_at: datetime | None = Field(default=None)


# Usage: Combine mixins with your table model
class Hero(HeroBase, TimestampMixin, SoftDeleteMixin, table=True):
    id: int | None = Field(default=None, primary_key=True)
```

---

## UUID Primary Keys (Distributed Systems)

```python
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel

class Hero(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)

# Foreign key with UUID
class Weapon(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hero_id: UUID = Field(foreign_key="hero.id", index=True)
```

**When to use UUID:**
- Distributed systems / multiple databases
- Security (IDs not guessable)
- Merge data from multiple sources

**When to use Integer:**
- Single database
- Performance critical (smaller index)
- Simpler debugging

---

## Nested Response Models

```python
# Team with heroes in response
class TeamPublicWithHeroes(TeamBase):
    id: int
    heroes: list[HeroPublic] = []

# Hero with team in response
class HeroPublicWithTeam(HeroBase):
    id: int
    team: TeamPublic | None = None

# Usage in FastAPI
@app.get("/teams/{team_id}", response_model=TeamPublicWithHeroes)
def read_team_with_heroes(*, session: Session = Depends(get_session), team_id: int):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
```

---

## Sensitive Field Handling

```python
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    name: str


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str  # Never exposed in API


class UserCreate(UserBase):
    password: str  # Plain password for input


class UserPublic(UserBase):
    """Public model - NO password fields"""
    id: int
    # hashed_password intentionally excluded


class UserUpdate(SQLModel):
    email: str | None = None
    name: str | None = None
    password: str | None = None  # Optional password update
```

---

## Model with Complex Constraints

```python
from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint, Index

class Hero(SQLModel, table=True):
    __tablename__ = "heroes"
    __table_args__ = (
        # Composite unique constraint
        UniqueConstraint("name", "team_id", name="uq_hero_name_team"),
        # Composite index
        Index("ix_hero_team_age", "team_id", "age"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    team_id: int | None = Field(default=None, foreign_key="team.id")
    age: int | None = None
```

---

## Enum Fields

```python
from enum import Enum
from sqlmodel import Field, SQLModel

class HeroStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    status: HeroStatus = Field(default=HeroStatus.ACTIVE)
```
