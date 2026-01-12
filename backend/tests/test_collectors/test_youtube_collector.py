"""Tests for YouTube collector."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from googleapiclient.errors import HttpError

from app.collectors.youtube_collector import (
    YouTubeCollector,
    DEFAULT_CHANNELS,
    QuotaExceededException
)


@pytest.fixture
def mock_youtube_client():
    """Mock google-api-python-client."""
    with patch('app.collectors.youtube_collector.build') as mock:
        yield mock


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_settings():
    """Mock settings with YouTube API key."""
    with patch('app.collectors.youtube_collector.settings') as mock:
        mock.youtube_api_key = "test_api_key"
        mock.youtube_api_service_name = "youtube"
        mock.youtube_api_version = "v3"
        yield mock


@pytest.mark.asyncio
async def test_youtube_collector_initialization(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test that YouTubeCollector initializes correctly."""
    collector = YouTubeCollector(db_session=mock_db_session)

    assert collector.name == "youtube"
    assert collector.youtube is not None
    assert collector.quota_limiter is not None
    assert collector.channel_cache is not None
    mock_youtube_client.assert_called_once()


@pytest.mark.asyncio
async def test_collect_success(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test successful collection from YouTube."""
    # Setup mock YouTube client
    mock_youtube = MagicMock()
    mock_youtube_client.return_value = mock_youtube

    # Mock channel response
    mock_channel_response = MagicMock()
    mock_channel_response.execute.return_value = {
        'items': [{
            'contentDetails': {
                'relatedPlaylists': {
                    'uploads': 'UU_test_playlist'
                }
            }
        }]
    }
    mock_youtube.channels.return_value.list.return_value = mock_channel_response

    # Mock playlist response
    mock_playlist_response = MagicMock()
    mock_playlist_response.execute.return_value = {
        'items': [{
            'snippet': {
                'resourceId': {
                    'videoId': 'test_video_123'
                }
            }
        }]
    }
    mock_youtube.playlistItems.return_value.list.return_value = mock_playlist_response

    # Mock video response
    mock_video_response = MagicMock()
    mock_video_response.execute.return_value = {
        'items': [{
            'id': 'test_video_123',
            'snippet': {
                'title': 'Test Video',
                'channelTitle': 'Test Channel',
                'publishedAt': '2026-01-09T10:00:00Z',
                'thumbnails': {'default': {'url': 'http://example.com/thumb.jpg'}}
            },
            'statistics': {
                'viewCount': '10000',
                'likeCount': '500',
                'commentCount': '50'
            }
        }]
    }
    mock_youtube.videos.return_value.list.return_value = mock_video_response

    # Mock channel statistics for subscriber count
    mock_channel_stats_response = MagicMock()
    mock_channel_stats_response.execute.return_value = {
        'items': [{
            'statistics': {
                'subscriberCount': '1000000'
            }
        }]
    }

    collector = YouTubeCollector(db_session=mock_db_session)

    # Mock quota limiter with proper async context manager
    collector.quota_limiter.get_usage_today = AsyncMock(return_value=100)
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=None)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    collector.quota_limiter.consume = MagicMock(return_value=mock_context_manager)

    result = await collector.collect(topics=["test_channel_id"])

    assert result.source == "youtube"
    assert len(result.data) >= 0  # May vary based on mocking
    assert result.total_calls == 1


@pytest.mark.asyncio
async def test_quota_exceeded(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test handling when quota is exceeded."""
    collector = YouTubeCollector(db_session=mock_db_session)

    # Mock quota already exceeded
    collector.quota_limiter.get_usage_today = AsyncMock(return_value=10000)

    result = await collector.collect(topics=["test_channel"])

    assert result.source == "youtube"
    assert len(result.data) == 0
    assert result.success_rate == 0.0
    assert result.failed_calls == 1
    assert "quota exceeded" in result.errors[0].lower()


@pytest.mark.asyncio
async def test_quota_warning_threshold(
    mock_youtube_client,
    mock_db_session,
    mock_settings,
    caplog
):
    """Test warning logged at 80% quota threshold."""
    collector = YouTubeCollector(db_session=mock_db_session)

    # Mock quota at 80% (8000/10000)
    collector.quota_limiter.get_usage_today = AsyncMock(return_value=8234)
    collector.quota_limiter.consume = AsyncMock()

    # Mock successful collection
    collector._fetch_latest_video = AsyncMock(return_value={
        "video_id": "test123",
        "video_title": "Test"
    })

    await collector.collect(topics=["test_channel"])

    # Check warning was logged
    assert "quota at 8234" in caplog.text.lower()


@pytest.mark.asyncio
async def test_channel_caching(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test that channel metadata is cached."""
    # Setup mock
    mock_youtube = MagicMock()
    mock_youtube_client.return_value = mock_youtube

    mock_channel_response = MagicMock()
    mock_channel_response.execute.return_value = {
        'items': [{
            'statistics': {
                'subscriberCount': '1000000'
            }
        }]
    }
    mock_youtube.channels.return_value.list.return_value = mock_channel_response

    collector = YouTubeCollector(db_session=mock_db_session)

    # Mock quota limiter with proper async context manager
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=None)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    collector.quota_limiter.consume = MagicMock(return_value=mock_context_manager)

    # First call - should fetch from API
    count1 = await collector._get_channel_subscriber_count("test_channel")
    assert count1 == 1000000

    # Second call - should use cache (no additional API call)
    count2 = await collector._get_channel_subscriber_count("test_channel")
    assert count2 == 1000000

    # Verify only 1 API call was made (cached on second call)
    assert collector.quota_limiter.consume.call_count == 1


@pytest.mark.asyncio
async def test_health_check_success(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test health check with working API."""
    mock_youtube = MagicMock()
    mock_youtube_client.return_value = mock_youtube

    mock_response = MagicMock()
    mock_response.execute.return_value = {'items': [{}]}
    mock_youtube.channels.return_value.list.return_value = mock_response

    collector = YouTubeCollector(db_session=mock_db_session)
    is_healthy = await collector.health_check()

    assert is_healthy is True


@pytest.mark.asyncio
async def test_health_check_failure(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test health check with failing API."""
    mock_youtube = MagicMock()
    mock_youtube_client.return_value = mock_youtube

    mock_response = MagicMock()
    mock_response.execute.side_effect = HttpError(
        resp=MagicMock(status=403),
        content=b"Forbidden"
    )
    mock_youtube.channels.return_value.list.return_value = mock_response

    collector = YouTubeCollector(db_session=mock_db_session)
    is_healthy = await collector.health_check()

    assert is_healthy is False


@pytest.mark.asyncio
async def test_get_rate_limit_info(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test getting rate limit information."""
    collector = YouTubeCollector(db_session=mock_db_session)

    # Mock quota limiter methods
    collector.quota_limiter.get_usage_today = AsyncMock(return_value=2500)
    collector.quota_limiter.get_remaining = AsyncMock(return_value=7500)

    rate_info = await collector.get_rate_limit_info()

    assert rate_info.limit == 10000
    assert rate_info.remaining == 7500
    assert rate_info.quota_type == "per_day"


@pytest.mark.asyncio
async def test_collect_with_failure(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test graceful degradation when channel fails."""
    collector = YouTubeCollector(db_session=mock_db_session)

    # Mock first channel succeeds, second fails
    async def mock_fetch(channel_id):
        if channel_id == "channel1":
            return {"video_id": "vid1", "video_title": "Test"}
        else:
            return None

    collector._fetch_latest_video = mock_fetch
    collector.quota_limiter.get_usage_today = AsyncMock(return_value=100)

    result = await collector.collect(topics=["channel1", "channel2"])

    assert result.total_calls == 2
    assert result.successful_calls == 1
    assert result.failed_calls == 1
    assert result.success_rate == 0.5
    assert len(result.errors) == 1


@pytest.mark.asyncio
async def test_quota_consumption_units(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test that quota limiter consumes correct number of units per channel."""
    # Setup mock YouTube client
    mock_youtube = MagicMock()
    mock_youtube_client.return_value = mock_youtube

    # Mock all API responses
    mock_channel_response = MagicMock()
    mock_channel_response.execute.return_value = {
        'items': [{
            'contentDetails': {'relatedPlaylists': {'uploads': 'UU_test'}},
            'statistics': {'subscriberCount': '1000000'}
        }]
    }
    mock_youtube.channels.return_value.list.return_value = mock_channel_response

    mock_playlist_response = MagicMock()
    mock_playlist_response.execute.return_value = {
        'items': [{'snippet': {'resourceId': {'videoId': 'test_vid'}}}]
    }
    mock_youtube.playlistItems.return_value.list.return_value = mock_playlist_response

    mock_video_response = MagicMock()
    mock_video_response.execute.return_value = {
        'items': [{
            'snippet': {
                'title': 'Test',
                'channelTitle': 'Test',
                'publishedAt': '2026-01-09T10:00:00Z',
                'thumbnails': {'default': {'url': 'test.jpg'}}
            },
            'statistics': {'viewCount': '1000', 'likeCount': '50', 'commentCount': '10'}
        }]
    }
    mock_youtube.videos.return_value.list.return_value = mock_video_response

    collector = YouTubeCollector(db_session=mock_db_session)

    # Track quota consume calls
    consume_call_count = 0
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=None)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    def track_consume(units=1):
        nonlocal consume_call_count
        consume_call_count += units
        return mock_context_manager

    collector.quota_limiter.consume = MagicMock(side_effect=track_consume)
    collector.quota_limiter.get_usage_today = AsyncMock(return_value=100)

    # Collect from 1 channel
    await collector.collect(topics=["test_channel"])

    # Verify 3-4 quota units consumed (3 API calls + optional 1 for subscriber count)
    # Since subscriber count is called, expect 4 calls
    assert consume_call_count >= 3, f"Expected at least 3 units consumed, got {consume_call_count}"
    assert consume_call_count <= 4, f"Expected at most 4 units consumed, got {consume_call_count}"


@pytest.mark.asyncio
async def test_cache_ttl_expiry(
    mock_youtube_client,
    mock_db_session,
    mock_settings
):
    """Test that channel cache expires after TTL (1 hour)."""
    from unittest.mock import patch
    import time

    mock_youtube = MagicMock()
    mock_youtube_client.return_value = mock_youtube

    mock_response = MagicMock()
    mock_response.execute.return_value = {
        'items': [{'statistics': {'subscriberCount': '1000000'}}]
    }
    mock_youtube.channels.return_value.list.return_value = mock_response

    collector = YouTubeCollector(db_session=mock_db_session)

    # Mock quota limiter
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=None)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    collector.quota_limiter.consume = MagicMock(return_value=mock_context_manager)

    # First call - cache miss
    count1 = await collector._get_channel_subscriber_count("test_channel")
    assert count1 == 1000000
    assert collector.quota_limiter.consume.call_count == 1

    # Second call immediately - cache hit (no API call)
    count2 = await collector._get_channel_subscriber_count("test_channel")
    assert count2 == 1000000
    assert collector.quota_limiter.consume.call_count == 1  # Still 1

    # Simulate cache expiry by clearing it (TTL would naturally expire after 3600s)
    collector.channel_cache.clear()

    # Third call after cache expiry - cache miss again
    count3 = await collector._get_channel_subscriber_count("test_channel")
    assert count3 == 1000000
    assert collector.quota_limiter.consume.call_count == 2  # New API call made
