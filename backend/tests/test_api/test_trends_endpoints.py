"""Integration tests for trends API endpoints."""
import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trend import Trend
from app.models.data_collection import DataCollection


# GET /trends endpoint tests

@pytest.mark.asyncio
async def test_get_trends_returns_top_10_sorted(async_client: AsyncClient, db_session: AsyncSession, test_user_token: str):
    """Test GET /trends returns Top 10 trends sorted by momentum_score DESC."""
    # Setup: Create completed collection with 15 trends
    collection = DataCollection(
        id=uuid4(),
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)
    await db_session.commit()

    # Create 15 trends with varying momentum scores
    for i in range(15):
        trend = Trend(
            id=uuid4(),
            title=f"Trend {i}",
            collection_id=collection.id,
            created_at=datetime.now(timezone.utc),
            momentum_score=100.0 - (i * 5.0),
            confidence_level="high"
        )
        db_session.add(trend)

    await db_session.commit()

    # Act: GET /trends
    response = await async_client.get(
        "/trends",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert data[0]["momentum_score"] == 100.0
    assert data[9]["momentum_score"] == 55.0

    scores = [t["momentum_score"] for t in data]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_get_trends_returns_404_when_no_collections(async_client: AsyncClient, test_user_token: str):
    """Test GET /trends returns 404 when no completed collections exist."""
    response = await async_client.get(
        "/trends",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 404
    assert "no completed collections" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_trends_requires_authentication(async_client: AsyncClient):
    """Test GET /trends returns 401 without JWT token."""
    response = await async_client.get("/trends")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_trends_response_format(async_client: AsyncClient, db_session: AsyncSession, test_user_token: str):
    """Test GET /trends returns correct response format."""
    collection = DataCollection(
        id=uuid4(),
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)

    trend = Trend(
        id=uuid4(),
        title="Test Trend",
        collection_id=collection.id,
        created_at=datetime.now(timezone.utc),
        momentum_score=87.5,
        confidence_level="high",
        reddit_score=15234,
        youtube_views=2534000,
        google_trends_interest=87,
        similarweb_traffic=1250000
    )
    db_session.add(trend)
    await db_session.commit()

    response = await async_client.get(
        "/trends",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    trend_response = data[0]
    assert "id" in trend_response
    assert trend_response["title"] == "Test Trend"
    assert trend_response["confidence_level"] == "high"
    assert trend_response["momentum_score"] == 87.5
    assert trend_response["reddit_score"] == 15234
    assert trend_response["youtube_views"] == 2534000
    assert trend_response["google_trends_interest"] == 87
    assert trend_response["similarweb_traffic"] == 1250000


# GET /trends/{id} endpoint tests

@pytest.mark.asyncio
async def test_get_trend_by_id_returns_details(async_client: AsyncClient, db_session: AsyncSession, test_user_token: str):
    """Test GET /trends/{id} returns full trend details."""
    collection = DataCollection(
        id=uuid4(),
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)

    trend_id = uuid4()
    trend = Trend(
        id=trend_id,
        title="Detailed Trend",
        collection_id=collection.id,
        created_at=datetime.now(timezone.utc),
        reddit_score=15234,
        reddit_comments=892,
        reddit_upvote_ratio=0.95,
        reddit_subreddit="programming",
        youtube_views=2534000,
        youtube_likes=125000,
        youtube_channel="TechExplained",
        google_trends_interest=87,
        similarweb_traffic=1250000,
        reddit_velocity_score=78.5,
        youtube_traction_score=82.3,
        google_trends_spike_score=85.1,
        similarweb_bonus_applied=True,
        momentum_score=87.5,
        confidence_level="high"
    )
    db_session.add(trend)
    await db_session.commit()

    response = await async_client.get(
        f"/trends/{trend_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(trend_id)
    assert data["title"] == "Detailed Trend"
    assert data["reddit_score"] == 15234
    assert data["youtube_views"] == 2534000
    assert data["momentum_score"] == 87.5


@pytest.mark.asyncio
async def test_get_trend_by_id_returns_404_when_not_found(async_client: AsyncClient, test_user_token: str):
    """Test GET /trends/{id} returns 404 for non-existent ID."""
    non_existent_id = uuid4()
    response = await async_client.get(
        f"/trends/{non_existent_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_trend_by_id_requires_authentication(async_client: AsyncClient):
    """Test GET /trends/{id} returns 401 without JWT token."""
    trend_id = uuid4()
    response = await async_client.get(f"/trends/{trend_id}")
    assert response.status_code == 401


# GET /trends/collections/latest endpoint tests

@pytest.mark.asyncio
async def test_get_latest_collection_returns_summary(async_client: AsyncClient, db_session: AsyncSession, test_user_token: str):
    """Test GET /collections/latest returns collection summary."""
    collection_id = uuid4()
    collection = DataCollection(
        id=collection_id,
        started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        completed_at=datetime.now(timezone.utc),
        status="completed"
    )
    db_session.add(collection)

    for i in range(5):
        trend = Trend(
            id=uuid4(),
            title=f"Trend {i}",
            collection_id=collection_id,
            created_at=datetime.now(timezone.utc),
            momentum_score=float(50 + i),
            confidence_level="medium"
        )
        db_session.add(trend)

    await db_session.commit()

    response = await async_client.get(
        "/trends/collections/latest",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(collection_id)
    assert data["status"] == "completed"
    assert data["trends_found"] == 5


@pytest.mark.asyncio
async def test_get_latest_collection_returns_404_when_none(async_client: AsyncClient, test_user_token: str):
    """Test GET /collections/latest returns 404 when no completed collections."""
    response = await async_client.get(
        "/trends/collections/latest",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 404
    assert "no completed collections" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_latest_collection_requires_authentication(async_client: AsyncClient):
    """Test GET /collections/latest returns 401 without JWT token."""
    response = await async_client.get("/trends/collections/latest")
    assert response.status_code == 401
