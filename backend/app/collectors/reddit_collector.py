"""Reddit data collector using PRAW library."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import praw
from praw.exceptions import PRAWException

from app.collectors.base import DataCollector, CollectionResult, RateLimitInfo
from app.collectors.rate_limiters import RequestsPerMinuteRateLimiter
from app.collectors.retry import retry_with_backoff
from app.config import settings

logger = logging.getLogger(__name__)

# Default subreddits to monitor
DEFAULT_SUBREDDITS = [
    "all",
    "popular",
    "videos",
    "movies",
    "television",
    "music",
    "news",
    "technology",
    "gaming",
    "sports"
]


class RedditCollector(DataCollector):
    """Collects trending posts from Reddit using PRAW.

    Monitors 10 default subreddits, collecting top 5 "hot" posts from each.
    Respects 60 requests/minute rate limit using RequestsPerMinuteRateLimiter.
    Retries failed requests with exponential backoff.

    Example:
        collector = RedditCollector()
        result = await collector.collect(topics=DEFAULT_SUBREDDITS)
        # Returns CollectionResult with 50 posts (10 subreddits × 5 posts)
    """

    def __init__(self):
        """Initialize Reddit collector with OAuth authentication."""
        super().__init__(name="reddit")

        # Validate credentials
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            raise ValueError(
                "Reddit API credentials not configured. "
                "Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."
            )

        # Initialize praw client
        self.reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent
        )

        # Read-only mode (no posting/voting)
        self.reddit.read_only = True

        # Rate limiter: 60 requests/minute
        self.rate_limiter = RequestsPerMinuteRateLimiter(limit=60, window_seconds=60)

        logger.info("RedditCollector initialized", extra={
            "event": "collector_init",
            "api": "reddit",
            "rate_limit": "60/min"
        })

    @retry_with_backoff(max_attempts=3, backoff_base=2, exceptions=(PRAWException,))
    async def _fetch_subreddit_posts(
        self,
        subreddit_name: str,
        limit: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch hot posts from a subreddit with retry logic.

        Args:
            subreddit_name: Subreddit name (e.g., "all", "videos")
            limit: Number of posts to fetch (default: 5)

        Returns:
            List of post data dictionaries, or None if failed after retries
        """
        try:
            async with self.rate_limiter:
                # Run synchronous praw call in thread pool
                subreddit = await asyncio.to_thread(
                    self.reddit.subreddit,
                    subreddit_name
                )

                # Get hot posts (currently trending)
                hot_posts = await asyncio.to_thread(
                    lambda: list(subreddit.hot(limit=limit))
                )

                # Extract metrics from each post
                posts_data = []
                for post in hot_posts:
                    # Calculate hours since post
                    created_time = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                    hours_since_post = (datetime.now(timezone.utc) - created_time).total_seconds() / 3600

                    post_data = {
                        "title": post.title,
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "upvote_ratio": post.upvote_ratio,
                        "created_utc": post.created_utc,
                        "subreddit_name": post.subreddit.display_name,
                        "subreddit_subscribers": post.subreddit.subscribers,
                        "num_crossposts": post.num_crossposts,
                        "permalink": post.permalink,
                        "hours_since_post": round(hours_since_post, 2),
                        "url": post.url,
                        "post_id": post.id
                    }
                    posts_data.append(post_data)

                return posts_data

        except PRAWException as e:
            logger.error(
                f"Reddit API error for r/{subreddit_name}: {str(e)}",
                extra={
                    "event": "api_error",
                    "api": "reddit",
                    "subreddit": subreddit_name,
                    "error": str(e)
                }
            )
            # Retry decorator will handle this
            raise

    async def collect(self, topics: List[str]) -> CollectionResult:
        """Collect trending posts from Reddit for given subreddits.

        Args:
            topics: List of subreddit names (e.g., ["all", "videos", "gaming"])

        Returns:
            CollectionResult with collected posts and metrics
        """
        start_time = datetime.now(timezone.utc)
        all_posts = []
        successful_calls = 0
        failed_calls = 0
        errors = []

        logger.info(
            f"Starting Reddit collection for {len(topics)} subreddits",
            extra={
                "event": "collection_start",
                "api": "reddit",
                "num_topics": len(topics)
            }
        )

        # Collect from each subreddit
        for subreddit_name in topics:
            call_start = datetime.now(timezone.utc)
            posts = await self._fetch_subreddit_posts(subreddit_name, limit=5)
            call_duration_ms = (datetime.now(timezone.utc) - call_start).total_seconds() * 1000

            if posts is not None:
                all_posts.extend(posts)
                successful_calls += 1
                logger.info(
                    f"Collected {len(posts)} posts from r/{subreddit_name}",
                    extra={
                        "event": "api_call",
                        "api": "reddit",
                        "topic": f"r/{subreddit_name}",
                        "success": True,
                        "posts_collected": len(posts),
                        "duration_ms": round(call_duration_ms, 2)
                    }
                )
            else:
                # Retry exhausted, continue with other subreddits
                failed_calls += 1
                errors.append(f"Failed to collect from r/{subreddit_name}")
                logger.warning(
                    f"Skipping r/{subreddit_name} after retries",
                    extra={
                        "event": "api_call_failed",
                        "api": "reddit",
                        "topic": f"r/{subreddit_name}",
                        "success": False,
                        "duration_ms": round(call_duration_ms, 2)
                    }
                )

        # Calculate metrics
        duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        total_calls = len(topics)

        result = CollectionResult(
            source="reddit",
            data=all_posts,  # List of post dictionaries
            success_rate=-1.0,  # Auto-calculate
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            errors=errors,
            duration_seconds=duration_seconds
        )

        logger.info(
            f"Reddit collection complete: {len(all_posts)} posts from {successful_calls}/{total_calls} subreddits",
            extra={
                "event": "collection_complete",
                "api": "reddit",
                "posts_collected": len(all_posts),
                "success_rate": result.success_rate,  # Auto-calculated
                "duration_seconds": duration_seconds
            }
        )

        return result

    async def health_check(self) -> bool:
        """Check if Reddit API is accessible and credentials are valid.

        Returns:
            True if Reddit API is healthy, False otherwise
        """
        try:
            # Test by fetching current user (authentication check)
            user = await asyncio.to_thread(lambda: self.reddit.user.me())

            # In read-only mode, user.me() returns None but doesn't raise
            # Try fetching a subreddit instead
            await asyncio.to_thread(self.reddit.subreddit, "all")

            logger.info("Reddit health check passed", extra={
                "event": "health_check",
                "api": "reddit",
                "status": "healthy"
            })
            return True

        except (PRAWException, ConnectionError, TimeoutError) as e:
            logger.error(f"Reddit health check failed: {str(e)}", extra={
                "event": "health_check",
                "api": "reddit",
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False

    async def get_rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit status for Reddit API.

        Returns:
            RateLimitInfo with current quota usage
        """
        remaining = self.rate_limiter.get_remaining()
        reset_at = datetime.now(timezone.utc) + timedelta(seconds=60)

        return RateLimitInfo(
            limit=60,
            remaining=remaining,
            reset_at=reset_at,
            quota_type="per_minute"
        )
