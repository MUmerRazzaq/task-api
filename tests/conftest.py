"""Pytest configuration and shared fixtures."""

import os
from collections.abc import AsyncGenerator
from typing import Any

# Set test environment BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.database import get_session
from src.main import app

# Test database URL - uses SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create test database engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide test database session with transaction rollback."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide test client with overridden database session."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_task_data() -> dict[str, Any]:
    """Valid task data for testing."""
    return {
        "title": "Write documentation",
        "description": "Create API documentation for task endpoints",
    }


@pytest.fixture
def sample_task_data_minimal() -> dict[str, Any]:
    """Valid task data with only required fields."""
    return {
        "title": "Simple task",
    }


@pytest.fixture
def completed_task_data() -> dict[str, Any]:
    """Completed task data for testing."""
    return {
        "title": "Deploy to production",
        "description": None,
        "is_completed": True,
    }
