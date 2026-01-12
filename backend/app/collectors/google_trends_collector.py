"""Google Trends data collector using PyTrends (unofficial API)."""
import asyncio
import logging
import statistics
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError, ResponseError

from app.collectors.base import DataCollector, CollectionResult, RateLimitInfo
from app.collectors.retry import retry_with_backoff
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Default topics to monitor
DEFAULT_TOPICS = [
    # Entertainment
    "Marvel", "Disney", "Netflix", "HBO", "Prime Video",

    # Technology
    "iPhone", "Android", "ChatGPT", "AI", "Cryptocurrency",

    # Gaming
    "PlayStation", "Xbox", "Nintendo", "Fortnite", "Minecraft",

    # Social Media
    "TikTok", "Instagram", "Twitter", "YouTube", "Threads",

    # Business/Finance
    "Stock Market", "Tesla", "Apple", "Microsoft", "Google",

    # News/Events
    "Olympics", "World Cup", "Elections", "Climate Change", "Space",

    # Health/Lifestyle
    "Fitness", "Nutrition", "Mental Health", "Meditation", "Yoga",

    # Pop Culture
    "Taylor Swift", "Beyonce", "NBA", "NFL", "Premier League",

    # Emerging Trends
    "Metaverse", "Web3", "Quantum Computing", "Green Energy", "EVs"
]


class GoogleTrendsCollector(DataCollector):
    """Collects search interest data from Google Trends using PyTrends.

    IMPORTANT: PyTrends is an unofficial API that web-scrapes Google Trends.
    It's subject to breaking changes if Google modifies their website.
    Implements 60-second delays and comprehensive error handling.

    Example:
        collector = GoogleTrendsCollector(db_session=db)
        result = await collector.collect(topics=DEFAULT_TOPICS)
        # Returns CollectionResult with 50 topics (7-day history each)
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize Google Trends collector.

        Args:
            db_session: Database session (not used for Google Trends, but required by interface)
        """
        super().__init__(name="google_trends")

        # Initialize PyTrends
        try:
            self.pytrend = TrendReq(
                hl='en-US',           # Language
                tz=360,               # Timezone offset (UTC-6)
                timeout=(10, 25),     # Connection and read timeouts
                retries=2,            # Built-in retries
                backoff_factor=0.1    # Exponential backoff
            )
            logger.info("PyTrends initialized successfully", extra={
                "event": "collector_init",
                "api": "google_trends",
                "rate_limit": "60s between requests"
            })
        except Exception as e:
            logger.error(f"Failed to initialize PyTrends: {e}", extra={
                "event": "collector_init_error",
                "api": "google_trends",
                "error": str(e)
            })
            raise ValueError(
                "Failed to initialize PyTrends. "
                "This may indicate a library compatibility issue."
            )

        # Track request timing for rate limiting
        self.last_request_time: Optional[datetime] = None

    def _calculate_spike_score(
        self,
        current_interest: int,
        seven_day_history: List[int]
    ) -> Tuple[float, bool]:
        """Calculate spike score using z-score.

        Args:
            current_interest: Today's interest (0-100)
            seven_day_history: Last 7 days including today

        Returns:
            (spike_score, spike_detected)
            spike_score: 0-100 normalized score
            spike_detected: True if z-score > 2.0
        """
        if len(seven_day_history) < 3:
            return (float(current_interest), False)

        mean = statistics.mean(seven_day_history)
        try:
            stddev = statistics.stdev(seven_day_history)
        except statistics.StatisticsError:
            # Insufficient variance
            return (float(current_interest), False)

        if stddev == 0:
            return (float(current_interest), False)

        z_score = (current_interest - mean) / stddev

        # Normalize to 0-100 scale
        normalized_score = min(100, max(0, (z_score + 3) / 6 * 100))

        # Spike if z-score > 2.0 (97.5th percentile)
        spike_detected = z_score > 2.0

        return (round(normalized_score, 2), spike_detected)

    @retry_with_backoff(
        max_attempts=2,
        backoff_base=2,
        exceptions=(TooManyRequestsError, ResponseError)
    )
    async def _fetch_topic_interest(
        self,
        topic: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch interest over time for a topic with retry logic.

        Args:
            topic: Search keyword/topic

        Returns:
            Topic data dictionary, or None if failed after retries
        """
        try:
            # Build payload (sync operation - use asyncio.to_thread)
            await asyncio.to_thread(
                lambda: self.pytrend.build_payload(
                    kw_list=[topic],
                    cat=0,                  # All categories
                    timeframe='now 7-d',    # Last 7 days
                    geo='',                 # Worldwide
                    gprop=''                # Google web search
                )
            )

            # Get interest over time
            df = await asyncio.to_thread(
                lambda: self.pytrend.interest_over_time()
            )

            # Check if data exists
            if df.empty:
                logger.warning(f"No interest data for topic: {topic}", extra={
                    "event": "no_data",
                    "api": "google_trends",
                    "topic": topic
                })
                return None

            # Handle case where topic not in columns
            if topic not in df.columns:
                logger.warning(f"Topic '{topic}' not in response columns", extra={
                    "event": "topic_missing",
                    "api": "google_trends",
                    "topic": topic,
                    "available_columns": list(df.columns)
                })
                return None

            # Extract interest data
            seven_day_history = df[topic].tolist()
            current_interest = seven_day_history[-1] if seven_day_history else 0

            # Calculate spike score
            spike_score, spike_detected = self._calculate_spike_score(
                int(current_interest),
                [int(x) for x in seven_day_history]
            )

            # Get related queries
            try:
                related_queries_raw = await asyncio.to_thread(
                    lambda: self.pytrend.related_queries()
                )
                related_queries = related_queries_raw.get(topic, {})
            except (TooManyRequestsError, ResponseError) as e:
                logger.warning(f"Failed to fetch related queries for {topic}: {e}")
                related_queries = {}

            topic_data = {
                "topic": topic,
                "current_interest": int(current_interest),
                "seven_day_history": [int(x) for x in seven_day_history],
                "average_interest": round(statistics.mean(seven_day_history), 2),
                "spike_score": spike_score,
                "spike_detected": spike_detected,
                "related_queries": related_queries,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            logger.debug(
                f"Fetched interest for topic '{topic}': {current_interest}",
                extra={
                    "event": "topic_fetch",
                    "api": "google_trends",
                    "topic": topic,
                    "current_interest": int(current_interest),
                    "spike_detected": spike_detected
                }
            )

            return topic_data

        except TooManyRequestsError:
            logger.error(
                f"Rate limit exceeded for topic '{topic}'",
                extra={
                    "event": "rate_limit_exceeded",
                    "api": "google_trends",
                    "topic": topic
                }
            )
            raise  # Let retry decorator handle
        except ResponseError as e:
            logger.error(
                f"Response error for topic '{topic}': {e}",
                extra={
                    "event": "response_error",
                    "api": "google_trends",
                    "topic": topic,
                    "error": str(e)
                }
            )
            raise  # Let retry decorator handle
        except Exception as e:
            logger.exception(
                f"Unexpected error for topic '{topic}': {e}",
                extra={
                    "event": "unexpected_error",
                    "api": "google_trends",
                    "topic": topic,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return None

    async def collect(self, topics: List[str]) -> CollectionResult:
        """Collect interest data from Google Trends for given topics.

        Args:
            topics: List of search keywords/topics

        Returns:
            CollectionResult with collected interest data and metrics
        """
        start_time = datetime.now(timezone.utc)
        all_data = []
        successful_calls = 0
        failed_calls = 0
        errors = []

        logger.info(
            f"Starting Google Trends collection for {len(topics)} topics",
            extra={
                "event": "collection_start",
                "api": "google_trends",
                "num_topics": len(topics),
                "estimated_duration_minutes": len(topics)  # ~1 min per topic
            }
        )

        # Collect from each topic
        for i, topic in enumerate(topics, 1):
            # Enforce 60-second delay between requests
            if self.last_request_time is not None:
                elapsed = (datetime.now(timezone.utc) - self.last_request_time).total_seconds()
                if elapsed < 60:
                    wait_time = 60 - elapsed
                    logger.info(
                        f"Rate limit: waiting {wait_time:.1f}s before next request",
                        extra={
                            "event": "rate_limit_wait",
                            "api": "google_trends",
                            "wait_seconds": round(wait_time, 1)
                        }
                    )
                    await asyncio.sleep(wait_time)

            call_start = datetime.now(timezone.utc)

            try:
                topic_data = await self._fetch_topic_interest(topic)
                call_duration_ms = (datetime.now(timezone.utc) - call_start).total_seconds() * 1000

                if topic_data is not None:
                    all_data.append(topic_data)
                    successful_calls += 1
                    logger.info(
                        f"Collected topic '{topic}' ({i}/{len(topics)})",
                        extra={
                            "event": "api_call",
                            "api": "google_trends",
                            "topic": topic,
                            "success": True,
                            "duration_ms": round(call_duration_ms, 2),
                            "progress": f"{i}/{len(topics)}"
                        }
                    )
                else:
                    failed_calls += 1
                    errors.append(f"Failed to collect topic: {topic}")
                    logger.warning(
                        f"Skipping topic '{topic}' after retries ({i}/{len(topics)})",
                        extra={
                            "event": "api_call_failed",
                            "api": "google_trends",
                            "topic": topic,
                            "success": False,
                            "duration_ms": round(call_duration_ms, 2),
                            "progress": f"{i}/{len(topics)}"
                        }
                    )

            except Exception as e:
                failed_calls += 1
                errors.append(f"Error collecting topic '{topic}': {str(e)}")
                logger.error(
                    f"Exception collecting topic '{topic}': {e}",
                    extra={
                        "event": "collection_error",
                        "api": "google_trends",
                        "topic": topic,
                        "error": str(e)
                    }
                )

            # Update last request time
            self.last_request_time = datetime.now(timezone.utc)

        # Calculate metrics
        duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        total_calls = len(topics)

        result = CollectionResult(
            source="google_trends",
            data=all_data,
            success_rate=-1.0,  # Auto-calculate
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            errors=errors,
            duration_seconds=duration_seconds
        )

        logger.info(
            f"Google Trends collection complete: {len(all_data)} topics from {successful_calls}/{total_calls} requests",
            extra={
                "event": "collection_complete",
                "api": "google_trends",
                "topics_collected": len(all_data),
                "success_rate": result.success_rate,
                "duration_seconds": round(duration_seconds, 2),
                "duration_minutes": round(duration_seconds / 60, 1)
            }
        )

        return result

    async def health_check(self) -> bool:
        """Check if Google Trends is accessible via PyTrends.

        Returns:
            True if Google Trends is healthy, False otherwise
        """
        try:
            # Test with a simple, reliable topic
            await asyncio.to_thread(
                lambda: self.pytrend.build_payload(
                    kw_list=['Python'],
                    timeframe='now 1-d'
                )
            )

            df = await asyncio.to_thread(
                lambda: self.pytrend.interest_over_time()
            )

            is_healthy = not df.empty

            logger.info(
                f"Google Trends health check {'passed' if is_healthy else 'failed'}",
                extra={
                    "event": "health_check",
                    "api": "google_trends",
                    "status": "healthy" if is_healthy else "unhealthy"
                }
            )

            return is_healthy

        except Exception as e:
            logger.error(
                f"Google Trends health check failed: {e}",
                extra={
                    "event": "health_check",
                    "api": "google_trends",
                    "status": "unhealthy",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return False

    async def get_rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit status for Google Trends.

        Google Trends has no official quota, just aggressive throttling.
        We enforce 60-second delays client-side.

        Returns:
            RateLimitInfo with timing information
        """
        # Calculate time until next request allowed
        if self.last_request_time is not None:
            elapsed = (datetime.now(timezone.utc) - self.last_request_time).total_seconds()
            remaining_wait = max(0, 60 - elapsed)
        else:
            remaining_wait = 0

        next_request_at = datetime.now(timezone.utc)
        if remaining_wait > 0:
            next_request_at = next_request_at + timedelta(seconds=remaining_wait)

        return RateLimitInfo(
            limit=60,  # 60 seconds per request
            remaining=0 if remaining_wait > 0 else 60,
            reset_at=next_request_at,
            quota_type="per_request"
        )
