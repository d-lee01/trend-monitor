"""Tests for collection API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from app.models.data_collection import DataCollection
from app.models.trend import Trend
from app.collectors.base import CollectionResult


@pytest.mark.asyncio
async def test_trigger_collection_api_endpoint_exists():
    """Test that POST /collect endpoint exists in app routes."""
    from app.main import app

    # Check that collect route is registered
    routes = [str(route.path) for route in app.routes]
    has_collect_route = any("/collect" in route for route in routes)
    assert has_collect_route, "POST /collect endpoint should be registered"


def test_collection_endpoint_registered():
    """Test that collection router is registered with app."""
    from app.main import app

    # Check that /collect route exists
    routes = [route.path for route in app.routes]
    assert "/collect" in routes or any("/collect" in r for r in routes)


@pytest.mark.asyncio
async def test_store_trends_helper():
    """Test store_trends helper function logic without database."""
    from app.api.collection import store_trends

    collection_id = uuid4()

    # Create mock results
    results = {
        "reddit": CollectionResult(
            source="reddit",
            data=[
                {"title": "Test Trend", "score": 1000, "comments": 100, "upvote_ratio": 0.95, "subreddit": "test"}
            ],
            total_calls=1,
            success_rate=1.0
        )
    }

    # Mock database session
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    # Should not raise exception
    await store_trends(mock_db, collection_id, results)

    # Verify database methods were called
    assert mock_db.add.called
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_update_collection_status_helper():
    """Test update_collection_status helper function logic."""
    from app.api.collection import update_collection_status

    collection_id = uuid4()
    start_time = datetime.now(timezone.utc) - timedelta(minutes=20)

    # Mock database session and collection
    mock_db = AsyncMock()
    mock_collection = MagicMock()
    mock_collection.id = collection_id
    mock_collection.status = "in_progress"

    # Mock the result properly - scalar_one_or_none should return the mock_collection directly
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_collection)
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    # Mock results
    results = {
        "reddit": CollectionResult(source="reddit", data=[], total_calls=50, success_rate=0.98),
        "youtube": CollectionResult(source="youtube", data=[], total_calls=100, success_rate=1.0),
        "google_trends": CollectionResult(source="google_trends", data=[], total_calls=50, success_rate=0.92)
    }

    # Should not raise exception
    await update_collection_status(mock_db, collection_id, results, start_time)

    # Verify collection was updated
    assert mock_collection.status == "completed"
    assert mock_collection.reddit_api_calls == 50


@pytest.mark.asyncio
async def test_mark_collection_failed_helper():
    """Test mark_collection_failed helper function logic."""
    from app.api.collection import mark_collection_failed

    collection_id = uuid4()

    # Mock database session and collection
    mock_db = AsyncMock()
    mock_collection = MagicMock()
    mock_collection.id = collection_id
    mock_collection.status = "in_progress"

    # Mock the result properly - scalar_one_or_none should return the mock_collection directly
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_collection)
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    # Should not raise exception
    await mark_collection_failed(mock_db, collection_id, "Test error")

    # Verify collection was marked failed
    assert mock_collection.status == "failed"
    assert mock_collection.errors == [{"error": "Test error"}]


def test_default_topics_exists():
    """Test that DEFAULT_TOPICS is defined with 50 topics."""
    from app.collectors.topics import DEFAULT_TOPICS

    assert DEFAULT_TOPICS is not None
    assert len(DEFAULT_TOPICS) == 50
    assert all(isinstance(topic, str) for topic in DEFAULT_TOPICS)


def test_collection_schemas():
    """Test that Pydantic schemas are properly defined."""
    from app.schemas.collection import CollectionResponse, CollectionStatusResponse

    # Test CollectionResponse
    response = CollectionResponse(
        collection_id=uuid4(),
        status="in_progress",
        started_at=datetime.now(timezone.utc),
        message="Test message"
    )
    assert response.status == "in_progress"

    # Test CollectionStatusResponse
    status_response = CollectionStatusResponse(
        collection_id=uuid4(),
        status="completed",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        trends_found=10,
        duration_minutes=5.5,
        errors=None
    )
    assert status_response.trends_found == 10
