# SQLModel Session Management

## Engine Configuration

### Development Engine

```python
from sqlmodel import create_engine

# SQLite (development)
sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, echo=True)  # echo=True for debugging

# In-memory SQLite (testing)
from sqlalchemy.pool import StaticPool

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
```

### Production Engine (PostgreSQL)

```python
from sqlmodel import create_engine

DATABASE_URL = "postgresql://user:password@localhost:5432/dbname"

engine = create_engine(
    DATABASE_URL,
    echo=False,  # NEVER True in production
    pool_size=20,  # Number of persistent connections
    max_overflow=10,  # Additional connections when pool full
    pool_pre_ping=True,  # Verify connection before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={
        "sslmode": "require",  # Enforce SSL
        "connect_timeout": 10,
    },
)
```

### Production Engine (MySQL)

```python
DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/dbname"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "ssl": {"ssl_mode": "REQUIRED"},
        "connect_timeout": 10,
    },
)
```

---

## Sync Session Management

### Basic Session Usage

```python
from sqlmodel import Session

# Context manager (recommended) - auto-closes session
with Session(engine) as session:
    hero = Hero(name="Spider-Boy", secret_name="Pedro")
    session.add(hero)
    session.commit()
    session.refresh(hero)  # Get DB-generated values
    print(hero.id)  # Now has the ID
```

### FastAPI Dependency

```python
from fastapi import Depends, FastAPI
from sqlmodel import Session

app = FastAPI()

def get_session():
    with Session(engine) as session:
        yield session

@app.post("/heroes/")
def create_hero(*, session: Session = Depends(get_session), hero: HeroCreate):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero
```

### Session with Transaction Control

```python
from sqlmodel import Session

def transfer_hero(hero_id: int, from_team_id: int, to_team_id: int):
    with Session(engine) as session:
        try:
            hero = session.get(Hero, hero_id)
            if not hero or hero.team_id != from_team_id:
                raise ValueError("Hero not found in source team")

            # Multiple operations in one transaction
            hero.team_id = to_team_id
            session.add(hero)

            # Log the transfer
            log = TransferLog(hero_id=hero_id, from_team=from_team_id, to_team=to_team_id)
            session.add(log)

            session.commit()
        except Exception:
            session.rollback()
            raise
```

---

## Async Session Management

### Async Engine Setup

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

# PostgreSQL with asyncpg
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/dbname"

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
```

### Async FastAPI Dependency

```python
from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(async_engine) as session:
        yield session

@app.post("/heroes/")
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
```

### Async Query Operations

```python
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

async def get_heroes_by_team(session: AsyncSession, team_id: int) -> list[Hero]:
    statement = select(Hero).where(Hero.team_id == team_id)
    result = await session.exec(statement)
    return result.all()

async def get_hero_by_id(session: AsyncSession, hero_id: int) -> Hero | None:
    return await session.get(Hero, hero_id)
```

---

## Connection Pool Configuration

### Pool Parameters Explained

```python
engine = create_engine(
    DATABASE_URL,

    # pool_size: Persistent connections kept open
    # - Too low: Connection contention under load
    # - Too high: Wastes database resources
    # - Rule: Start with 5-10, increase based on concurrent users
    pool_size=20,

    # max_overflow: Additional connections when pool exhausted
    # - Temporary connections, closed when returned to pool
    # - Total max connections = pool_size + max_overflow
    max_overflow=10,

    # pool_pre_ping: Test connection before use
    # - Prevents "connection closed" errors
    # - Small overhead, but essential for production
    pool_pre_ping=True,

    # pool_recycle: Seconds before connection is recycled
    # - Prevents stale connections
    # - Set lower than database wait_timeout
    # - MySQL default wait_timeout is 28800 (8 hours)
    pool_recycle=3600,

    # pool_timeout: Seconds to wait for available connection
    # - Raises exception if timeout exceeded
    # - Default is 30 seconds
    pool_timeout=30,
)
```

### Environment-Based Configuration

```python
import os
from sqlmodel import create_engine

def get_engine():
    database_url = os.getenv("DATABASE_URL")
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        return create_engine(
            database_url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    elif environment == "testing":
        from sqlalchemy.pool import StaticPool
        return create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:  # development
        return create_engine(
            database_url or "sqlite:///dev.db",
            echo=True,
            pool_pre_ping=True,
        )

engine = get_engine()
```

---

## Table Creation

### Create All Tables

```python
from sqlmodel import SQLModel

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# In FastAPI
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Or with lifespan (FastAPI 0.100+)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
```

### Async Table Creation

```python
from sqlmodel import SQLModel

async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

---

## Session Lifecycle Rules

1. **Always use context managers** - Ensures proper cleanup
2. **One session per request** - Never share sessions across requests
3. **Commit explicitly** - Auto-commit is disabled by default
4. **Refresh after commit** - Get database-generated values
5. **Don't hold sessions long** - Keep transactions short
6. **Handle exceptions** - Rollback on error
