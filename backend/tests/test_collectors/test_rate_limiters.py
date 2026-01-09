"""Tests for rate limiter classes."""
import pytest
import asyncio
from datetime import datetime, timedelta, date
from app.collectors.rate_limiters import RequestsPerMinuteRateLimiter, DailyQuotaRateLimiter
from app.models.api_quota_usage import ApiQuotaUsage


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_within_limit():
    """Test that rate limiter allows requests within limit."""
    limiter = RequestsPerMinuteRateLimiter(limit=3, window_seconds=2)

    start = datetime.utcnow()

    # Make 3 requests (should complete immediately)
    for _ in range(3):
        async with limiter:
            pass

    elapsed = (datetime.utcnow() - start).total_seconds()
    assert elapsed < 0.1  # Should be instant


@pytest.mark.asyncio
async def test_rate_limiter_enforces_limit():
    """Test that rate limiter blocks requests exceeding limit."""
    limiter = RequestsPerMinuteRateLimiter(limit=2, window_seconds=1)

    # Make 2 requests (should complete immediately)
    async with limiter:
        pass
    async with limiter:
        pass

    # 3rd request should wait ~1 second
    start = datetime.utcnow()
    async with limiter:
        pass
    elapsed = (datetime.utcnow() - start).total_seconds()

    assert elapsed >= 0.9  # Should wait ~1 second


@pytest.mark.asyncio
async def test_rate_limiter_get_remaining():
    """Test that get_remaining returns correct count."""
    limiter = RequestsPerMinuteRateLimiter(limit=5, window_seconds=2)

    assert limiter.get_remaining() == 5

    async with limiter:
        pass
    assert limiter.get_remaining() == 4

    async with limiter:
        pass
    async with limiter:
        pass
    assert limiter.get_remaining() == 2


@pytest.mark.asyncio
async def test_rate_limiter_sliding_window():
    """Test that sliding window properly expires old requests."""
    limiter = RequestsPerMinuteRateLimiter(limit=2, window_seconds=1)

    # Make 2 requests
    async with limiter:
        pass
    async with limiter:
        pass

    # Wait for window to expire
    await asyncio.sleep(1.1)

    # Should be able to make 2 more requests immediately
    start = datetime.utcnow()
    async with limiter:
        pass
    async with limiter:
        pass
    elapsed = (datetime.utcnow() - start).total_seconds()

    assert elapsed < 0.1  # Should be instant


@pytest.mark.asyncio
async def test_daily_quota_limiter_get_usage_today(async_session):
    """Test getting current quota usage for today."""
    limiter = DailyQuotaRateLimiter(
        api_name="test_api",
        daily_limit=1000,
        db_session=async_session
    )

    # Initially should be 0
    usage = await limiter.get_usage_today()
    assert usage == 0


@pytest.mark.asyncio
async def test_daily_quota_limiter_increment_usage(async_session):
    """Test incrementing quota usage."""
    limiter = DailyQuotaRateLimiter(
        api_name="test_api_increment",
        daily_limit=1000,
        db_session=async_session
    )

    # Increment by 10
    new_total = await limiter.increment_usage(10)
    assert new_total == 10

    # Increment by 5 more
    new_total = await limiter.increment_usage(5)
    assert new_total == 15


@pytest.mark.asyncio
async def test_daily_quota_limiter_can_consume(async_session):
    """Test checking if quota consumption is within limit."""
    limiter = DailyQuotaRateLimiter(
        api_name="test_api_can_consume",
        daily_limit=100,
        db_session=async_session
    )

    # Should be able to consume 50
    can_consume = await limiter.can_consume(50)
    assert can_consume is True

    # Consume 90
    await limiter.increment_usage(90)

    # Should not be able to consume 20 more (would exceed 100)
    can_consume = await limiter.can_consume(20)
    assert can_consume is False

    # Should be able to consume 10 (would be exactly 100)
    can_consume = await limiter.can_consume(10)
    assert can_consume is True


@pytest.mark.asyncio
async def test_daily_quota_limiter_upsert_same_day(async_session):
    """Test that incrementing on same day updates existing record."""
    limiter = DailyQuotaRateLimiter(
        api_name="test_api_upsert",
        daily_limit=1000,
        db_session=async_session
    )

    # First increment
    await limiter.increment_usage(10)

    # Second increment should update, not create new record
    await limiter.increment_usage(5)

    # Check total
    usage = await limiter.get_usage_today()
    assert usage == 15

    # Verify only one record exists for today
    from sqlalchemy import select, func
    today = date.today()
    result = await async_session.execute(
        select(func.count())
        .select_from(ApiQuotaUsage)
        .where(ApiQuotaUsage.api_name == "test_api_upsert")
        .where(ApiQuotaUsage.date == today)
    )
    count = result.scalar()
    assert count == 1
