"""Rate limiting implementations for API collectors."""
import asyncio
from datetime import datetime, timedelta, date
from typing import Optional
from collections import deque
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_quota_usage import ApiQuotaUsage


class RequestsPerMinuteRateLimiter:
    """Rate limiter using sliding window algorithm for requests/minute limits.

    Example: Reddit API allows 60 requests/minute with OAuth.

    Usage:
        limiter = RequestsPerMinuteRateLimiter(limit=60, window_seconds=60)

        async with limiter:
            # Make API call here
            response = await api.get()
    """

    def __init__(self, limit: int, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            limit: Maximum number of requests allowed in window
            window_seconds: Time window in seconds (default: 60)
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = deque()  # Timestamps of recent requests

    async def __aenter__(self):
        """Async context manager entry - wait if rate limit exceeded."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    async def acquire(self):
        """Wait until request can be made without exceeding rate limit."""
        now = datetime.utcnow()

        # Remove requests outside current window
        cutoff = now - timedelta(seconds=self.window_seconds)
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

        # If at limit, wait until oldest request expires
        if len(self.requests) >= self.limit:
            oldest_request = self.requests[0]
            wait_until = oldest_request + timedelta(seconds=self.window_seconds)
            wait_seconds = (wait_until - now).total_seconds()

            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

        # Record this request
        self.requests.append(datetime.utcnow())

    def get_remaining(self) -> int:
        """Get number of requests remaining in current window."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Clean up old requests
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

        return max(0, self.limit - len(self.requests))


class DailyQuotaRateLimiter:
    """Daily quota rate limiter with database persistence.

    Example: YouTube API has 10,000 units/day quota.

    Usage:
        limiter = DailyQuotaRateLimiter(
            api_name="youtube",
            daily_limit=10000,
            db_session=db
        )

        if await limiter.can_consume(units=1):
            # Make API call that costs 1 unit
            response = await youtube.videos().list()
            await limiter.increment_usage(units=1)
    """

    def __init__(
        self,
        api_name: str,
        daily_limit: int,
        db_session: AsyncSession,
        warning_threshold: float = 0.8
    ):
        """Initialize daily quota limiter.

        Args:
            api_name: API identifier (e.g., "youtube", "claude")
            daily_limit: Maximum units allowed per day
            db_session: Database session for quota tracking
            warning_threshold: Log warning when usage exceeds this fraction
        """
        self.api_name = api_name
        self.daily_limit = daily_limit
        self.db_session = db_session
        self.warning_threshold = warning_threshold

    async def get_usage_today(self) -> int:
        """Get current quota usage for today.

        Returns:
            Number of units used today
        """
        today = date.today()

        result = await self.db_session.execute(
            select(ApiQuotaUsage.units_used)
            .where(ApiQuotaUsage.api_name == self.api_name)
            .where(ApiQuotaUsage.date == today)
        )

        row = result.scalar_one_or_none()
        return row if row is not None else 0

    async def increment_usage(self, units: int) -> int:
        """Increment quota usage and return new total.

        Args:
            units: Number of units to add

        Returns:
            New total usage for today
        """
        today = date.today()

        # Upsert: insert or update on conflict
        stmt = insert(ApiQuotaUsage).values(
            api_name=self.api_name,
            date=today,
            units_used=units
        ).on_conflict_do_update(
            index_elements=['api_name', 'date'],
            set_={'units_used': ApiQuotaUsage.units_used + units}
        )

        await self.db_session.execute(stmt)
        await self.db_session.commit()

        # Get new total
        new_total = await self.get_usage_today()

        # Log warning if approaching limit
        if new_total >= self.daily_limit * self.warning_threshold:
            percentage = (new_total / self.daily_limit) * 100
            import logging
            logging.warning(
                f"{self.api_name} quota at {new_total}/{self.daily_limit} ({percentage:.1f}%)"
            )

        return new_total

    async def can_consume(self, units: int) -> bool:
        """Check if consuming units would exceed daily limit.

        Args:
            units: Number of units to check

        Returns:
            True if consumption would stay within limit
        """
        current_usage = await self.get_usage_today()
        return (current_usage + units) <= self.daily_limit

    def get_remaining(self) -> int:
        """Get remaining quota for today (synchronous helper).

        Note: This returns a cached value, call get_usage_today() for fresh data.
        """
        import asyncio
        current = asyncio.run(self.get_usage_today())
        return max(0, self.daily_limit - current)
