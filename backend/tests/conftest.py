"""
Pytest configuration and fixtures for database tests
"""
import asyncio
import os
import pytest
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.models.base import Base


# Get test database URL from environment, or derive from main DATABASE_URL
def get_test_database_url() -> str:
    """Get test database URL from environment variables"""
    test_url = os.getenv("TEST_DATABASE_URL")
    if test_url:
        # Convert to async format if needed
        if test_url.startswith("postgresql://"):
            return test_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return test_url

    # Fall back to main DATABASE_URL with _test suffix
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None  # No database available

    # Convert to async format and add _test suffix
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Add _test suffix to database name
    # Example: postgresql+asyncpg://user:pass@host:5432/dbname -> postgresql+asyncpg://user:pass@host:5432/dbname_test
    parts = database_url.rsplit("/", 1)
    if len(parts) == 2:
        return f"{parts[0]}/{parts[1]}_test"

    return database_url


# Create test engine only if database URL is available
_test_db_url = get_test_database_url()
test_engine = None
TestSessionLocal = None

if _test_db_url:
    test_engine = create_async_engine(
        _test_db_url,
        echo=False,
        poolclass=NullPool,
    )

    # Create test session factory
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=False)  # Changed autouse to False
async def setup_database():
    """Create all tables before running tests, drop them after

    Note: Not autouse to avoid async fixture issues in pytest 9.
    Tests requiring database should depend on async_session which will set up database.
    """
    if test_engine is None:
        # Skip database setup if no database URL configured
        yield
        return

    async with test_engine.begin() as conn:
        # Drop all tables first (clean slate)
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup: drop all tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def async_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session that rolls back after each test"""
    if TestSessionLocal is None:
        pytest.skip("Database not configured - set DATABASE_URL or TEST_DATABASE_URL")

    async with TestSessionLocal() as session:
        # Start a transaction
        async with session.begin():
            yield session
            # Rollback happens automatically when context exits
            # This ensures each test gets a clean database state
            await session.rollback()
