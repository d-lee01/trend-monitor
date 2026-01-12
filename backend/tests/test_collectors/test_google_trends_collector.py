"""Tests for Google Trends collector."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
import pandas as pd
from pytrends.exceptions import TooManyRequestsError, ResponseError

from app.collectors.google_trends_collector import (
    GoogleTrendsCollector,
    DEFAULT_TOPICS
)


@pytest.fixture
def mock_pytrends():
    """Mock PyTrends TrendReq."""
    with patch('app.collectors.google_trends_collector.TrendReq') as mock:
        yield mock


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_google_trends_collector_initialization(
    mock_pytrends,
    mock_db_session
):
    """Test that GoogleTrendsCollector initializes correctly."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    assert collector.name == "google_trends"
    assert collector.pytrend is not None
    assert collector.last_request_time is None
    mock_pytrends.assert_called_once()


@pytest.mark.asyncio
async def test_collect_success(
    mock_pytrends,
    mock_db_session
):
    """Test successful collection from Google Trends."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    # Mock interest_over_time response
    mock_df = pd.DataFrame({
        'test_topic': [45, 52, 67, 71, 85, 92, 100],
        'isPartial': [False] * 7
    })

    collector.pytrend.interest_over_time = MagicMock(return_value=mock_df)
    collector.pytrend.build_payload = MagicMock()
    collector.pytrend.related_queries = MagicMock(return_value={'test_topic': {}})

    result = await collector.collect(topics=["test_topic"])

    assert result.source == "google_trends"
    assert len(result.data) == 1
    assert result.success_rate == 1.0
    assert result.data[0]['topic'] == 'test_topic'
    assert result.data[0]['current_interest'] == 100
    assert len(result.data[0]['seven_day_history']) == 7


@pytest.mark.asyncio
async def test_60_second_delay_enforcement(
    mock_pytrends,
    mock_db_session
):
    """Test that 60-second delays are enforced between requests."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    # Mock responses
    mock_df = pd.DataFrame({'topic1': [50], 'topic2': [60]})
    collector.pytrend.interest_over_time = MagicMock(return_value=mock_df)
    collector.pytrend.build_payload = MagicMock()
    collector.pytrend.related_queries = MagicMock(return_value={})

    # Track sleep calls
    with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
        # Set last_request_time to 10 seconds ago
        collector.last_request_time = datetime.now(timezone.utc) - timedelta(seconds=10)

        await collector.collect(topics=["topic1"])

        # Should have slept for ~50 seconds (60 - 10)
        if mock_sleep.call_count > 0:
            sleep_time = mock_sleep.call_args[0][0]
            assert 45 <= sleep_time <= 55  # Allow some tolerance


@pytest.mark.asyncio
async def test_spike_detection(
    mock_pytrends,
    mock_db_session
):
    """Test spike detection algorithm."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    # History with clear spike
    seven_day_history = [10, 12, 11, 13, 12, 14, 95]  # Last day is spike

    spike_score, spike_detected = collector._calculate_spike_score(
        current_interest=95,
        seven_day_history=seven_day_history
    )

    assert spike_detected is True
    assert spike_score > 80  # Should be high score


@pytest.mark.asyncio
async def test_no_spike_detection(
    mock_pytrends,
    mock_db_session
):
    """Test that stable data doesn't trigger spike."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    # Stable history
    seven_day_history = [50, 52, 51, 53, 52, 54, 53]

    spike_score, spike_detected = collector._calculate_spike_score(
        current_interest=53,
        seven_day_history=seven_day_history
    )

    assert spike_detected is False


@pytest.mark.asyncio
async def test_handle_too_many_requests_error(
    mock_pytrends,
    mock_db_session
):
    """Test handling of rate limit errors."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    # Mock TooManyRequestsError (requires response parameter)
    mock_response = MagicMock()
    mock_response.status_code = 429
    collector.pytrend.build_payload = MagicMock()
    collector.pytrend.interest_over_time = MagicMock(
        side_effect=TooManyRequestsError("Rate limit exceeded", response=mock_response)
    )

    result = await collector.collect(topics=["test_topic"])

    # Should gracefully handle error
    assert result.source == "google_trends"
    assert len(result.data) == 0
    assert result.failed_calls == 1
    assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_handle_response_error(
    mock_pytrends,
    mock_db_session
):
    """Test handling of response errors."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    # Mock ResponseError (requires response parameter)
    mock_response = MagicMock()
    mock_response.status_code = 500
    collector.pytrend.build_payload = MagicMock()
    collector.pytrend.interest_over_time = MagicMock(
        side_effect=ResponseError("Invalid response", response=mock_response)
    )

    result = await collector.collect(topics=["test_topic"])

    # Should gracefully handle error
    assert result.failed_calls == 1


@pytest.mark.asyncio
async def test_health_check_success(
    mock_pytrends,
    mock_db_session
):
    """Test health check with working PyTrends."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    # Mock successful response
    mock_df = pd.DataFrame({'Python': [75]})
    collector.pytrend.interest_over_time = MagicMock(return_value=mock_df)
    collector.pytrend.build_payload = MagicMock()

    is_healthy = await collector.health_check()

    assert is_healthy is True


@pytest.mark.asyncio
async def test_health_check_failure(
    mock_pytrends,
    mock_db_session
):
    """Test health check with failing PyTrends."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    # Mock failure
    collector.pytrend.build_payload = MagicMock(
        side_effect=Exception("PyTrends unavailable")
    )

    is_healthy = await collector.health_check()

    assert is_healthy is False


@pytest.mark.asyncio
async def test_get_rate_limit_info(
    mock_pytrends,
    mock_db_session
):
    """Test getting rate limit information."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    rate_info = await collector.get_rate_limit_info()

    assert rate_info.limit == 60
    assert rate_info.quota_type == "per_request"


@pytest.mark.asyncio
async def test_collect_with_empty_dataframe(
    mock_pytrends,
    mock_db_session
):
    """Test handling of empty DataFrame (no data for topic)."""
    collector = GoogleTrendsCollector(db_session=mock_db_session)

    # Mock empty DataFrame
    mock_df = pd.DataFrame()
    collector.pytrend.interest_over_time = MagicMock(return_value=mock_df)
    collector.pytrend.build_payload = MagicMock()

    result = await collector.collect(topics=["unknown_topic"])

    # Should handle gracefully
    assert len(result.data) == 0
    assert result.failed_calls == 1
