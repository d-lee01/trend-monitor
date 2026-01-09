"""Abstract base class for data collectors with standardized interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def __post_init__(self):
        """Initialize computed fields."""
        # Calculate success rate if not provided and we have calls
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
