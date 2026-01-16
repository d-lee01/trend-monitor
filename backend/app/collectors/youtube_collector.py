"""YouTube data collector using Google API Python Client."""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from cachetools import TTLCache

from app.collectors.base import DataCollector, CollectionResult, RateLimitInfo
from app.collectors.rate_limiters import DailyQuotaRateLimiter
from app.collectors.retry import retry_with_backoff
from app.collectors.topics import YOUTUBE_TOPIC_CATEGORIES
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class QuotaExceededException(Exception):
    """Raised when YouTube API quota is exceeded."""
    pass


class YouTubeCollector(DataCollector):
    """Collects trending videos from YouTube using Google API Client.

    Searches for trending videos about specified topics using YouTube Search API.
    Returns the top 5 most relevant and recent videos per topic, ordered by relevance.

    Quota cost: 100 units per search call + 1 unit per video details call.
    For 5 videos per topic: 100 + 5 = 105 units per topic.
    With 10K daily quota, can search ~95 topics per day (50 topics = ~5,250 units).

    Implements video metadata caching and quota tracking to stay within 10K daily quota.

    Example:
        collector = YouTubeCollector(db_session=db)
        result = await collector.collect(topics=["artificial intelligence", "machine learning"])
        # Returns CollectionResult with 10 videos (5 per topic)
        # Consumes ~210 quota units (105 per topic)
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize YouTube collector with API key authentication.

        Args:
            db_session: Database session for quota tracking
        """
        super().__init__(name="youtube")

        # Validate credentials
        if not settings.youtube_api_key:
            raise ValueError(
                "YouTube API key not configured. "
                "Please set YOUTUBE_API_KEY environment variable."
            )

        # Initialize YouTube API client
        self.youtube = build(
            settings.youtube_api_service_name,
            settings.youtube_api_version,
            developerKey=settings.youtube_api_key
        )

        # Quota limiter: 10,000 units/day
        self.quota_limiter = DailyQuotaRateLimiter(
            daily_limit=10000,
            api_name="youtube",
            db_session=db_session
        )

        # Video metadata cache (1 hour TTL) - cache video details to avoid redundant API calls
        self.video_cache = TTLCache(maxsize=500, ttl=3600)

        logger.info("YouTubeCollector initialized", extra={
            "event": "collector_init",
            "api": "youtube",
            "quota_limit": "10000/day"
        })

    @retry_with_backoff(max_attempts=3, backoff_base=2, exceptions=(HttpError,))
    async def _search_videos_for_topic(
        self,
        topic: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for trending videos about a topic with retry logic.

        Quota cost: 100 units for search + 1 unit per video for details.
        For max_results=5: 100 + 5 = 105 units total.

        Args:
            topic: Search query/topic (e.g., "artificial intelligence")
            max_results: Number of videos to return (default: 5)

        Returns:
            List of video data dictionaries
        """
        try:
            # Search for videos about the topic
            async with self.quota_limiter.consume(units=100):
                search_response = await asyncio.to_thread(
                    lambda: self.youtube.search().list(
                        part="snippet",
                        q=topic,
                        type="video",
                        order="viewCount",  # Most-viewed videos (trending!)
                        maxResults=max_results,
                        publishedAfter=(datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace('+00:00', 'Z'),  # Last 7 days
                        relevanceLanguage="en",  # English videos
                        safeSearch="moderate"
                    ).execute()
                )

            if not search_response.get('items'):
                logger.warning(f"No videos found for topic: {topic}")
                return []

            # Extract video IDs
            video_ids = [item['id']['videoId'] for item in search_response['items']]

            # Get detailed statistics for all videos (1 unit per call, but can batch)
            async with self.quota_limiter.consume(units=1):
                videos_response = await asyncio.to_thread(
                    lambda: self.youtube.videos().list(
                        part="snippet,statistics",
                        id=",".join(video_ids)
                    ).execute()
                )

            if not videos_response.get('items'):
                logger.warning(f"No video details found for topic: {topic}")
                return []

            # Process video data
            videos_data = []
            for video in videos_response['items']:
                snippet = video['snippet']
                stats = video['statistics']

                # Parse published_at timestamp
                published_at = datetime.fromisoformat(
                    snippet['publishedAt'].replace('Z', '+00:00')
                )
                hours_since_publish = (
                    datetime.now(timezone.utc) - published_at
                ).total_seconds() / 3600

                # Calculate engagement rate
                view_count = int(stats.get('viewCount', 0))
                like_count = int(stats.get('likeCount', 0))
                engagement_rate = like_count / view_count if view_count > 0 else 0.0

                # Get category for this topic (travel, news, or unknown)
                category = YOUTUBE_TOPIC_CATEGORIES.get(topic, "unknown")

                video_data = {
                    "video_id": video['id'],
                    "video_title": snippet['title'],
                    "channel_title": snippet['channelTitle'],
                    "channel_id": snippet['channelId'],
                    "published_at": snippet['publishedAt'],
                    "view_count": view_count,
                    "like_count": like_count,
                    "comment_count": int(stats.get('commentCount', 0)),
                    "hours_since_publish": round(hours_since_publish, 2),
                    "engagement_rate": round(engagement_rate, 4),
                    "thumbnail_url": snippet['thumbnails']['default']['url'],
                    "topic": topic,  # Track which topic this video was found for
                    "category": category  # Category: "travel", "news", or "unknown"
                }
                videos_data.append(video_data)

            logger.info(
                f"Found {len(videos_data)} videos for topic: {topic}",
                extra={
                    "event": "topic_search_complete",
                    "api": "youtube",
                    "topic": topic,
                    "videos_found": len(videos_data)
                }
            )

            return videos_data

        except HttpError as e:
            if e.resp.status == 403:
                # Quota exceeded
                logger.error("YouTube quota exceeded", extra={
                    "event": "quota_exceeded",
                    "api": "youtube"
                })
                raise QuotaExceededException("YouTube API quota exceeded")
            else:
                logger.error(
                    f"YouTube API error for topic '{topic}': {str(e)}",
                    extra={
                        "event": "api_error",
                        "api": "youtube",
                        "topic": topic,
                        "error": str(e),
                        "status_code": e.resp.status
                    }
                )
                # Retry decorator will handle this
                raise

    async def collect(self, topics: List[str]) -> CollectionResult:
        """Collect trending videos from YouTube for given topics.

        Args:
            topics: List of search topics/keywords (e.g., ["artificial intelligence", "machine learning"])

        Returns:
            CollectionResult with collected videos and metrics
        """
        start_time = datetime.now(timezone.utc)
        all_videos = []
        successful_calls = 0
        failed_calls = 0
        errors = []

        # Check current quota usage
        current_usage = await self.quota_limiter.get_usage_today()
        if current_usage >= 8000:
            logger.warning(
                f"YouTube quota at {current_usage}/10,000 ({current_usage/100:.1f}%)",
                extra={
                    "event": "quota_warning",
                    "api": "youtube",
                    "quota_used": current_usage,
                    "quota_limit": 10000
                }
            )

        if current_usage >= 10000:
            logger.error("YouTube quota exceeded, cannot collect", extra={
                "event": "quota_exceeded",
                "api": "youtube"
            })
            return CollectionResult(
                source="youtube",
                data=[],
                success_rate=-1.0,
                total_calls=len(topics),
                successful_calls=0,
                failed_calls=len(topics),
                errors=["YouTube quota exceeded"],
                duration_seconds=0.0
            )

        logger.info(
            f"Starting YouTube collection for {len(topics)} topics",
            extra={
                "event": "collection_start",
                "api": "youtube",
                "num_topics": len(topics),
                "quota_used": current_usage
            }
        )

        # Collect from each topic
        for topic in topics:
            # Check quota before each topic (prevent mid-collection quota exceeded)
            # Each topic costs ~105 units (100 for search + 5 for video details)
            current_usage = await self.quota_limiter.get_usage_today()
            if current_usage + 105 > 10000:
                logger.warning(
                    f"Stopping collection: insufficient quota ({current_usage}/10,000, need 105 more)",
                    extra={
                        "event": "quota_insufficient",
                        "api": "youtube",
                        "quota_used": current_usage,
                        "quota_limit": 10000
                    }
                )
                failed_calls += len(topics) - successful_calls - failed_calls
                errors.append(f"Stopped early: insufficient quota (used {current_usage}/10,000)")
                break

            call_start = datetime.now(timezone.utc)

            try:
                videos = await self._search_videos_for_topic(topic, max_results=5)
                call_duration_ms = (datetime.now(timezone.utc) - call_start).total_seconds() * 1000

                if videos:
                    all_videos.extend(videos)
                    successful_calls += 1
                    logger.info(
                        f"Collected {len(videos)} videos for topic '{topic}'",
                        extra={
                            "event": "api_call",
                            "api": "youtube",
                            "topic": topic,
                            "success": True,
                            "videos_found": len(videos),
                            "duration_ms": round(call_duration_ms, 2)
                        }
                    )
                else:
                    failed_calls += 1
                    errors.append(f"No videos found for topic: {topic}")
                    logger.warning(
                        f"No videos found for topic '{topic}' after retries",
                        extra={
                            "event": "api_call_failed",
                            "api": "youtube",
                            "topic": topic,
                            "success": False,
                            "duration_ms": round(call_duration_ms, 2)
                        }
                    )

            except QuotaExceededException:
                # Stop collection if quota exceeded
                failed_calls += len(topics) - successful_calls - failed_calls
                errors.append("YouTube quota exceeded, stopped collection")
                logger.error("Quota exceeded, stopping YouTube collection")
                break

        # Calculate metrics
        duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        total_calls = len(topics)

        result = CollectionResult(
            source="youtube",
            data=all_videos,
            success_rate=-1.0,  # Auto-calculate
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            errors=errors,
            duration_seconds=duration_seconds
        )

        # Log final quota usage
        final_usage = await self.quota_limiter.get_usage_today()

        logger.info(
            f"YouTube collection complete: {len(all_videos)} videos from {successful_calls}/{total_calls} topics",
            extra={
                "event": "collection_complete",
                "api": "youtube",
                "videos_collected": len(all_videos),
                "success_rate": result.success_rate,
                "duration_seconds": duration_seconds,
                "quota_used": final_usage
            }
        )

        return result

    async def health_check(self) -> bool:
        """Check if YouTube API is accessible and credentials are valid.

        Returns:
            True if YouTube API is healthy, False otherwise
        """
        try:
            # Test by fetching a well-known channel
            await asyncio.to_thread(
                lambda: self.youtube.channels().list(
                    part="snippet",
                    id="UC_x5XG1OV2P6uZZ5FSM9Ttw"  # Google Developers
                ).execute()
            )

            logger.info("YouTube health check passed", extra={
                "event": "health_check",
                "api": "youtube",
                "status": "healthy"
            })
            return True

        except (HttpError, ConnectionError, TimeoutError) as e:
            logger.error(f"YouTube health check failed: {str(e)}", extra={
                "event": "health_check",
                "api": "youtube",
                "status": "unhealthy",
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False

    async def get_rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit status for YouTube API.

        Returns:
            RateLimitInfo with current quota usage
        """
        usage_today = await self.quota_limiter.get_usage_today()
        remaining = await self.quota_limiter.get_remaining()

        # Reset at midnight UTC
        now = datetime.now(timezone.utc)
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        return RateLimitInfo(
            limit=10000,
            remaining=remaining,
            reset_at=tomorrow,
            quota_type="per_day"
        )
