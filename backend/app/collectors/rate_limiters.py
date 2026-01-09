"""Rate limiting implementations for API collectors."""
import asyncio
import logging
from datetime import datetime, timedelta, date, timezone
from typing import Optional
from collections import deque
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_quota_usage import ApiQuotaUsage

logger = logging.getLogger(__name__)


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
        now = datetime.now(timezone.utc)

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

        # Record this request (re-fetch time after potential sleep)
        self.requests.append(datetime.now(timezone.utc))

    def get_remaining(self) -> int:
        """Get number of requests remaining in current window."""
        now = datetime.now(timezone.utc)
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

        Note:
            Does NOT commit the transaction - caller must commit.
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
        # Removed commit - let caller control transaction

        # Get new total
        new_total = await self.get_usage_today()

        # Log warning if approaching limit
        if new_total >= self.daily_limit * self.warning_threshold:
            percentage = (new_total / self.daily_limit) * 100
            logger.warning(
                f"{self.api_name} quota at {new_total}/{self.daily_limit} ({percentage:.1f}%)",
                extra={
                    "event": "quota_warning",
                    "api": self.api_name,
                    "usage": new_total,
                    "limit": self.daily_limit,
                    "percentage": percentage
                }
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

    async def get_remaining(self) -> int:
        """Get remaining quota for today.

        Returns:
            Number of units remaining in today's quota
        """
        current = await self.get_usage_today()
        return max(0, self.daily_limit - current)

    class ConsumeContext:
        """Async context manager for quota consumption."""

        def __init__(self, limiter: 'DailyQuotaRateLimiter', units: int):
            self.limiter = limiter
            self.units = units
            self.consumed = False

        async def __aenter__(self):
            """Check quota before entering context."""
            if not await self.limiter.can_consume(self.units):
                raise RuntimeError(
                    f"{self.limiter.api_name} quota exceeded: "
                    f"{await self.limiter.get_usage_today()}/{self.limiter.daily_limit} units used"
                )
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            """Increment usage on successful completion."""
            # Only increment if no exception occurred
            if exc_type is None:
                await self.limiter.increment_usage(self.units)
                self.consumed = True

    def consume(self, units: int) -> ConsumeContext:
        """Create async context manager for quota consumption.

        Usage:
            async with limiter.consume(units=1):
                # Make API call that costs 1 unit
                response = await youtube.videos().list()
                # Usage auto-incremented on success

        Args:
            units: Number of units to consume

        Returns:
            Async context manager that checks quota and increments usage
        """
        return self.ConsumeContext(self, units)
