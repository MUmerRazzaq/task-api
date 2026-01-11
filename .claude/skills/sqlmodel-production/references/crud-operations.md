# SQLModel CRUD Operations

## Complete FastAPI CRUD Example

```python
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Models
class HeroBase(SQLModel):
    name: str = Field(index=True, max_length=100)
    secret_name: str = Field(max_length=255)
    age: int | None = Field(default=None, index=True)
    team_id: int | None = Field(default=None, foreign_key="team.id")

class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class HeroCreate(HeroBase):
    pass

class HeroPublic(HeroBase):
    id: int

class HeroUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None
    team_id: int | None = None

# Engine and session
engine = create_engine("sqlite:///database.db", echo=False)

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI()

# CREATE
@app.post("/heroes/", response_model=HeroPublic)
def create_hero(*, session: Session = Depends(get_session), hero: HeroCreate):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

# READ (list with pagination)
@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes

# READ (single)
@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

# UPDATE (partial)
@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(
    *,
    session: Session = Depends(get_session),
    hero_id: int,
    hero: HeroUpdate
):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

# DELETE
@app.delete("/heroes/{hero_id}")
def delete_hero(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}
```

---

## Async CRUD Operations

```python
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

async def get_async_session():
    async with AsyncSession(async_engine) as session:
        yield session

# CREATE
@app.post("/heroes/", response_model=HeroPublic)
async def create_hero(
    *,
    session: AsyncSession = Depends(get_async_session),
    hero: HeroCreate
):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    await session.commit()
    await session.refresh(db_hero)
    return db_hero

# READ (list)
@app.get("/heroes/", response_model=list[HeroPublic])
async def read_heroes(
    *,
    session: AsyncSession = Depends(get_async_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    result = await session.exec(select(Hero).offset(offset).limit(limit))
    return result.all()

# READ (single)
@app.get("/heroes/{hero_id}", response_model=HeroPublic)
async def read_hero(*, session: AsyncSession = Depends(get_async_session), hero_id: int):
    hero = await session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

# UPDATE
@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
async def update_hero(
    *,
    session: AsyncSession = Depends(get_async_session),
    hero_id: int,
    hero: HeroUpdate
):
    db_hero = await session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)
    session.add(db_hero)
    await session.commit()
    await session.refresh(db_hero)
    return db_hero

# DELETE
@app.delete("/heroes/{hero_id}")
async def delete_hero(*, session: AsyncSession = Depends(get_async_session), hero_id: int):
    hero = await session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    await session.delete(hero)
    await session.commit()
    return {"ok": True}
```

---

## Query Patterns

### Filtering

```python
from sqlmodel import select, col

# Single filter
statement = select(Hero).where(Hero.age > 30)
heroes = session.exec(statement).all()

# Multiple filters (AND)
statement = select(Hero).where(Hero.age > 30, Hero.team_id == 1)
# Or using multiple .where()
statement = select(Hero).where(Hero.age > 30).where(Hero.team_id == 1)

# OR conditions
from sqlalchemy import or_
statement = select(Hero).where(or_(Hero.age > 50, Hero.name == "Spider-Boy"))

# IN query
team_ids = [1, 2, 3]
statement = select(Hero).where(col(Hero.team_id).in_(team_ids))

# LIKE query
statement = select(Hero).where(col(Hero.name).contains("Spider"))
# Or for starts_with / ends_with
statement = select(Hero).where(col(Hero.name).startswith("Spider"))

# NULL check
statement = select(Hero).where(Hero.team_id == None)
statement = select(Hero).where(Hero.team_id != None)
```

### Sorting

```python
from sqlmodel import col

# Ascending (default)
statement = select(Hero).order_by(Hero.name)

# Descending
statement = select(Hero).order_by(col(Hero.age).desc())

# Multiple columns
statement = select(Hero).order_by(Hero.team_id, col(Hero.name).desc())
```

### Pagination

```python
# Offset-based pagination
def get_heroes_paginated(session: Session, page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page
    statement = select(Hero).offset(offset).limit(per_page)
    return session.exec(statement).all()

# With total count
from sqlalchemy import func

def get_heroes_with_count(session: Session, page: int = 1, per_page: int = 20):
    offset = (page - 1) * per_page

    # Get total count
    count_statement = select(func.count()).select_from(Hero)
    total = session.exec(count_statement).one()

    # Get page data
    statement = select(Hero).offset(offset).limit(per_page)
    heroes = session.exec(statement).all()

    return {
        "items": heroes,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }
```

---

## Bulk Operations

### Bulk Create

```python
def bulk_create_heroes(session: Session, heroes: list[HeroCreate]) -> list[Hero]:
    db_heroes = [Hero.model_validate(hero) for hero in heroes]
    session.add_all(db_heroes)
    session.commit()
    for hero in db_heroes:
        session.refresh(hero)
    return db_heroes
```

### Bulk Update

```python
from sqlmodel import update

def bulk_update_team(session: Session, old_team_id: int, new_team_id: int):
    statement = (
        update(Hero)
        .where(Hero.team_id == old_team_id)
        .values(team_id=new_team_id)
    )
    session.exec(statement)
    session.commit()
```

### Bulk Delete

```python
from sqlmodel import delete

def bulk_delete_by_team(session: Session, team_id: int):
    statement = delete(Hero).where(Hero.team_id == team_id)
    session.exec(statement)
    session.commit()
```

---

## Soft Delete Pattern

```python
from datetime import datetime

class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    is_deleted: bool = Field(default=False, index=True)
    deleted_at: datetime | None = None

# Soft delete endpoint
@app.delete("/heroes/{hero_id}")
def soft_delete_hero(*, session: Session = Depends(get_session), hero_id: int):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    hero.is_deleted = True
    hero.deleted_at = datetime.utcnow()
    session.add(hero)
    session.commit()
    return {"ok": True}

# Filter out deleted in queries
@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(*, session: Session = Depends(get_session)):
    statement = select(Hero).where(Hero.is_deleted == False)
    return session.exec(statement).all()
```

---

## Upsert (Insert or Update)

```python
def upsert_hero(session: Session, hero_data: HeroCreate, hero_id: int | None = None):
    if hero_id:
        db_hero = session.get(Hero, hero_id)
        if db_hero:
            # Update existing
            hero_dict = hero_data.model_dump(exclude_unset=True)
            db_hero.sqlmodel_update(hero_dict)
            session.add(db_hero)
            session.commit()
            session.refresh(db_hero)
            return db_hero

    # Create new
    db_hero = Hero.model_validate(hero_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero
```
