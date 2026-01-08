"""Database session management and utilities."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings

# Create async engine only if DATABASE_URL is set
# Use NullPool for serverless/short-lived connections (Railway)
engine = None
AsyncSessionLocal = None

try:
    if settings.database_url_async:
        print(f"Database: Connecting to {settings.database_url_async[:30]}...")
        engine = create_async_engine(
            settings.database_url_async,
            echo=settings.debug,  # Log SQL in debug mode
            pool_pre_ping=True,   # Verify connections before using
            poolclass=NullPool,   # No connection pooling for Railway
        )

        # Create async session factory
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        print("Database: Engine created successfully")
    else:
        print("Database: DATABASE_URL not set - database features will be unavailable")
except Exception as e:
    print(f"Database: Failed to create engine: {e}")
    # Don't crash the app - let it start without database
    engine = None
    AsyncSessionLocal = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes to get database session.

    Usage:
        @app.get("/trends")
        async def get_trends(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Trend))
            trends = result.scalars().all()
            return trends
    """
    if not AsyncSessionLocal:
        raise RuntimeError("Database not initialized - DATABASE_URL environment variable not set")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database (create all tables).

    NOTE: In production, use Alembic migrations instead.
    This is only for development/testing.
    """
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    if engine:
        await engine.dispose()
