"""
Tests for database models
"""
import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.models.trend import Trend
from app.models.data_collection import DataCollection
from app.models.user import User
from app.models.api_quota_usage import ApiQuotaUsage


@pytest.mark.asyncio
async def test_user_unique_username_constraint(async_session):
    """Test that username uniqueness is enforced"""
    # Create first user
    user1 = User(username="testuser", password_hash="hash123")
    async_session.add(user1)
    await async_session.commit()

    # Try to create duplicate username
    user2 = User(username="testuser", password_hash="hash456")
    async_session.add(user2)

    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_api_quota_usage_unique_constraint(async_session):
    """Test that api_name + date uniqueness is enforced"""
    from datetime import date

    # Create first entry
    quota1 = ApiQuotaUsage(api_name="youtube", date=date(2026, 1, 1), units_used=100)
    async_session.add(quota1)
    await async_session.commit()

    # Try to create duplicate api_name + date
    quota2 = ApiQuotaUsage(api_name="youtube", date=date(2026, 1, 1), units_used=200)
    async_session.add(quota2)

    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_confidence_level_check_constraint(async_session):
    """Test that confidence_level check constraint is enforced"""
    collection = DataCollection(status="in_progress")
    async_session.add(collection)
    await async_session.commit()

    # Try to create trend with invalid confidence level
    trend = Trend(
        title="Test Trend",
        collection_id=collection.id,
        confidence_level="invalid"  # Should fail
    )
    async_session.add(trend)

    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_confidence_level_valid_values(async_session):
    """Test that valid confidence levels are accepted"""
    collection = DataCollection(status="in_progress")
    async_session.add(collection)
    await async_session.commit()

    for level in ["high", "medium", "low"]:
        trend = Trend(
            title=f"Test Trend {level}",
            collection_id=collection.id,
            confidence_level=level
        )
        async_session.add(trend)
        await async_session.commit()

        # Verify it was created
        result = await async_session.execute(
            select(Trend).where(Trend.title == f"Test Trend {level}")
        )
        saved_trend = result.scalar_one()
        assert saved_trend.confidence_level == level


@pytest.mark.asyncio
async def test_data_collection_status_check_constraint(async_session):
    """Test that status check constraint is enforced"""
    # Try to create collection with invalid status
    collection = DataCollection(status="invalid_status")
    async_session.add(collection)

    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_data_collection_valid_statuses(async_session):
    """Test that valid statuses are accepted"""
    for status in ["in_progress", "completed", "failed"]:
        collection = DataCollection(status=status)
        async_session.add(collection)
        await async_session.commit()

        # Verify it was created
        result = await async_session.execute(
            select(DataCollection).where(DataCollection.id == collection.id)
        )
        saved_collection = result.scalar_one()
        assert saved_collection.status == status

        # Clean up for next iteration
        await async_session.delete(saved_collection)
        await async_session.commit()


@pytest.mark.asyncio
async def test_foreign_key_cascade_delete(async_session):
    """Test that deleting collection cascades to trends"""
    # Create collection
    collection = DataCollection(status="completed")
    async_session.add(collection)
    await async_session.commit()

    # Create trends linked to collection
    trend1 = Trend(title="Trend 1", collection_id=collection.id)
    trend2 = Trend(title="Trend 2", collection_id=collection.id)
    async_session.add_all([trend1, trend2])
    await async_session.commit()

    trend1_id = trend1.id
    trend2_id = trend2.id

    # Delete collection
    await async_session.delete(collection)
    await async_session.commit()

    # Verify trends were also deleted (cascade)
    result = await async_session.execute(
        select(Trend).where(Trend.id.in_([trend1_id, trend2_id]))
    )
    remaining_trends = result.scalars().all()
    assert len(remaining_trends) == 0, "Trends should be cascade deleted"


@pytest.mark.asyncio
async def test_trend_jsonb_columns(async_session):
    """Test that JSONB columns work correctly"""
    collection = DataCollection(status="completed")
    async_session.add(collection)
    await async_session.commit()

    # Create trend with JSONB data
    trend = Trend(
        title="Test Trend",
        collection_id=collection.id,
        google_trends_related_queries={"rising": ["query1", "query2"], "top": ["query3"]},
        similarweb_sources={"direct": 45.2, "search": 30.1, "social": 24.7}
    )
    async_session.add(trend)
    await async_session.commit()

    # Retrieve and verify
    result = await async_session.execute(
        select(Trend).where(Trend.id == trend.id)
    )
    saved_trend = result.scalar_one()

    assert saved_trend.google_trends_related_queries["rising"] == ["query1", "query2"]
    assert saved_trend.similarweb_sources["direct"] == 45.2


@pytest.mark.asyncio
async def test_trend_timestamps_auto_set(async_session):
    """Test that created_at is automatically set"""
    collection = DataCollection(status="completed")
    async_session.add(collection)
    await async_session.commit()

    trend = Trend(title="Test Trend", collection_id=collection.id)
    async_session.add(trend)
    await async_session.commit()

    assert trend.created_at is not None
    assert isinstance(trend.created_at, datetime)


@pytest.mark.asyncio
async def test_user_timestamps_auto_set(async_session):
    """Test that user created_at is automatically set"""
    user = User(username="testuser", password_hash="hash123")
    async_session.add(user)
    await async_session.commit()

    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)


@pytest.mark.asyncio
async def test_trend_nullable_columns(async_session):
    """Test that API metric columns can be null (partial data collection)"""
    collection = DataCollection(status="completed")
    async_session.add(collection)
    await async_session.commit()

    # Create trend with minimal data (all API metrics null)
    trend = Trend(
        title="Minimal Trend",
        collection_id=collection.id,
        # All API metrics are optional
    )
    async_session.add(trend)
    await async_session.commit()

    # Should succeed - nullable columns allow partial data
    result = await async_session.execute(
        select(Trend).where(Trend.id == trend.id)
    )
    saved_trend = result.scalar_one()
    assert saved_trend.reddit_score is None
    assert saved_trend.youtube_views is None
    assert saved_trend.google_trends_interest is None
