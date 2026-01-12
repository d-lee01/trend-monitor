"""Tests for SimilarWeb collector."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timezone
import requests

from app.collectors.similarweb_collector import (
    SimilarWebCollector,
    DEFAULT_DOMAINS
)


@pytest.fixture
def mock_settings():
    """Mock settings with SimilarWeb API key."""
    with patch('app.collectors.similarweb_collector.settings') as mock:
        mock.similarweb_api_key = "test_api_key"
        mock.similarweb_api_base_url = "https://api.similarweb.com/v1"
        yield mock


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_similarweb_collector_initialization(
    mock_settings,
    mock_db_session
):
    """Test that SimilarWebCollector initializes correctly."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    assert collector.name == "similarweb"
    assert collector.session is not None
    assert "Authorization" in collector.session.headers


@pytest.mark.asyncio
async def test_collect_success(
    mock_settings,
    mock_db_session
):
    """Test successful collection from SimilarWeb."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    # Mock HTTP responses
    mock_traffic_response = Mock()
    mock_traffic_response.status_code = 200
    mock_traffic_response.json.return_value = {
        "visits": 1000000,
        "pages_per_visit": 3.5,
        "average_visit_duration": 180,
        "bounce_rate": 0.45,
        "historical_visits": [800000, 850000, 900000, 920000, 950000, 980000, 1000000]
    }

    mock_sources_response = Mock()
    mock_sources_response.status_code = 200
    mock_sources_response.json.return_value = {
        "search": 0.35,
        "social": 0.25,
        "direct": 0.20
    }

    mock_geo_response = Mock()
    mock_geo_response.status_code = 200
    mock_geo_response.json.return_value = {
        "US": 0.45,
        "UK": 0.15
    }

    with patch.object(collector.session, 'get') as mock_get:
        mock_get.side_effect = [
            mock_traffic_response,
            mock_sources_response,
            mock_geo_response
        ]

        result = await collector.collect(topics=["test.com"])

        assert result.source == "similarweb"
        assert len(result.data) == 1
        assert result.success_rate == 1.0
        assert result.data[0]['domain'] == 'test.com'
        assert result.data[0]['total_visits'] == 1000000


@pytest.mark.asyncio
async def test_traffic_spike_detection(
    mock_settings,
    mock_db_session
):
    """Test traffic spike detection algorithm."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    # History with clear spike (100k → 200k = +100% spike)
    seven_day_history = [100000, 105000, 98000, 102000, 99000, 101000, 103000]
    current_visits = 200000

    change_pct, spike_detected = collector._calculate_traffic_spike(
        current_visits,
        seven_day_history
    )

    assert spike_detected is True
    assert change_pct > 50.0


@pytest.mark.asyncio
async def test_no_traffic_spike(
    mock_settings,
    mock_db_session
):
    """Test that stable traffic doesn't trigger spike."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    # Stable history
    seven_day_history = [100000, 102000, 98000, 101000, 99000, 103000, 100000]
    current_visits = 105000  # Only +5% change

    change_pct, spike_detected = collector._calculate_traffic_spike(
        current_visits,
        seven_day_history
    )

    assert spike_detected is False


@pytest.mark.asyncio
async def test_handle_401_unauthorized(
    mock_settings,
    mock_db_session
):
    """Test handling of authentication errors."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    # Mock 401 error
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

    with patch.object(collector.session, 'get', return_value=mock_response):
        result = await collector.collect(topics=["test.com"])

        assert result.failed_calls == 1
        assert len(result.errors) > 0


@pytest.mark.asyncio
async def test_handle_429_rate_limit(
    mock_settings,
    mock_db_session
):
    """Test handling of rate limit errors."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    # Mock 429 error
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

    with patch.object(collector.session, 'get', return_value=mock_response):
        result = await collector.collect(topics=["test.com"])

        assert result.failed_calls == 1


@pytest.mark.asyncio
async def test_handle_404_domain_not_found(
    mock_settings,
    mock_db_session
):
    """Test handling of domain not found."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    # Mock 404 error
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

    with patch.object(collector.session, 'get', return_value=mock_response):
        result = await collector.collect(topics=["unknown-domain.com"])

        assert result.failed_calls == 1


@pytest.mark.asyncio
async def test_health_check_success(
    mock_settings,
    mock_db_session
):
    """Test health check with working API."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()

    with patch.object(collector.session, 'get', return_value=mock_response):
        is_healthy = await collector.health_check()

        assert is_healthy is True


@pytest.mark.asyncio
async def test_health_check_failure(
    mock_settings,
    mock_db_session
):
    """Test health check with failing API."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    # Mock failure
    with patch.object(collector.session, 'get', side_effect=Exception("API unavailable")):
        is_healthy = await collector.health_check()

        assert is_healthy is False


@pytest.mark.asyncio
async def test_get_rate_limit_info(
    mock_settings,
    mock_db_session
):
    """Test getting rate limit information."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    rate_info = await collector.get_rate_limit_info()

    assert rate_info.quota_type == "subscription_based"


@pytest.mark.asyncio
async def test_collect_with_timeout(
    mock_settings,
    mock_db_session
):
    """Test handling of API timeout."""
    collector = SimilarWebCollector(db_session=mock_db_session)

    # Mock timeout
    with patch.object(collector.session, 'get', side_effect=requests.exceptions.Timeout()):
        result = await collector.collect(topics=["test.com"])

        assert result.failed_calls == 1
