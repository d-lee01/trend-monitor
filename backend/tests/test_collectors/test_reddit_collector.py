"""Tests for Reddit collector."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from praw.exceptions import PRAWException

from app.collectors.reddit_collector import RedditCollector, DEFAULT_SUBREDDITS


@pytest.fixture
def mock_reddit_client():
    """Mock praw Reddit client."""
    with patch('app.collectors.reddit_collector.praw.Reddit') as mock:
        yield mock


@pytest.mark.asyncio
async def test_reddit_collector_initialization(mock_reddit_client):
    """Test that RedditCollector initializes correctly."""
    collector = RedditCollector()

    assert collector.name == "reddit"
    assert collector.reddit is not None
    assert collector.rate_limiter is not None
    mock_reddit_client.assert_called_once()


@pytest.mark.asyncio
async def test_collect_success(mock_reddit_client):
    """Test successful collection from Reddit."""
    # Setup mock
    mock_post = MagicMock()
    mock_post.title = "Test Post"
    mock_post.score = 1000
    mock_post.num_comments = 50
    mock_post.upvote_ratio = 0.95
    mock_post.created_utc = datetime.utcnow().timestamp() - 3600  # 1 hour ago
    mock_post.subreddit.display_name = "all"
    mock_post.subreddit.subscribers = 1000000
    mock_post.num_crossposts = 5
    mock_post.permalink = "/r/all/comments/abc123"
    mock_post.url = "https://reddit.com/r/all/comments/abc123"
    mock_post.id = "abc123"

    mock_subreddit = MagicMock()
    mock_subreddit.hot.return_value = [mock_post]
    mock_reddit_client.return_value.subreddit.return_value = mock_subreddit

    collector = RedditCollector()
    result = await collector.collect(topics=["all"])

    assert result.source == "reddit"
    assert len(result.data) == 1
    assert result.success_rate == 1.0
    assert result.total_calls == 1
    assert result.successful_calls == 1
    assert result.failed_calls == 0


@pytest.mark.asyncio
async def test_collect_with_failure(mock_reddit_client):
    """Test graceful degradation when subreddit fails."""
    # First subreddit succeeds
    mock_post = MagicMock()
    mock_post.title = "Success Post"
    mock_post.score = 500
    mock_post.num_comments = 25
    mock_post.upvote_ratio = 0.90
    mock_post.created_utc = datetime.utcnow().timestamp() - 1800
    mock_post.subreddit.display_name = "all"
    mock_post.subreddit.subscribers = 500000
    mock_post.num_crossposts = 2
    mock_post.permalink = "/r/all/comments/xyz789"
    mock_post.url = "https://reddit.com/r/all/comments/xyz789"
    mock_post.id = "xyz789"

    mock_subreddit_success = MagicMock()
    mock_subreddit_success.hot.return_value = [mock_post]

    # Mock subreddit() to return success for first call, then fail for retry attempts
    call_count = 0
    def mock_subreddit_side_effect(*args):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_subreddit_success
        else:
            raise PRAWException("API Error")

    mock_reddit_client.return_value.subreddit.side_effect = mock_subreddit_side_effect

    collector = RedditCollector()

    # Mock asyncio.sleep to speed up test
    with patch('asyncio.sleep', new_callable=AsyncMock):
        result = await collector.collect(topics=["all", "videos"])

    # Should have 1 success, 1 failure
    assert result.total_calls == 2
    assert result.successful_calls == 1
    assert result.failed_calls == 1
    assert result.success_rate == 0.5
    assert len(result.errors) == 1


@pytest.mark.asyncio
async def test_health_check_success(mock_reddit_client):
    """Test health check with working API."""
    collector = RedditCollector()
    is_healthy = await collector.health_check()

    assert is_healthy is True


@pytest.mark.asyncio
async def test_health_check_failure(mock_reddit_client):
    """Test health check with failing API."""
    mock_reddit_client.return_value.subreddit.side_effect = Exception("Auth failed")

    collector = RedditCollector()
    is_healthy = await collector.health_check()

    assert is_healthy is False


@pytest.mark.asyncio
async def test_get_rate_limit_info(mock_reddit_client):
    """Test getting rate limit information."""
    collector = RedditCollector()
    rate_info = await collector.get_rate_limit_info()

    assert rate_info.limit == 60
    assert rate_info.quota_type == "per_minute"
    assert 0 <= rate_info.remaining <= 60


@pytest.mark.asyncio
async def test_hours_since_post_calculation(mock_reddit_client):
    """Test that hours_since_post is calculated correctly."""
    # Post created 2 hours ago
    two_hours_ago = datetime.utcnow().timestamp() - 7200

    mock_post = MagicMock()
    mock_post.title = "Old Post"
    mock_post.score = 100
    mock_post.num_comments = 10
    mock_post.upvote_ratio = 0.85
    mock_post.created_utc = two_hours_ago
    mock_post.subreddit.display_name = "all"
    mock_post.subreddit.subscribers = 100000
    mock_post.num_crossposts = 0
    mock_post.permalink = "/r/all/comments/old123"
    mock_post.url = "https://reddit.com/r/all/comments/old123"
    mock_post.id = "old123"

    mock_subreddit = MagicMock()
    mock_subreddit.hot.return_value = [mock_post]
    mock_reddit_client.return_value.subreddit.return_value = mock_subreddit

    collector = RedditCollector()
    result = await collector.collect(topics=["all"])

    post_data = result.data[0]
    # Should be approximately 2.0 hours
    assert 1.9 <= post_data["hours_since_post"] <= 2.1
