---
name: sqlmodel-production
description: |
  Production-ready SQLModel patterns for FastAPI applications. This skill should be used when
  creating database models, writing queries, managing sessions, setting up relationships,
  configuring connection pools, or troubleshooting database issues with SQLModel.
---

# SQLModel Production Patterns

## What This Skill Does

- Creates production-grade SQLModel models with proper patterns
- Implements relationships (one-to-many, many-to-many)
- Configures session management (sync and async)
- Builds FastAPI CRUD endpoints with SQLModel
- Troubleshoots common database problems

## What This Skill Does NOT Do

- Set up Alembic migrations (separate concern)
- Configure specific database servers (PostgreSQL, MySQL setup)
- Handle authentication/authorization logic

---

## Before Implementation

| Source               | Gather                                                   |
|----------------------|----------------------------------------------------------|
| **Codebase**         | Existing models, engine setup, project structure         |
| **Conversation**     | User's specific entities, relationships, constraints     |
| **Skill References** | Patterns from `references/` for domain expertise         |
| **User Guidelines**  | Project naming conventions, async/sync preference        |

---

## Quick Reference: Model Patterns

### The Four Model Types

```python
# 1. Base - Shared fields (NO table=True)
class HeroBase(SQLModel):
    name: str = Field(max_length=100, index=True)
    age: int | None = Field(default=None, index=True)

# 2. Table - Database table (table=True)
class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    secret_name: str = Field(max_length=255)

# 3. Create - Input validation (NO id)
class HeroCreate(HeroBase):
    secret_name: str

# 4. Read/Public - API response (includes id)
class HeroPublic(HeroBase):
    id: int

# 5. Update - Partial updates (all Optional)
class HeroUpdate(SQLModel):
    name: str | None = None
    age: int | None = None
```

See `references/model-patterns.md` for complete patterns including audit fields.

---

## Quick Reference: Relationships

### One-to-Many

```python
class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    heroes: list["Hero"] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    team_id: int | None = Field(default=None, foreign_key="team.id", index=True)
    team: Team | None = Relationship(back_populates="heroes")
```

### Many-to-Many (Link Table)

```python
class HeroTeamLink(SQLModel, table=True):
    team_id: int = Field(foreign_key="team.id", primary_key=True)
    hero_id: int = Field(foreign_key="hero.id", primary_key=True)
    role: str = Field(default="member")  # Extra data on link

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    heroes: list["Hero"] = Relationship(back_populates="teams", link_model=HeroTeamLink)

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    teams: list[Team] = Relationship(back_populates="heroes", link_model=HeroTeamLink)
```

See `references/relationships.md` for advanced patterns.

---

## Quick Reference: Session Management

### Sync (Standard)

```python
from sqlmodel import Session, create_engine

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

def get_session():
    with Session(engine) as session:
        yield session
```

### Async

```python
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    pool_pre_ping=True,
)

async def get_async_session():
    async with AsyncSession(async_engine) as session:
        yield session
```

See `references/session-management.md` for connection pooling configuration.

---

## Quick Reference: CRUD Operations

```python
from fastapi import Depends, HTTPException, Query
from sqlmodel import select

@app.post("/heroes/", response_model=HeroPublic)
def create_hero(*, session: Session = Depends(get_session), hero: HeroCreate):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes

@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(*, session: Session = Depends(get_session), hero_id: int, hero: HeroUpdate):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@app.delete("/heroes/{hero_id}")
def delete_hero(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}
```

See `references/crud-operations.md` for async patterns and bulk operations.

---

## Database Problems Quick Reference

| Problem | Symptom | Solution |
|---------|---------|----------|
| N+1 Queries | Slow list endpoints | `selectinload()` / `joinedload()` |
| Connection Leak | "Too many connections" | Use context managers, `pool_pre_ping=True` |
| Detached Instance | "not bound to Session" | `session.refresh()` after commit |
| Transaction Deadlock | Timeout errors | Consistent ordering, short transactions |
| Stale Data | Wrong values returned | `session.expire_all()` or new session |

See `references/database-problems.md` for complete troubleshooting guide.

---

## Field Configuration

```python
from sqlmodel import Field

class Hero(SQLModel, table=True):
    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Indexed for faster queries
    name: str = Field(index=True, max_length=100)

    # Unique constraint
    email: str = Field(unique=True, max_length=255)

    # Foreign key with index
    team_id: int | None = Field(default=None, foreign_key="team.id", index=True)

    # Nullable with default
    age: int | None = Field(default=None)

    # Required field with validation
    secret_name: str = Field(min_length=1, max_length=255)
```

See `references/field-configuration.md` for advanced constraints and custom types.

---

## Critical Rules

1. **Always separate table and non-table models** - Base, Create, Read, Update pattern
2. **Never use `echo=True` in production** - Logs all SQL, performance impact
3. **Always use `pool_pre_ping=True`** - Validates connections before use
4. **Always index foreign keys** - Critical for join performance
5. **Use `back_populates` not `backref`** - Explicit is better than implicit
6. **Call `session.refresh()` after commit** - Gets database-generated values
7. **Use `model_validate()` for creation** - Proper Pydantic validation
8. **Use `model_dump(exclude_unset=True)` for updates** - Only update provided fields
9. **Never commit inside loops** - Batch operations for performance
10. **Always handle `HTTPException` for not found** - Return 404, not 500
