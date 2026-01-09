# Story 2.1: API Collector Infrastructure

**Status:** ready-for-dev
**Epic:** 2 - Multi-Source Data Collection Pipeline
**Story ID:** 2.1
**Created:** 2026-01-09

---

## Story

As a **developer**,
I want **a modular DataCollector interface pattern with async/parallel orchestration**,
So that **I can easily add multiple API collectors that run in parallel with retry logic and graceful degradation**.

---

## Acceptance Criteria

**Given** backend FastAPI is operational
**When** I create the base collector infrastructure
**Then** DataCollector abstract base class exists with methods: `collect(topics: List[str]) -> CollectionResult`, `health_check() -> bool`, `get_rate_limit_info() -> RateLimitInfo`
**And** CollectionOrchestrator class exists with method: `collect_all(topics: List[str]) -> Dict[str, CollectionResult]`
**And** CollectionOrchestrator uses `asyncio.gather()` to run all collectors in parallel
**And** RateLimiter classes exist: `RequestsPerMinuteRateLimiter(limit: int, window: int)`, `DailyQuotaRateLimiter(limit: int)`
**And** `retry_with_backoff()` decorator exists with exponential backoff: 2s, 4s, 8s (max 3 attempts)
**And** CollectionResult dataclass exists with fields: `source` (str), `data` (List[Optional[Dict]]), `success_rate` (float)
**And** Failed API calls return None in data list instead of crashing (graceful degradation)
**And** All async functions use proper exception handling with try/except blocks
**And** Structured JSON logging implemented for all API calls: `{"event": "api_call", "api": "reddit", "success": true, "duration_ms": 234.5}`

---

## Developer Context & Implementation Guide

### 🎯 Epic Context

This story is the **first story** in Epic 2: Multi-Source Data Collection Pipeline. It establishes the foundational infrastructure that all subsequent API collector stories (2.2-2.5) will build upon.

**Epic Goal:** Build robust data collection system that automatically gathers trend data from 4 platforms daily, with manual trigger option and graceful error handling.

**Dependencies:**
- ✅ **Epic 1 (Foundation & Authentication)** - COMPLETE
  - Story 1.1: Railway deployment operational
  - Story 1.2: Database schema created (trends, data_collections tables ready)
  - Story 1.3: FastAPI backend with JWT auth
  - Story 1.4: Next.js frontend with login

**Dependent Stories (blocked by this story):**
- **Story 2.2:** Reddit Data Collection - Needs DataCollector ABC and RateLimiters
- **Story 2.3:** YouTube Data Collection - Needs DataCollector ABC and quota tracking
- **Story 2.4:** Google Trends Collection - Needs DataCollector ABC and retry logic
- **Story 2.5:** SimilarWeb Collection - Needs DataCollector ABC and orchestration
- **Story 2.6:** Manual Collection Trigger - Needs CollectionOrchestrator.collect_all()
- **Story 2.7:** Automated Scheduling - Needs complete collection pipeline

---

## Technical Requirements

### Architecture Decision References

This story implements foundational patterns from Architecture Document:

#### API Integration Requirements (from AD-5: API Integration Architecture)

**Modular Collector Pattern:**
- Abstract base class `DataCollector` defining standard interface
- Standardized method signatures for health checks and rate limit info
- Factory pattern for instantiating specific collectors

**Async/Parallel Collection:**
- Use Python `asyncio` for concurrent API calls
- `asyncio.gather()` for parallel execution with return_exceptions=True
- Async context managers for proper resource cleanup

**Rate Limiting:**
- Per-API rate limiters to prevent hitting API limits
- Reddit: 60 requests/minute (OAuth authenticated)
- YouTube: Daily quota tracking (10,000 units/day)
- Google Trends: 60-second delays between requests
- SimilarWeb: Standard HTTP rate limiting

**Retry Logic:**
- Exponential backoff: 2s → 4s → 8s
- Maximum 3 retry attempts per API call
- Decorator pattern for reusable retry logic
- Preserve original exception context for debugging

**Graceful Degradation:**
- Individual API failures don't crash entire collection
- Return None for failed data points
- Calculate success_rate metrics (successful_calls / total_calls)
- Continue collection even if some APIs fail

#### Structured Logging (from AD-10: Observability)

**JSON Format for All API Calls:**
```json
{
  "event": "api_call",
  "api": "reddit",
  "topic": "r/videos",
  "success": true,
  "duration_ms": 234.5,
  "timestamp": "2026-01-09T10:30:45Z"
}
```

**Error Logging:**
```json
{
  "event": "api_call",
  "api": "youtube",
  "topic": "channel_id",
  "success": false,
  "error": "QuotaExceeded",
  "retry_attempt": 2,
  "duration_ms": 1023.2
}
```

---

## Implementation Tasks

### Task 1: Create DataCollector Abstract Base Class

**Acceptance Criteria:** AC #1 (DataCollector ABC with specified methods)

**Subtasks:**
- [ ] Create `backend/app/collectors/base.py` module
- [ ] Define DataCollector ABC with abstract methods
- [ ] Define CollectionResult dataclass
- [ ] Define RateLimitInfo dataclass
- [ ] Add comprehensive docstrings

**Implementation Steps:**

1. **Create collectors module** (backend/app/collectors/__init__.py):
```python
"""Data collection infrastructure for multi-source API integration."""
from .base import DataCollector, CollectionResult, RateLimitInfo
from .orchestrator import CollectionOrchestrator

__all__ = [
    "DataCollector",
    "CollectionResult",
    "RateLimitInfo",
    "CollectionOrchestrator",
]
```

2. **Create DataCollector ABC** (backend/app/collectors/base.py):
```python
"""Abstract base class for data collectors with standardized interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class RateLimitInfo:
    """Rate limiting information for API collector.

    Attributes:
        limit: Maximum requests allowed in time window
        remaining: Requests remaining in current window
        reset_at: When the rate limit window resets
        quota_type: Type of quota ("per_minute", "per_day", etc.)
    """
    limit: int
    remaining: int
    reset_at: datetime
    quota_type: str


@dataclass
class CollectionResult:
    """Result of data collection from a single source.

    Attributes:
        source: API source name (e.g., "reddit", "youtube")
        data: List of collected data points (None for failed calls)
        success_rate: Fraction of successful API calls (0.0-1.0)
        total_calls: Total number of API calls attempted
        successful_calls: Number of successful API calls
        failed_calls: Number of failed API calls
        errors: List of error messages encountered
        duration_seconds: Total collection duration in seconds
    """
    source: str
    data: List[Optional[Dict[str, Any]]]
    success_rate: float
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    errors: List[str] = None
    duration_seconds: float = 0.0

    def __post_init__(self):
        """Initialize computed fields."""
        if self.errors is None:
            self.errors = []

        # Calculate success rate if not provided
        if self.total_calls > 0 and self.success_rate == 0.0:
            self.success_rate = self.successful_calls / self.total_calls


class DataCollector(ABC):
    """Abstract base class for API data collectors.

    All API collectors (Reddit, YouTube, Google Trends, SimilarWeb) must
    inherit from this class and implement the required methods.

    Key Design Principles:
    - Async-first: All collection methods are async for parallel execution
    - Graceful degradation: Failed calls return None, don't crash
    - Rate limiting: Built-in rate limit tracking and enforcement
    - Structured logging: All API calls logged in JSON format
    - Testable: Abstract interface allows mocking in tests

    Example:
        class RedditCollector(DataCollector):
            async def collect(self, topics: List[str]) -> CollectionResult:
                # Implementation here
                pass
    """

    def __init__(self, name: str):
        """Initialize collector with name.

        Args:
            name: Collector name (e.g., "reddit", "youtube")
        """
        self.name = name

    @abstractmethod
    async def collect(self, topics: List[str]) -> CollectionResult:
        """Collect data from API for given topics.

        This method must:
        1. Make API calls for each topic
        2. Apply rate limiting
        3. Retry failed calls with exponential backoff
        4. Return None for failed calls (graceful degradation)
        5. Log all API calls in JSON format
        6. Calculate success_rate metric

        Args:
            topics: List of topics/keywords to collect data for
                   (e.g., subreddit names, channel IDs, search terms)

        Returns:
            CollectionResult with collected data and metrics

        Raises:
            Should NOT raise exceptions - handle internally and return
            failed results in CollectionResult.errors
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if API is accessible and credentials are valid.

        Returns:
            True if API is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def get_rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit status for this API.

        Returns:
            RateLimitInfo with current quota usage
        """
        pass
```

---

### Task 2: Create Rate Limiter Classes

**Acceptance Criteria:** AC #4 (RequestsPerMinuteRateLimiter and DailyQuotaRateLimiter)

**Subtasks:**
- [ ] Create `backend/app/collectors/rate_limiters.py` module
- [ ] Implement RequestsPerMinuteRateLimiter with sliding window
- [ ] Implement DailyQuotaRateLimiter with database tracking
- [ ] Add async context manager support
- [ ] Add unit tests

**Implementation Steps:**

1. **Create rate limiters module** (backend/app/collectors/rate_limiters.py):
```python
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

        async with limiter.consume(units=1):
            # Make API call that costs 1 unit
            response = await youtube.videos().list()
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
```

---

### Task 3: Create Retry Decorator with Exponential Backoff

**Acceptance Criteria:** AC #5 (retry_with_backoff decorator with 2s, 4s, 8s backoff)

**Subtasks:**
- [ ] Create `backend/app/collectors/retry.py` module
- [ ] Implement retry_with_backoff decorator
- [ ] Support configurable max_attempts and backoff_base
- [ ] Log all retry attempts
- [ ] Add unit tests for retry behavior

**Implementation Steps:**

1. **Create retry module** (backend/app/collectors/retry.py):
```python
"""Retry decorator with exponential backoff for API calls."""
import asyncio
import logging
from functools import wraps
from typing import Optional, Type, Tuple, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    backoff_base: int = 2,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """Decorator for retrying async functions with exponential backoff.

    Implements exponential backoff: 2s, 4s, 8s for default settings.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        backoff_base: Base for exponential backoff in seconds (default: 2)
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated async function with retry logic

    Example:
        @retry_with_backoff(max_attempts=3, backoff_base=2)
        async def fetch_reddit_data(topic: str):
            response = await reddit.get(topic)
            return response

    Backoff Formula:
        delay = backoff_base ^ attempt_number
        attempt 1: 2^1 = 2 seconds
        attempt 2: 2^2 = 4 seconds
        attempt 3: 2^3 = 8 seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    start_time = datetime.utcnow()
                    result = await func(*args, **kwargs)
                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                    # Log successful call
                    logger.info(
                        "API call succeeded",
                        extra={
                            "event": "api_call",
                            "function": func.__name__,
                            "attempt": attempt,
                            "success": True,
                            "duration_ms": duration_ms
                        }
                    )

                    return result

                except exceptions as e:
                    last_exception = e
                    duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                    # Log failed attempt
                    logger.warning(
                        f"API call failed (attempt {attempt}/{max_attempts}): {str(e)}",
                        extra={
                            "event": "api_call",
                            "function": func.__name__,
                            "attempt": attempt,
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "duration_ms": duration_ms
                        }
                    )

                    # Don't sleep on last attempt
                    if attempt < max_attempts:
                        backoff_seconds = backoff_base ** attempt
                        logger.info(f"Retrying in {backoff_seconds}s...")
                        await asyncio.sleep(backoff_seconds)

            # All attempts failed - log final failure
            logger.error(
                f"API call failed after {max_attempts} attempts",
                extra={
                    "event": "api_call_exhausted",
                    "function": func.__name__,
                    "max_attempts": max_attempts,
                    "final_error": str(last_exception)
                }
            )

            # Return None for graceful degradation
            return None

        return wrapper
    return decorator
```

---

### Task 4: Create Collection Orchestrator

**Acceptance Criteria:** AC #2, #3 (CollectionOrchestrator with asyncio.gather)

**Subtasks:**
- [ ] Create `backend/app/collectors/orchestrator.py` module
- [ ] Implement collect_all() with parallel execution
- [ ] Add graceful degradation for individual failures
- [ ] Track collection metrics
- [ ] Add structured logging

**Implementation Steps:**

1. **Create orchestrator module** (backend/app/collectors/orchestrator.py):
```python
"""Collection orchestrator for parallel multi-source data collection."""
import asyncio
import logging
from typing import List, Dict
from datetime import datetime
from uuid import UUID

from app.collectors.base import DataCollector, CollectionResult
from app.models.data_collection import DataCollection
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CollectionOrchestrator:
    """Orchestrates parallel data collection from multiple API sources.

    Coordinates multiple DataCollector instances to run in parallel using
    asyncio.gather(), tracking metrics and handling failures gracefully.

    Example:
        orchestrator = CollectionOrchestrator(
            collectors=[reddit_collector, youtube_collector],
            db_session=db
        )

        results = await orchestrator.collect_all(topics=["trending", "viral"])
        # Returns: {"reddit": CollectionResult(...), "youtube": CollectionResult(...)}
    """

    def __init__(
        self,
        collectors: List[DataCollector],
        db_session: AsyncSession
    ):
        """Initialize orchestrator with collectors.

        Args:
            collectors: List of DataCollector instances to coordinate
            db_session: Database session for tracking collection runs
        """
        self.collectors = collectors
        self.db_session = db_session

    async def collect_all(
        self,
        topics: List[str],
        collection_id: UUID
    ) -> Dict[str, CollectionResult]:
        """Collect data from all collectors in parallel.

        Uses asyncio.gather() with return_exceptions=True to ensure one
        collector's failure doesn't crash the entire collection.

        Args:
            topics: List of topics/keywords to collect
            collection_id: UUID of DataCollection record tracking this run

        Returns:
            Dictionary mapping collector name to CollectionResult

        Example:
            {
                "reddit": CollectionResult(source="reddit", data=[...], success_rate=0.95),
                "youtube": CollectionResult(source="youtube", data=[...], success_rate=1.0),
                "google_trends": CollectionResult(source="google_trends", data=[], success_rate=0.0)  # Failed
            }
        """
        start_time = datetime.utcnow()

        logger.info(
            f"Starting parallel collection with {len(self.collectors)} collectors",
            extra={
                "event": "collection_start",
                "collection_id": str(collection_id),
                "num_collectors": len(self.collectors),
                "num_topics": len(topics)
            }
        )

        # Create tasks for parallel execution
        tasks = [
            collector.collect(topics)
            for collector in self.collectors
        ]

        # Run all collectors in parallel with exception handling
        results_or_exceptions = await asyncio.gather(
            *tasks,
            return_exceptions=True  # Don't let one failure crash others
        )

        # Process results
        results = {}
        total_trends_found = 0
        failed_collectors = []

        for collector, result_or_exception in zip(self.collectors, results_or_exceptions):
            if isinstance(result_or_exception, Exception):
                # Collector raised unhandled exception
                logger.error(
                    f"Collector {collector.name} crashed: {str(result_or_exception)}",
                    extra={
                        "event": "collector_crash",
                        "collector": collector.name,
                        "error": str(result_or_exception),
                        "error_type": type(result_or_exception).__name__
                    }
                )

                # Create failed result for graceful degradation
                results[collector.name] = CollectionResult(
                    source=collector.name,
                    data=[],
                    success_rate=0.0,
                    total_calls=len(topics),
                    successful_calls=0,
                    failed_calls=len(topics),
                    errors=[str(result_or_exception)]
                )
                failed_collectors.append(collector.name)

            elif isinstance(result_or_exception, CollectionResult):
                # Collector completed successfully (may have partial failures)
                result = result_or_exception
                results[collector.name] = result

                # Count non-None data points
                trends_found = len([d for d in result.data if d is not None])
                total_trends_found += trends_found

                if result.success_rate < 1.0:
                    logger.warning(
                        f"Collector {collector.name} had partial failures: {result.success_rate:.1%} success rate",
                        extra={
                            "event": "partial_collection_failure",
                            "collector": collector.name,
                            "success_rate": result.success_rate,
                            "successful_calls": result.successful_calls,
                            "failed_calls": result.failed_calls
                        }
                    )

        # Calculate overall metrics
        duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        duration_minutes = duration_seconds / 60

        # Calculate API-specific metrics for database
        reddit_calls = results.get("reddit", CollectionResult("reddit", [], 0.0)).total_calls
        youtube_quota = results.get("youtube", CollectionResult("youtube", [], 0.0)).total_calls  # 1 unit per call
        google_trends_calls = results.get("google_trends", CollectionResult("google_trends", [], 0.0)).total_calls

        logger.info(
            f"Collection complete: {total_trends_found} trends found in {duration_minutes:.1f} minutes",
            extra={
                "event": "collection_complete",
                "collection_id": str(collection_id),
                "duration_minutes": duration_minutes,
                "trends_found": total_trends_found,
                "failed_collectors": failed_collectors,
                "reddit_api_calls": reddit_calls,
                "youtube_api_quota_used": youtube_quota,
                "google_trends_api_calls": google_trends_calls
            }
        )

        return results
```

---

### Task 5: Configure Structured JSON Logging

**Acceptance Criteria:** AC #9 (Structured JSON logging for all API calls)

**Subtasks:**
- [ ] Configure Python logging with JSON formatter
- [ ] Update main.py to initialize logging on startup
- [ ] Add log filters for sensitive data
- [ ] Configure log levels per environment

**Implementation Steps:**

1. **Create logging configuration** (backend/app/core/logging_config.py):
```python
"""Structured JSON logging configuration."""
import logging
import json
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: LogRecord to format

        Returns:
            JSON string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "event"):
            log_data["event"] = record.event

        if hasattr(record, "api"):
            log_data["api"] = record.api

        if hasattr(record, "success"):
            log_data["success"] = record.success

        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if hasattr(record, "error"):
            log_data["error"] = record.error

        # Add any other extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName",
                          "levelname", "levelno", "lineno", "module", "msecs",
                          "pathname", "process", "processName", "relativeCreated",
                          "thread", "threadName", "exc_info", "exc_text", "stack_info",
                          "event", "api", "success", "duration_ms", "error"]:
                log_data[key] = value

        return json.dumps(log_data)


def setup_logging(debug: bool = False):
    """Configure structured JSON logging for the application.

    Args:
        debug: If True, set log level to DEBUG. Otherwise INFO.
    """
    # Create JSON formatter
    formatter = JSONFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
```

2. **Update main.py to initialize logging** (backend/app/main.py):
```python
# Add at top of file after imports
from app.core.logging_config import setup_logging

# In lifespan function, add after database setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan event handler for startup/shutdown tasks."""
    # Startup
    print("=" * 50)
    print("FastAPI: Starting up trend-monitor API")

    # Initialize structured logging
    setup_logging(debug=settings.debug)
    logger = logging.getLogger(__name__)
    logger.info("Structured JSON logging initialized")

    # ... rest of startup
    yield
    # Shutdown
    await close_db()
```

---

## Architecture Compliance

### API Integration Architecture (AD-5)

✅ **Modular DataCollector Pattern**
- Abstract base class with standardized interface
- Factory-ready for instantiating specific collectors
- Dependency injection for database and configuration

✅ **Async/Parallel Execution**
- Python asyncio for concurrent API calls
- `asyncio.gather()` with return_exceptions=True
- Async context managers for rate limiters

✅ **Rate Limiting**
- RequestsPerMinuteRateLimiter: Sliding window algorithm
- DailyQuotaRateLimiter: Database-persisted quota tracking
- Per-API customization (Reddit 60/min, YouTube 10K/day)

✅ **Retry Logic**
- Exponential backoff: 2s → 4s → 8s
- Maximum 3 retry attempts
- Decorator pattern for reusability
- Preserves exception context

✅ **Graceful Degradation**
- Individual failures return None
- Collection continues despite failures
- Success rate metrics tracked
- Detailed error logging

### Observability (AD-10)

✅ **Structured JSON Logging**
- All API calls logged with: event, api, success, duration_ms
- Error logs include: error_type, error_message, retry_attempt
- Collection metrics: duration, trends_found, API failures

✅ **Quota Tracking**
- Database-persisted daily quota usage
- Warning logs at 80% threshold
- Per-API quota monitoring

---

## Library & Framework Requirements

### Required Packages

Add to `backend/requirements.txt`:
```
# Already installed from Epic 1
fastapi==0.104.1
sqlalchemy==2.0.23
asyncpg==0.29.0
pydantic==2.5.0
pydantic-settings==2.1.0

# New for Epic 2
# (API-specific libraries will be added in Stories 2.2-2.5)
```

### Why These Versions?

- **Python 3.10+**: Native async/await support, type hints
- **asyncio** (built-in): Parallel API collection
- **dataclasses** (built-in): Clean data structures (CollectionResult, RateLimitInfo)
- **SQLAlchemy 2.0.23**: Already installed, used for quota tracking

---

## File Structure Requirements

### Backend Directory Structure (After This Story)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app (update logging init)
│   ├── config.py                    # Settings (from Story 1.1)
│   ├── database.py                  # Database session (from Story 1.2)
│   ├── collectors/                  # NEW: Data collection infrastructure
│   │   ├── __init__.py              # Exports: DataCollector, CollectionOrchestrator
│   │   ├── base.py                  # DataCollector ABC, CollectionResult, RateLimitInfo
│   │   ├── orchestrator.py          # CollectionOrchestrator
│   │   ├── rate_limiters.py         # RequestsPerMinuteRateLimiter, DailyQuotaRateLimiter
│   │   └── retry.py                 # retry_with_backoff decorator
│   ├── core/                        # Existing from Story 1.3
│   │   ├── __init__.py
│   │   ├── security.py              # JWT functions
│   │   └── logging_config.py        # NEW: JSON logging setup
│   ├── models/                      # Existing from Story 1.2
│   │   ├── base.py
│   │   ├── trend.py
│   │   ├── data_collection.py
│   │   ├── user.py
│   │   └── api_quota_usage.py
│   ├── api/                         # Existing from Story 1.3
│   │   ├── auth.py
│   │   └── admin.py
│   └── schemas/                     # Existing from Story 1.3
│       └── auth.py
├── tests/                           # Existing from Story 1.2
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_collectors/             # NEW: Collector tests
│   │   ├── __init__.py
│   │   ├── test_base.py
│   │   ├── test_rate_limiters.py
│   │   └── test_retry.py
│   └── test_api/
│       └── test_auth.py
└── requirements.txt                 # No changes needed (dependencies in Stories 2.2-2.5)
```

---

## Testing Requirements

### Unit Tests to Create

1. **Test DataCollector ABC** (backend/tests/test_collectors/test_base.py):
```python
import pytest
from app.collectors.base import DataCollector, CollectionResult

def test_collection_result_success_rate_calculation():
    """Test that success_rate is calculated correctly."""
    result = CollectionResult(
        source="test",
        data=[{"id": 1}, None, {"id": 2}],
        success_rate=0.0,  # Will be calculated
        total_calls=3,
        successful_calls=2,
        failed_calls=1
    )

    assert result.success_rate == pytest.approx(0.666, rel=0.01)

def test_collection_result_errors_list_initialized():
    """Test that errors list is initialized if None."""
    result = CollectionResult(
        source="test",
        data=[],
        success_rate=0.0,
        total_calls=0
    )

    assert result.errors == []
```

2. **Test RequestsPerMinuteRateLimiter** (backend/tests/test_collectors/test_rate_limiters.py):
```python
import pytest
import asyncio
from datetime import datetime, timedelta
from app.collectors.rate_limiters import RequestsPerMinuteRateLimiter

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
```

3. **Test retry_with_backoff** (backend/tests/test_collectors/test_retry.py):
```python
import pytest
from unittest.mock import AsyncMock, call
from app.collectors.retry import retry_with_backoff

@pytest.mark.asyncio
async def test_retry_succeeds_on_first_attempt():
    """Test that retry succeeds immediately if no exception."""
    mock_func = AsyncMock(return_value="success")

    @retry_with_backoff(max_attempts=3)
    async def test_func():
        return await mock_func()

    result = await test_func()

    assert result == "success"
    assert mock_func.call_count == 1

@pytest.mark.asyncio
async def test_retry_retries_on_failure():
    """Test that retry attempts exponential backoff."""
    mock_func = AsyncMock(side_effect=[
        Exception("Fail 1"),
        Exception("Fail 2"),
        "success"
    ])

    @retry_with_backoff(max_attempts=3, backoff_base=0.1)  # Fast backoff for testing
    async def test_func():
        result = await mock_func()
        if isinstance(result, Exception):
            raise result
        return result

    result = await test_func()

    assert result == "success"
    assert mock_func.call_count == 3
```

---

## Previous Story Intelligence

### Key Learnings from Story 1.4 (Frontend Setup)

**Successfully Implemented:**
1. ✅ Next.js 14 with App Router pattern established
2. ✅ TypeScript with strict mode configuration
3. ✅ Environment variables via process.env.NEXT_PUBLIC_*
4. ✅ API client pattern in lib/api.ts with fetch()
5. ✅ JWT tokens stored in localStorage
6. ✅ Custom error classes (APIError) for type-safe error handling

**Code Patterns to Follow:**
- Module exports via `__init__.py` with `__all__` list
- Type hints for all function signatures
- Async/await for all I/O operations
- Dataclasses for structured data (@dataclass decorator)
- Environment variables via settings.* (never hardcoded)

**Files Created:**
- Organized by feature/concern (api/, models/, core/, collectors/)
- Test files mirror source structure (tests/test_collectors/)

---

## Git Intelligence Summary

**Recent Commits Relevant to This Story:**

1. `b4c5a1b` - chore: Mark Story 1.2 and Epic 1 as complete
   - Epic 1 fully complete, starting fresh with Epic 2
   - Database schema ready for data collection

2. `1ddfbed` - fix: Code review fixes for Story 1.2
   - Comprehensive database tests added (pattern to follow)
   - Pytest fixtures with async_session (reuse for collector tests)
   - Naming conventions established (ck_trends_* for check constraints)

3. `218659d` - Complete Story 1.4: Frontend Setup with Login UI
   - Frontend deployment patterns established
   - Environment variable management pattern

4. `db178ea` - Complete Story 1.2: Database Schema Creation
   - DataCollection model ready (id, started_at, status, api_calls columns)
   - ApiQuotaUsage model ready (api_name, date, units_used)
   - Database session available via `get_db()` dependency

**Code Patterns Established:**
- Import pattern: `from app.models import Model` (not relative imports)
- Config access: `settings.database_url`, `settings.debug`
- Async patterns: `async def` with `await`, `AsyncSession`
- Error handling: try/except with specific exceptions, never bare except
- Logging: `logger.info()` with structured extra fields

---

## Latest Technical Information (Web Research)

### Python Asyncio Best Practices (2026)

**Async Context Managers:**
- Use `async with` for resource management (rate limiters, database sessions)
- Implement `__aenter__` and `__aexit__` for cleanup
- Ensures proper resource release even on exceptions

**asyncio.gather() for Parallel Execution:**
- Use `return_exceptions=True` to prevent one failure from cancelling others
- Returns list of results or exceptions in same order as tasks
- Ideal for independent parallel API calls

**Exponential Backoff Algorithm:**
- Standard formula: `delay = base ^ attempt_number`
- Common base values: 2 (aggressive), 1.5 (moderate)
- Maximum delay cap recommended (e.g., 60 seconds) for production

**Sliding Window Rate Limiting:**
- More accurate than fixed window (avoids burst at window boundaries)
- Track individual request timestamps in deque
- Clean up expired requests before checking limit

**Database-Backed Quota Tracking:**
- Use UPSERT for thread-safe increment: `ON CONFLICT DO UPDATE`
- Track daily quotas with `(api_name, date)` composite key
- Query current usage before making API calls

### Structured Logging Best Practices (2026)

**JSON Format Benefits:**
- Machine-readable for log aggregation tools (Datadog, ELK stack)
- Structured fields enable filtering and analysis
- Consistent schema across microservices

**Required Fields:**
- timestamp (ISO 8601 format with Z suffix)
- level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- event (e.g., "api_call", "collection_start")
- message (human-readable description)

**API Call Logging:**
- Always log: api name, success boolean, duration_ms
- On failure: error_type, error_message, retry_attempt
- On success: data_points_collected, quota_used

---

## Project Context Reference

**Project:** trend-monitor
**Project Type:** Quantified trend monitoring system with multi-API data collection
**User:** dave (content planning lead, non-technical)
**Goal:** Enable data-driven content planning decisions by detecting cross-platform trend momentum

**This Story's Role:**
- First story in Epic 2 - establishes data collection foundation
- Creates reusable infrastructure for 4 API collectors (Stories 2.2-2.5)
- Implements core patterns: async/parallel, rate limiting, retry, graceful degradation
- Sets up structured logging for observability

**Success Criteria:**
- DataCollector ABC allows easy addition of new collectors
- Rate limiters prevent API quota overages
- Retry logic handles transient failures automatically
- Graceful degradation ensures partial data is better than no data
- Structured logs enable debugging and monitoring

---

## Definition of Done

This story is **DONE** when:

1. ✅ DataCollector abstract base class created with required methods
2. ✅ CollectionResult and RateLimitInfo dataclasses defined
3. ✅ RequestsPerMinuteRateLimiter implemented with sliding window
4. ✅ DailyQuotaRateLimiter implemented with database persistence
5. ✅ retry_with_backoff decorator created with exponential backoff (2s, 4s, 8s)
6. ✅ CollectionOrchestrator created with asyncio.gather()
7. ✅ Graceful degradation implemented (None for failed calls)
8. ✅ Structured JSON logging configured with JSONFormatter
9. ✅ main.py updated to initialize logging on startup
10. ✅ All unit tests passing (test_base, test_rate_limiters, test_retry)
11. ✅ Code follows established patterns from Epic 1
12. ✅ Type hints on all functions
13. ✅ Comprehensive docstrings on all classes and methods
14. ✅ No security vulnerabilities (API keys via environment, no secrets in logs)
15. ✅ Story documentation updated with actual implementation details

---

## Dev Agent Record

### Agent Model Used

**Claude Sonnet 4.5** (claude-sonnet-4-5-20250929)

### Completion Notes

**Implementation Summary:**
(To be filled in by dev agent after implementation)

### Files Created/Modified

**Files Created:**
(To be filled in by dev agent after implementation)

**Files Modified:**
(To be filled in by dev agent after implementation)

---

**Story Status:** ✅ Ready for Development
**Last Updated:** 2026-01-09

**Next Steps:**
1. Run `dev-story 2-1-api-collector-infrastructure` to implement
2. Stories 2.2-2.5 can then implement specific API collectors using this infrastructure
3. Story 2.6 can integrate CollectionOrchestrator into POST /collect endpoint
