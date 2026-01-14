"""Database connection and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.config import settings

# Build engine options based on database type
engine_options: dict = {
    "echo": settings.log_level == "DEBUG",
}

# SQLite doesn't support connection pooling options
if not settings.database_url.startswith("sqlite"):
    engine_options.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
    })
else:
    # SQLite needs check_same_thread=False for async
    engine_options["connect_args"] = {"check_same_thread": False}

# Create async engine
engine = create_async_engine(settings.database_url, **engine_options)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session for dependency injection."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database by creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
