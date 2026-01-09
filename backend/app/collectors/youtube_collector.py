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
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Default trending channels to monitor
DEFAULT_CHANNELS = [
    "UC-lHJZR3Gqxm24_Vd_AJ5Yw",  # PewDiePie
    "UCbCmjCuTUZos6Inko4u57UQ",  # Cocomelon
    "UCq-Fj5jknLsUf-MWSy4_brA",  # T-Series
    "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast
    "UCFFbwnve3yF62-tV_0ie4ZA",  # Dude Perfect
    "UCpEhnqL0y41EpW2TvWAHD7Q",  # Vlad and Niki
    "UCbxy8LzGJbMhZNCr4wRVtgg",  # Zee Music Company
    "UCEgdi0XIXXZ-qJOFPf4JSKw",  # Sports
    "UC_x5XG1OV2P6uZZ5FSM9Ttw",  # Google Developers
    "UCBJycsmduvYEL83R_U4JriQ",  # MKBHD
    "UCXuqSBlHAE6Xw-yeJA0Tunw",  # Linus Tech Tips
    "UCsvn_Po0SmunchJYOWpOxMg",  # jacksepticeye
    "UCRijo3ddMTht_IHyNSNXpNQ",  # Dua Lipa
    "UCqECaJ8Gagnn7YCbPEzWH6g",  # Taylor Swift
    "UCpko_-a4wgz2u_DgDgd9fqA",  # WWE
    "UCj22tfcQrWG7EMEKS0qLeEg",  # NBA
    "UC7_YxT-KID8kRbqZo7MyscQ",  # Markiplier
    "UCq-W1KE9ErbvC7jOhmfj6hA",  # Unbox Therapy
    "UCfV36TX5AejfAGIbtwTc7Zw",  # Veritasium
    "UCHnyfMqiRRG1u-2MsSQLbXA",  # Vsauce
]


class QuotaExceededException(Exception):
    """Raised when YouTube API quota is exceeded."""
    pass


class YouTubeCollector(DataCollector):
    """Collects trending videos from YouTube using Google API Client.

    Monitors 20 default trending channels, collecting latest video from each.
    Uses videos.list endpoint (1 unit/call) to stay within 10K daily quota.
    Implements channel metadata caching and quota tracking.

    Example:
        collector = YouTubeCollector(db_session=db)
        result = await collector.collect(topics=DEFAULT_CHANNELS)
        # Returns CollectionResult with 20 videos (1 per channel)
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

        # Channel metadata cache (1 hour TTL)
        self.channel_cache = TTLCache(maxsize=100, ttl=3600)

        logger.info("YouTubeCollector initialized", extra={
            "event": "collector_init",
            "api": "youtube",
            "quota_limit": "10000/day"
        })

    async def _get_channel_subscriber_count(
        self,
        channel_id: str
    ) -> Optional[int]:
        """Get channel subscriber count with caching.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Subscriber count, or None if failed
        """
        # Check cache first
        if channel_id in self.channel_cache:
            logger.debug(
                f"Cache hit for channel {channel_id}",
                extra={"event": "cache_hit", "channel_id": channel_id}
            )
            return self.channel_cache[channel_id]

        # Cache miss - fetch from API
        try:
            async with self.quota_limiter.consume(units=1):
                response = await asyncio.to_thread(
                    lambda: self.youtube.channels().list(
                        part="statistics",
                        id=channel_id
                    ).execute()
                )

            if not response.get('items'):
                logger.warning(f"Channel {channel_id} not found")
                return None

            subscriber_count = int(
                response['items'][0]['statistics'].get('subscriberCount', 0)
            )
            self.channel_cache[channel_id] = subscriber_count

            logger.debug(
                f"Fetched subscriber count for channel {channel_id}: {subscriber_count:,}",
                extra={
                    "event": "channel_fetch",
                    "channel_id": channel_id,
                    "subscribers": subscriber_count
                }
            )

            return subscriber_count

        except (HttpError, Exception) as e:
            logger.error(
                f"Failed to fetch channel {channel_id}: {str(e)}",
                extra={
                    "event": "channel_fetch_error",
                    "channel_id": channel_id,
                    "error": str(e)
                }
            )
            return None

    @retry_with_backoff(max_attempts=3, backoff_base=2, exceptions=(HttpError,))
    async def _fetch_latest_video(
        self,
        channel_id: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch latest video from a channel with retry logic.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Video data dictionary, or None if failed after retries
        """
        try:
            # Get latest video from channel's uploads playlist
            async with self.quota_limiter.consume(units=1):
                # Get channel's uploads playlist ID
                channel_response = await asyncio.to_thread(
                    lambda: self.youtube.channels().list(
                        part="contentDetails",
                        id=channel_id
                    ).execute()
                )

            if not channel_response.get('items'):
                logger.warning(f"Channel {channel_id} not found")
                return None

            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # Get latest video from uploads playlist
            async with self.quota_limiter.consume(units=1):
                playlist_response = await asyncio.to_thread(
                    lambda: self.youtube.playlistItems().list(
                        part="snippet",
                        playlistId=uploads_playlist_id,
                        maxResults=1
                    ).execute()
                )

            if not playlist_response.get('items'):
                logger.warning(f"No videos found for channel {channel_id}")
                return None

            video_id = playlist_response['items'][0]['snippet']['resourceId']['videoId']

            # Get video statistics
            async with self.quota_limiter.consume(units=1):
                video_response = await asyncio.to_thread(
                    lambda: self.youtube.videos().list(
                        part="snippet,statistics",
                        id=video_id
                    ).execute()
                )

            if not video_response.get('items'):
                return None

            video = video_response['items'][0]
            snippet = video['snippet']
            stats = video['statistics']

            # Parse published_at timestamp
            published_at = datetime.fromisoformat(
                snippet['publishedAt'].replace('Z', '+00:00')
            )
            hours_since_publish = (
                datetime.now(timezone.utc) - published_at
            ).total_seconds() / 3600

            # Get channel subscriber count (cached)
            subscriber_count = await self._get_channel_subscriber_count(channel_id)

            # Calculate engagement rate
            view_count = int(stats.get('viewCount', 0))
            like_count = int(stats.get('likeCount', 0))
            engagement_rate = like_count / view_count if view_count > 0 else 0.0

            video_data = {
                "video_id": video_id,
                "video_title": snippet['title'],
                "channel_title": snippet['channelTitle'],
                "channel_id": channel_id,
                "published_at": snippet['publishedAt'],
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": int(stats.get('commentCount', 0)),
                "channel_subscriber_count": subscriber_count or 0,
                "hours_since_publish": round(hours_since_publish, 2),
                "engagement_rate": round(engagement_rate, 4),
                "thumbnail_url": snippet['thumbnails']['default']['url']
            }

            return video_data

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
                    f"YouTube API error for channel {channel_id}: {str(e)}",
                    extra={
                        "event": "api_error",
                        "api": "youtube",
                        "channel_id": channel_id,
                        "error": str(e),
                        "status_code": e.resp.status
                    }
                )
                # Retry decorator will handle this
                raise

    async def collect(self, topics: List[str]) -> CollectionResult:
        """Collect trending videos from YouTube for given channels.

        Args:
            topics: List of YouTube channel IDs

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
            f"Starting YouTube collection for {len(topics)} channels",
            extra={
                "event": "collection_start",
                "api": "youtube",
                "num_topics": len(topics),
                "quota_used": current_usage
            }
        )

        # Collect from each channel
        for channel_id in topics:
            call_start = datetime.now(timezone.utc)

            try:
                video = await self._fetch_latest_video(channel_id)
                call_duration_ms = (datetime.now(timezone.utc) - call_start).total_seconds() * 1000

                if video is not None:
                    all_videos.append(video)
                    successful_calls += 1
                    logger.info(
                        f"Collected video from channel {channel_id[:20]}",
                        extra={
                            "event": "api_call",
                            "api": "youtube",
                            "topic": channel_id,
                            "success": True,
                            "video_id": video['video_id'],
                            "duration_ms": round(call_duration_ms, 2)
                        }
                    )
                else:
                    failed_calls += 1
                    errors.append(f"Failed to collect from channel {channel_id}")
                    logger.warning(
                        f"Skipping channel {channel_id[:20]} after retries",
                        extra={
                            "event": "api_call_failed",
                            "api": "youtube",
                            "topic": channel_id,
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
            f"YouTube collection complete: {len(all_videos)} videos from {successful_calls}/{total_calls} channels",
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
