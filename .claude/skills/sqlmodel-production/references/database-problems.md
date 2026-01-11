# Database Problems and Solutions

## Quick Diagnosis Table

| Symptom | Likely Problem | Solution |
|---------|----------------|----------|
| Slow list endpoints | N+1 Query Problem | Eager loading |
| "Too many connections" | Connection leak | Context managers, pool_pre_ping |
| "Instance not bound to Session" | Detached instance | Refresh after commit |
| Timeout errors | Transaction deadlock | Shorter transactions, consistent ordering |
| Wrong data returned | Stale session data | Expire or new session |
| "Connection already closed" | Stale connection | pool_pre_ping=True |
| Integrity error on insert | Unique constraint violation | Handle IntegrityError |
| Foreign key error | Missing parent record | Check parent exists first |
| "Object already attached" | Adding same object twice | Check before add |
| Memory growing endlessly | Unbounded query results | Pagination, streaming |

---

## N+1 Query Problem

### The Problem

```python
# BAD: N+1 queries - 1 for teams, then N queries for heroes
@app.get("/teams/")
def get_teams(session: Session = Depends(get_session)):
    teams = session.exec(select(Team)).all()
    for team in teams:
        print(team.heroes)  # Each access triggers a new query!
    return teams
```

If you have 100 teams, this executes **101 queries**.

### The Solution: Eager Loading

```python
from sqlalchemy.orm import selectinload, joinedload

# GOOD: 2 queries total - one for teams, one for all heroes
@app.get("/teams/")
def get_teams(session: Session = Depends(get_session)):
    statement = select(Team).options(selectinload(Team.heroes))
    teams = session.exec(statement).all()
    return teams
```

### Eager Loading Options

```python
from sqlalchemy.orm import selectinload, joinedload, subqueryload

# selectinload - Uses IN query (best for collections)
select(Team).options(selectinload(Team.heroes))
# Query 1: SELECT * FROM team
# Query 2: SELECT * FROM hero WHERE team_id IN (1, 2, 3, ...)

# joinedload - Uses LEFT JOIN (best for single objects)
select(Hero).options(joinedload(Hero.team))
# Query: SELECT * FROM hero LEFT JOIN team ON hero.team_id = team.id

# Nested eager loading
select(Team).options(
    selectinload(Team.heroes).selectinload(Hero.weapons)
)
```

### When to Use Which

| Relationship | Use | Why |
|--------------|-----|-----|
| One-to-many (collection) | `selectinload` | Avoids cartesian product |
| Many-to-one (single) | `joinedload` | Single query, small overhead |
| Many-to-many | `selectinload` | Handles link table efficiently |
| Deep nesting | `selectinload` chain | Predictable query count |

---

## Connection Leak

### The Problem

```python
# BAD: Connection leak - session never closed
def get_hero(hero_id: int):
    session = Session(engine)  # Opens connection
    hero = session.get(Hero, hero_id)
    return hero  # Connection never closed!
```

Over time: "FATAL: too many connections for role"

### The Solution: Always Use Context Managers

```python
# GOOD: Context manager auto-closes session
def get_hero(hero_id: int):
    with Session(engine) as session:
        hero = session.get(Hero, hero_id)
        return hero  # Session auto-closed

# GOOD: FastAPI dependency with yield
def get_session():
    with Session(engine) as session:
        yield session  # Cleanup happens after request
```

### Additional Safeguards

```python
engine = create_engine(
    DATABASE_URL,
    # Verify connection is alive before use
    pool_pre_ping=True,
    # Limit connection pool size
    pool_size=20,
    max_overflow=10,
    # Recycle stale connections
    pool_recycle=3600,
)
```

---

## Detached Instance Error

### The Problem

```python
# BAD: Accessing object after session closed
def get_hero_with_team(hero_id: int):
    with Session(engine) as session:
        hero = session.get(Hero, hero_id)

    # Session closed, hero is "detached"
    print(hero.team)  # Error: Instance not bound to a Session
```

### Solutions

**Solution 1: Access within session**

```python
def get_hero_with_team(hero_id: int):
    with Session(engine) as session:
        hero = session.get(Hero, hero_id)
        team_name = hero.team.name if hero.team else None  # Access while in session
    return {"hero": hero.name, "team": team_name}
```

**Solution 2: Eager load**

```python
def get_hero_with_team(hero_id: int):
    with Session(engine) as session:
        statement = select(Hero).where(Hero.id == hero_id).options(joinedload(Hero.team))
        hero = session.exec(statement).first()
    # hero.team is loaded, safe to access
    return hero
```

**Solution 3: Return response model**

```python
@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def get_hero(hero_id: int, session: Session = Depends(get_session)):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(404)
    return hero  # FastAPI serializes while session is open
```

---

## Transaction Deadlock

### The Problem

```python
# Transaction 1: Locks Hero 1, then tries to lock Hero 2
# Transaction 2: Locks Hero 2, then tries to lock Hero 1
# Result: DEADLOCK - both transactions wait forever
```

### Solutions

**Solution 1: Consistent lock ordering**

```python
def transfer_item(from_hero_id: int, to_hero_id: int, item_id: int):
    with Session(engine) as session:
        # Always lock in consistent order (by ID)
        first_id, second_id = sorted([from_hero_id, to_hero_id])

        hero1 = session.get(Hero, first_id)
        hero2 = session.get(Hero, second_id)

        # Now perform the transfer
        ...
        session.commit()
```

**Solution 2: Short transactions**

```python
# BAD: Long transaction
def process_heroes():
    with Session(engine) as session:
        heroes = session.exec(select(Hero)).all()
        for hero in heroes:
            external_api_call(hero)  # Slow! Holds locks
            hero.processed = True
        session.commit()

# GOOD: Process outside transaction
def process_heroes():
    with Session(engine) as session:
        heroes = session.exec(select(Hero)).all()
        hero_data = [(h.id, h.name) for h in heroes]  # Extract data

    # Process outside transaction
    for hero_id, name in hero_data:
        external_api_call(name)

        # Update in separate short transaction
        with Session(engine) as session:
            hero = session.get(Hero, hero_id)
            hero.processed = True
            session.commit()
```

**Solution 3: Optimistic locking**

```python
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    version: int = Field(default=1)  # Version column

def update_hero(hero_id: int, new_name: str, expected_version: int):
    with Session(engine) as session:
        hero = session.get(Hero, hero_id)
        if hero.version != expected_version:
            raise HTTPException(409, "Conflict: hero was modified")

        hero.name = new_name
        hero.version += 1
        session.commit()
```

---

## Stale Session Data

### The Problem

```python
# Session 1
with Session(engine) as session1:
    hero = session1.get(Hero, 1)
    print(hero.name)  # "Spider-Boy"

    # Meanwhile, Session 2 updates the hero
    # Session 1 still sees old data

    print(hero.name)  # Still "Spider-Boy" (stale!)
```

### Solutions

**Solution 1: Refresh from database**

```python
with Session(engine) as session:
    hero = session.get(Hero, 1)
    # ... time passes ...
    session.refresh(hero)  # Reload from database
    print(hero.name)  # Fresh data
```

**Solution 2: Expire and re-access**

```python
with Session(engine) as session:
    hero = session.get(Hero, 1)
    session.expire(hero)  # Mark as stale
    print(hero.name)  # Triggers fresh query
```

**Solution 3: New session for fresh data**

```python
def get_current_hero(hero_id: int):
    with Session(engine) as session:  # Fresh session = fresh data
        return session.get(Hero, hero_id)
```

---

## Unique Constraint Violation

### The Problem

```python
# User already exists with this email
@app.post("/users/")
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()  # IntegrityError: duplicate key value
```

### Solution: Handle IntegrityError

```python
from sqlalchemy.exc import IntegrityError

@app.post("/users/")
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User.model_validate(user)
    try:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists"
        )
```

### Check Before Insert (Alternative)

```python
@app.post("/users/")
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # Check first
    existing = session.exec(
        select(User).where(User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(409, "Email already registered")

    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

---

## Foreign Key Violation

### The Problem

```python
# Team with id=999 doesn't exist
hero = Hero(name="Test", team_id=999)
session.add(hero)
session.commit()  # IntegrityError: foreign key constraint
```

### Solution: Validate Foreign Keys

```python
@app.post("/heroes/")
def create_hero(hero: HeroCreate, session: Session = Depends(get_session)):
    # Validate foreign key
    if hero.team_id:
        team = session.get(Team, hero.team_id)
        if not team:
            raise HTTPException(404, f"Team {hero.team_id} not found")

    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero
```

---

## Memory Issues with Large Queries

### The Problem

```python
# BAD: Loads ALL records into memory
def export_all_heroes():
    with Session(engine) as session:
        heroes = session.exec(select(Hero)).all()  # 1 million rows in memory!
        return heroes
```

### Solution: Pagination or Streaming

**Pagination:**

```python
def export_heroes_paginated():
    page = 1
    per_page = 1000
    all_heroes = []

    while True:
        with Session(engine) as session:
            heroes = session.exec(
                select(Hero).offset((page - 1) * per_page).limit(per_page)
            ).all()

            if not heroes:
                break

            all_heroes.extend([h.model_dump() for h in heroes])
            page += 1

    return all_heroes
```

**Streaming (for very large datasets):**

```python
from fastapi.responses import StreamingResponse
import json

def generate_heroes():
    offset = 0
    limit = 1000

    yield "["
    first = True

    while True:
        with Session(engine) as session:
            heroes = session.exec(
                select(Hero).offset(offset).limit(limit)
            ).all()

            if not heroes:
                break

            for hero in heroes:
                if not first:
                    yield ","
                first = False
                yield json.dumps(hero.model_dump())

            offset += limit

    yield "]"

@app.get("/heroes/export")
def export_heroes():
    return StreamingResponse(
        generate_heroes(),
        media_type="application/json"
    )
```

---

## Committing Inside Loops

### The Problem

```python
# BAD: 1000 separate transactions = very slow
def create_many_heroes(heroes: list[HeroCreate]):
    with Session(engine) as session:
        for hero in heroes:
            db_hero = Hero.model_validate(hero)
            session.add(db_hero)
            session.commit()  # Commit per item = slow!
```

### Solution: Batch Commits

```python
# GOOD: Single transaction
def create_many_heroes(heroes: list[HeroCreate]):
    with Session(engine) as session:
        for hero in heroes:
            db_hero = Hero.model_validate(hero)
            session.add(db_hero)
        session.commit()  # One commit at the end

# GOOD: Batch commits for very large datasets
def create_many_heroes(heroes: list[HeroCreate], batch_size: int = 1000):
    with Session(engine) as session:
        for i, hero in enumerate(heroes):
            db_hero = Hero.model_validate(hero)
            session.add(db_hero)

            if (i + 1) % batch_size == 0:
                session.commit()  # Commit every N items

        session.commit()  # Final commit for remainder
```

---

## Session Object Already Attached

### The Problem

```python
# BAD: Adding same object twice
with Session(engine) as session:
    hero = Hero(name="Test")
    session.add(hero)
    session.add(hero)  # Warning: already attached
```

### Solution: Check State or Use merge

```python
from sqlalchemy import inspect

with Session(engine) as session:
    hero = Hero(name="Test")

    # Option 1: Check if pending
    if hero not in session.new:
        session.add(hero)

    # Option 2: Use merge (upsert-like)
    hero = session.merge(hero)

    session.commit()
```

---

## Async Session Issues

### Problem: Using Sync Operations in Async Context

```python
# BAD: Blocking call in async function
async def get_hero(hero_id: int, session: AsyncSession):
    return session.get(Hero, hero_id)  # Missing await!
```

### Solution: Always Await Async Operations

```python
async def get_hero(hero_id: int, session: AsyncSession):
    return await session.get(Hero, hero_id)

async def get_heroes(session: AsyncSession):
    result = await session.exec(select(Hero))
    return result.all()
```

---

## Migration Pitfalls

### Problem 1: Adding NOT NULL Without Default

```python
# Migration fails on existing data
op.add_column("hero", sa.Column("status", sa.String(), nullable=False))
```

**Solution: Two-step migration**

```python
# Step 1: Add nullable column with default
op.add_column("hero", sa.Column("status", sa.String(), nullable=True))
op.execute("UPDATE hero SET status = 'active' WHERE status IS NULL")

# Step 2: Make non-nullable (separate migration)
op.alter_column("hero", "status", nullable=False)
```

### Problem 2: Dropping Column with Data

```python
# Lost data cannot be recovered
op.drop_column("hero", "legacy_field")
```

**Solution: Deprecation cycle**

```python
# Migration 1: Mark as deprecated (optional column)
# Migration 2: Stop writing to it
# Migration 3: Drop after N releases
```

### Problem 3: Long-running Migrations

```python
# Locks table, causes downtime
op.create_index("ix_hero_name", "hero", ["name"])
```

**Solution: Concurrent index (PostgreSQL)**

```python
# Doesn't lock table
op.execute("CREATE INDEX CONCURRENTLY ix_hero_name ON hero(name)")
```
