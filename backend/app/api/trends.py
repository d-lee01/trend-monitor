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
from app.schemas.brief import BriefResponse
from app.services.claude_service import get_claude_service, ClaudeServiceError

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

    try:
        # Get latest completed collection
        collection_stmt = select(DataCollection).where(
            DataCollection.status == "completed"
        ).order_by(
            desc(DataCollection.completed_at)
        ).limit(1)

        collection_result = await db.execute(collection_stmt)
        collection = collection_result.scalar_one_or_none()

        if not collection:
            logger.warning(
                "No completed collections found",
                extra={
                    "event": "trends_not_found",
                    "user": current_user.username
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No completed collections found"
            )

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

    except HTTPException:
        # Re-raise HTTP exceptions (404, 401, etc.)
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve trends",
            extra={
                "event": "trends_retrieval_failed",
                "user": current_user.username,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve trends due to database error"
        )


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

    try:
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

    except HTTPException:
        # Re-raise HTTP exceptions (404, 401, etc.)
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve trend detail",
            extra={
                "event": "trend_detail_retrieval_failed",
                "user": current_user.username,
                "trend_id": str(trend_id),
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve trend due to database error"
        )


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

    try:
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

    except HTTPException:
        # Re-raise HTTP exceptions (404, 401, etc.)
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve latest collection",
            extra={
                "event": "latest_collection_retrieval_failed",
                "user": current_user.username,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve collection due to database error"
        )


@router.post("/{trend_id}/explain", response_model=BriefResponse)
async def generate_trend_brief(
    trend_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BriefResponse:
    """Generate AI-powered brief explanation for a trend using Claude API.

    This endpoint generates a 3-sentence summary explaining:
    1. What the trend is
    2. Why it's trending (with metrics)
    3. Where it's big (platform distribution)

    Briefs are cached in the database after first generation.
    Cached briefs return instantly (<100ms), fresh generation takes <3s.

    Requires JWT authentication.

    Args:
        trend_id: Unique trend identifier (UUID)
        db: Database session
        current_user: Authenticated user

    Returns:
        BriefResponse with ai_brief text, timestamp, and cached flag

    Raises:
        401 Unauthorized: JWT token missing or invalid
        404 Not Found: Trend ID doesn't exist
        503 Service Unavailable: Claude API unavailable or failed
    """
    start_time = datetime.now(timezone.utc)

    try:
        # Query trend by ID
        stmt = select(Trend).where(Trend.id == trend_id)
        result = await db.execute(stmt)
        trend = result.scalar_one_or_none()

        if not trend:
            logger.warning(
                "Trend not found for brief generation",
                extra={
                    "event": "trend_not_found_for_brief",
                    "user": current_user.username,
                    "trend_id": str(trend_id)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trend not found"
            )

        # Check if brief already cached
        if trend.ai_brief and trend.ai_brief_generated_at:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            logger.info(
                "Cached brief returned",
                extra={
                    "event": "cached_brief_returned",
                    "user": current_user.username,
                    "trend_id": str(trend_id),
                    "duration_ms": round(duration, 2)
                }
            )

            return BriefResponse(
                ai_brief=trend.ai_brief,
                generated_at=trend.ai_brief_generated_at,
                cached=True
            )

        # Generate fresh brief using Claude API
        try:
            claude_service = get_claude_service()

            # Prepare trend data for prompt
            trend_data = {
                "title": trend.title,
                "reddit_score": trend.reddit_score,
                "youtube_views": trend.youtube_views,
                "google_trends_interest": trend.google_trends_interest,
                "similarweb_traffic": trend.similarweb_traffic,
                "momentum_score": trend.momentum_score
            }

            # Generate brief
            result = await claude_service.generate_brief(trend_data)
            brief_text = result["brief"]
            tokens_used = result["tokens_used"]
            claude_duration = result["duration_ms"]

            # Store in database with explicit error handling
            try:
                trend.ai_brief = brief_text
                trend.ai_brief_generated_at = datetime.now(timezone.utc)
                await db.commit()
                await db.refresh(trend)
            except Exception as db_error:
                await db.rollback()
                logger.error(
                    "Database update failed after brief generation",
                    extra={
                        "event": "database_update_failed",
                        "user": current_user.username,
                        "trend_id": str(trend_id),
                        "error": str(db_error)
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to save AI brief to database. Brief was generated but not persisted."
                )

            # Calculate total duration
            total_duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            logger.info(
                "Fresh brief generated and stored",
                extra={
                    "event": "claude_api_call",
                    "user": current_user.username,
                    "trend_id": str(trend_id),
                    "tokens_used": tokens_used,
                    "claude_duration_ms": claude_duration,
                    "duration_ms": round(total_duration, 2),
                    "success": True
                }
            )

            return BriefResponse(
                ai_brief=brief_text,
                generated_at=trend.ai_brief_generated_at,
                cached=False
            )

        except ClaudeServiceError as e:
            logger.error(
                "Claude API failed to generate brief",
                extra={
                    "event": "claude_service_error",
                    "user": current_user.username,
                    "trend_id": str(trend_id),
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI brief generation unavailable. Claude API error. Try again later."
            )

    except HTTPException:
        # Re-raise HTTP exceptions (404, 401, 503)
        raise
    except Exception as e:
        logger.error(
            "Failed to generate trend brief",
            extra={
                "event": "brief_generation_failed",
                "user": current_user.username,
                "trend_id": str(trend_id),
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate brief due to unexpected error"
        )
