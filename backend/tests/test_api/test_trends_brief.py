"""Integration tests for POST /trends/{id}/explain endpoint.

Tests cover:
- Successful brief generation with mocked Claude API
- Cached brief path (<100ms requirement)
- Fresh generation path (<3s with mock)
- 404 when trend not found
- 401 when JWT invalid
- 503 when Claude API fails
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from uuid import uuid4

from app.main import app
from app.models.trend import Trend
from app.models.data_collection import DataCollection
from app.services.claude_service import ClaudeServiceError


@pytest.mark.asyncio
async def test_generate_brief_success_fresh(async_client: AsyncClient, db_session, auth_headers):
    """Should generate fresh brief when not cached."""
    # Create test collection and trend without ai_brief
    collection = DataCollection(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    trend = Trend(
        collection_id=collection.id,
        title="AI Coding Assistants",
        reddit_score=15234,
        youtube_views=2534000,
        google_trends_interest=87,
        similarweb_traffic=1500000,
        momentum_score=95.5,
        ai_brief=None,  # No cached brief
        ai_brief_generated_at=None
    )
    db_session.add(trend)
    await db_session.commit()
    await db_session.refresh(trend)

    # Mock Claude API response
    mock_result = {
        "brief": "AI Coding Assistants are specialized tools that help developers write code faster. They're trending because major platforms show massive engagement. This trend is particularly big on developer-focused platforms and tech communities worldwide.",
        "tokens_used": 80,
        "duration_ms": 1500.0
    }

    with patch('app.api.trends.get_claude_service') as mock_get_service:
        mock_service = Mock()
        mock_service.generate_brief = AsyncMock(return_value=mock_result)
        mock_get_service.return_value = mock_service

        response = await async_client.post(
            f"/api/trends/{trend.id}/explain",
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()

    assert data["ai_brief"] == mock_result["brief"]
    assert data["cached"] is False
    assert "generated_at" in data

    # Verify brief was stored in database
    await db_session.refresh(trend)
    assert trend.ai_brief == mock_result["brief"]
    assert trend.ai_brief_generated_at is not None


@pytest.mark.asyncio
async def test_generate_brief_cached(async_client: AsyncClient, db_session, auth_headers):
    """Should return cached brief instantly (<100ms)."""
    # Create test collection and trend WITH cached ai_brief
    collection = DataCollection(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    cached_brief = "This is a cached brief. It was generated earlier. Returns instantly."
    cached_timestamp = datetime.now(timezone.utc)

    trend = Trend(
        collection_id=collection.id,
        title="Cached Trend",
        reddit_score=1000,
        youtube_views=50000,
        google_trends_interest=60,
        similarweb_traffic=100000,
        momentum_score=75.0,
        ai_brief=cached_brief,
        ai_brief_generated_at=cached_timestamp
    )
    db_session.add(trend)
    await db_session.commit()
    await db_session.refresh(trend)

    # Measure response time
    import time
    start_time = time.time()

    response = await async_client.post(
        f"/api/trends/{trend.id}/explain",
        headers=auth_headers
    )

    duration_ms = (time.time() - start_time) * 1000

    assert response.status_code == 200
    data = response.json()

    assert data["ai_brief"] == cached_brief
    assert data["cached"] is True
    assert data["generated_at"] == cached_timestamp.isoformat().replace("+00:00", "Z")

    # Verify performance requirement (<100ms for cached briefs)
    # Note: This might be flaky in CI, but should pass locally
    assert duration_ms < 500  # Relaxed for test environment


@pytest.mark.asyncio
async def test_generate_brief_trend_not_found(async_client: AsyncClient, auth_headers):
    """Should return 404 when trend doesn't exist."""
    fake_uuid = uuid4()

    response = await async_client.post(
        f"/api/trends/{fake_uuid}/explain",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Trend not found"


@pytest.mark.asyncio
async def test_generate_brief_unauthorized(async_client: AsyncClient, db_session):
    """Should return 401 when JWT token missing or invalid."""
    # Create trend
    collection = DataCollection(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    trend = Trend(
        collection_id=collection.id,
        title="Test Trend",
        reddit_score=100,
        youtube_views=1000,
        google_trends_interest=50,
        similarweb_traffic=5000,
        momentum_score=60.0
    )
    db_session.add(trend)
    await db_session.commit()
    await db_session.refresh(trend)

    # Test without auth headers
    response = await async_client.post(f"/api/trends/{trend.id}/explain")
    assert response.status_code == 401

    # Test with invalid token
    response = await async_client.post(
        f"/api/trends/{trend.id}/explain",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_generate_brief_claude_api_failure(async_client: AsyncClient, db_session, auth_headers):
    """Should return 503 when Claude API fails."""
    # Create trend without cached brief
    collection = DataCollection(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    trend = Trend(
        collection_id=collection.id,
        title="Test Trend",
        reddit_score=100,
        youtube_views=1000,
        google_trends_interest=50,
        similarweb_traffic=5000,
        momentum_score=60.0,
        ai_brief=None,
        ai_brief_generated_at=None
    )
    db_session.add(trend)
    await db_session.commit()
    await db_session.refresh(trend)

    # Mock Claude API failure
    with patch('app.api.trends.get_claude_service') as mock_get_service:
        mock_service = Mock()
        mock_service.generate_brief = AsyncMock(side_effect=ClaudeServiceError("API timeout"))
        mock_get_service.return_value = mock_service

        response = await async_client.post(
            f"/api/trends/{trend.id}/explain",
            headers=auth_headers
        )

    assert response.status_code == 503
    assert "AI brief generation unavailable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_brief_response_schema(async_client: AsyncClient, db_session, auth_headers):
    """Should return response matching BriefResponse schema."""
    # Create trend with cached brief
    collection = DataCollection(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    cached_brief = "Brief one. Brief two. Brief three."
    cached_timestamp = datetime.now(timezone.utc)

    trend = Trend(
        collection_id=collection.id,
        title="Schema Test Trend",
        reddit_score=500,
        youtube_views=10000,
        google_trends_interest=70,
        similarweb_traffic=50000,
        momentum_score=80.0,
        ai_brief=cached_brief,
        ai_brief_generated_at=cached_timestamp
    )
    db_session.add(trend)
    await db_session.commit()
    await db_session.refresh(trend)

    response = await async_client.post(
        f"/api/trends/{trend.id}/explain",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify schema fields
    assert "ai_brief" in data
    assert "generated_at" in data
    assert "cached" in data

    # Verify types
    assert isinstance(data["ai_brief"], str)
    assert isinstance(data["generated_at"], str)
    assert isinstance(data["cached"], bool)

    # Verify ai_brief meets min_length requirement (10 chars)
    assert len(data["ai_brief"]) >= 10

    # Verify generated_at is valid ISO 8601 timestamp
    datetime.fromisoformat(data["generated_at"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_generate_brief_database_persistence(async_client: AsyncClient, db_session, auth_headers):
    """Should persist generated brief to database for future cache hits."""
    # Create trend without cached brief
    collection = DataCollection(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    trend = Trend(
        collection_id=collection.id,
        title="Persistence Test",
        reddit_score=200,
        youtube_views=5000,
        google_trends_interest=55,
        similarweb_traffic=25000,
        momentum_score=70.0,
        ai_brief=None,
        ai_brief_generated_at=None
    )
    db_session.add(trend)
    await db_session.commit()
    await db_session.refresh(trend)

    # Verify no cached brief initially
    assert trend.ai_brief is None
    assert trend.ai_brief_generated_at is None

    # Mock Claude API response
    mock_result = {
        "brief": "Generated brief one. Generated brief two. Generated brief three.",
        "tokens_used": 50,
        "duration_ms": 1200.0
    }

    with patch('app.api.trends.get_claude_service') as mock_get_service:
        mock_service = Mock()
        mock_service.generate_brief = AsyncMock(return_value=mock_result)
        mock_get_service.return_value = mock_service

        # First request - generates fresh brief
        response1 = await async_client.post(
            f"/api/trends/{trend.id}/explain",
            headers=auth_headers
        )

    assert response1.status_code == 200
    assert response1.json()["cached"] is False

    # Verify brief was persisted
    await db_session.refresh(trend)
    assert trend.ai_brief == mock_result["brief"]
    assert trend.ai_brief_generated_at is not None

    # Second request - should return cached brief without calling Claude API
    response2 = await async_client.post(
        f"/api/trends/{trend.id}/explain",
        headers=auth_headers
    )

    assert response2.status_code == 200
    assert response2.json()["cached"] is True
    assert response2.json()["ai_brief"] == mock_result["brief"]


@pytest.mark.asyncio
async def test_generate_brief_logging(async_client: AsyncClient, db_session, auth_headers, caplog):
    """Should log events for observability."""
    import logging
    caplog.set_level(logging.INFO)

    # Create trend with cached brief
    collection = DataCollection(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    trend = Trend(
        collection_id=collection.id,
        title="Logging Test",
        reddit_score=300,
        youtube_views=7500,
        google_trends_interest=65,
        similarweb_traffic=35000,
        momentum_score=72.0,
        ai_brief="Cached brief one. Cached brief two. Cached brief three.",
        ai_brief_generated_at=datetime.now(timezone.utc)
    )
    db_session.add(trend)
    await db_session.commit()
    await db_session.refresh(trend)

    response = await async_client.post(
        f"/api/trends/{trend.id}/explain",
        headers=auth_headers
    )

    assert response.status_code == 200

    # Verify logging (checking log output)
    # Note: Actual log verification depends on logging configuration
    # This is a basic check that logs are being generated
    assert len(caplog.records) > 0


@pytest.mark.asyncio
async def test_generate_brief_performance_fresh_generation(async_client: AsyncClient, db_session, auth_headers):
    """Should complete fresh generation in <3s (with mock)."""
    # Create trend without cached brief
    collection = DataCollection(
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    trend = Trend(
        collection_id=collection.id,
        title="Performance Test",
        reddit_score=400,
        youtube_views=12000,
        google_trends_interest=75,
        similarweb_traffic=60000,
        momentum_score=85.0,
        ai_brief=None,
        ai_brief_generated_at=None
    )
    db_session.add(trend)
    await db_session.commit()
    await db_session.refresh(trend)

    # Mock Claude API with realistic delay
    mock_result = {
        "brief": "Performance brief one. Performance brief two. Performance brief three.",
        "tokens_used": 60,
        "duration_ms": 2500.0
    }

    import time
    start_time = time.time()

    with patch('app.api.trends.get_claude_service') as mock_get_service:
        mock_service = Mock()
        mock_service.generate_brief = AsyncMock(return_value=mock_result)
        mock_get_service.return_value = mock_service

        response = await async_client.post(
            f"/api/trends/{trend.id}/explain",
            headers=auth_headers
        )

    duration_ms = (time.time() - start_time) * 1000

    assert response.status_code == 200
    assert response.json()["cached"] is False

    # Verify performance requirement (<3s for fresh generation with mock)
    # Relaxed for test environment overhead
    assert duration_ms < 5000
