"""Trends API endpoints for retrieving ranked trends and trend details."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from typing import List

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.trend import Trend
from app.models.data_collection import DataCollection
from app.schemas.trend import TrendListResponse, TrendDetailResponse, CollectionSummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("", response_model=List[TrendListResponse])
async def get_top_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TrendListResponse]:
    """Get Top 10 trends ranked by momentum score from latest completed collection.

    Requires JWT authentication.

    Returns:
        List of top 10 trends sorted by momentum_score DESC.
        Returns empty list if no completed collections exist.

    Raises:
        401 Unauthorized if JWT token missing or invalid.
    """
    start_time = datetime.now(timezone.utc)

    # Get latest completed collection
    collection_stmt = select(DataCollection).where(
        DataCollection.status == "completed"
    ).order_by(
        desc(DataCollection.completed_at)
    ).limit(1)

    collection_result = await db.execute(collection_stmt)
    collection = collection_result.scalar_one_or_none()

    if not collection:
        logger.info(
            "No completed collections found",
            extra={
                "event": "trends_retrieved",
                "user": current_user.username,
                "trends_count": 0,
                "duration_ms": 0
            }
        )
        return []

    # Get top 10 trends from latest collection
    trends_stmt = select(Trend).where(
        Trend.collection_id == collection.id
    ).order_by(
        desc(Trend.momentum_score)
    ).limit(10)

    trends_result = await db.execute(trends_stmt)
    trends = trends_result.scalars().all()

    # Calculate duration
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    logger.info(
        "Trends retrieved",
        extra={
            "event": "trends_retrieved",
            "user": current_user.username,
            "collection_id": str(collection.id),
            "trends_count": len(trends),
            "top_momentum": trends[0].momentum_score if trends else 0,
            "duration_ms": round(duration * 1000, 2)
        }
    )

    return trends


@router.get("/{trend_id}", response_model=TrendDetailResponse)
async def get_trend_by_id(
    trend_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TrendDetailResponse:
    """Get detailed information for a specific trend by ID.

    Requires JWT authentication.

    Args:
        trend_id: Unique trend identifier (UUID)

    Returns:
        Detailed trend information including all platform metrics and scores.

    Raises:
        401 Unauthorized if JWT token missing or invalid.
        404 Not Found if trend ID doesn't exist.
    """
    start_time = datetime.now(timezone.utc)

    # Query trend by ID
    stmt = select(Trend).where(Trend.id == trend_id)
    result = await db.execute(stmt)
    trend = result.scalar_one_or_none()

    if not trend:
        logger.warning(
            "Trend not found",
            extra={
                "event": "trend_not_found",
                "user": current_user.username,
                "trend_id": str(trend_id)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trend not found"
        )

    # Calculate duration
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    logger.info(
        "Trend detail retrieved",
        extra={
            "event": "trend_detail_retrieved",
            "user": current_user.username,
            "trend_id": str(trend_id),
            "momentum_score": trend.momentum_score,
            "duration_ms": round(duration * 1000, 2)
        }
    )

    return trend


@router.get("/collections/latest", response_model=CollectionSummaryResponse)
async def get_latest_collection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CollectionSummaryResponse:
    """Get summary of the latest completed data collection.

    Requires JWT authentication.

    Returns:
        Latest collection metadata including trends count.

    Raises:
        401 Unauthorized if JWT token missing or invalid.
        404 Not Found if no completed collections exist.
    """
    start_time = datetime.now(timezone.utc)

    # Get latest completed collection with trends count
    collection_stmt = select(
        DataCollection,
        func.count(Trend.id).label("trends_found")
    ).outerjoin(
        Trend, Trend.collection_id == DataCollection.id
    ).where(
        DataCollection.status == "completed"
    ).group_by(
        DataCollection.id
    ).order_by(
        desc(DataCollection.completed_at)
    ).limit(1)

    result = await db.execute(collection_stmt)
    row = result.first()

    if not row:
        logger.warning(
            "No completed collections found",
            extra={
                "event": "latest_collection_not_found",
                "user": current_user.username
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed collections found"
        )

    collection, trends_found = row

    # Calculate duration
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

    logger.info(
        "Latest collection retrieved",
        extra={
            "event": "latest_collection_retrieved",
            "user": current_user.username,
            "collection_id": str(collection.id),
            "trends_found": trends_found,
            "duration_ms": round(duration * 1000, 2)
        }
    )

    # Create response with trends_found
    response = CollectionSummaryResponse(
        id=collection.id,
        started_at=collection.started_at,
        completed_at=collection.completed_at,
        status=collection.status,
        trends_found=trends_found
    )

    return response
