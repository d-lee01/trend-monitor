"""Collection API endpoints for manual data collection trigger."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.data_collection import DataCollection
from app.models.trend import Trend
from app.schemas.collection import CollectionResponse, CollectionStatusResponse
from app.collectors.reddit_collector import RedditCollector
from app.collectors.youtube_collector import YouTubeCollector
from app.collectors.google_trends_collector import GoogleTrendsCollector
from app.collectors.similarweb_collector import SimilarWebCollector
from app.collectors.orchestrator import CollectionOrchestrator
from app.collectors.base import CollectionResult
from app.collectors.topics import DEFAULT_TOPICS

logger = logging.getLogger(__name__)

router = APIRouter(tags=["collection"])


async def store_trends(
    db: AsyncSession,
    collection_id: UUID,
    results: Dict[str, CollectionResult]
):
    """Store collected trends in database.

    Args:
        db: Database session
        collection_id: UUID of the collection run
        results: Dictionary mapping collector name to CollectionResult
    """
    logger.info(
        "Storing trends in database",
        extra={
            "event": "store_trends_start",
            "collection_id": str(collection_id),
            "num_sources": len(results)
        }
    )

    trends_stored = 0

    # Extract data from all collectors
    for source, result in results.items():
        for trend_data in result.data:
            if trend_data is None:
                continue  # Skip failed items

            # Create trend record
            trend = Trend(
                id=uuid4(),
                title=trend_data.get("title", trend_data.get("topic", "Untitled")),
                collection_id=collection_id,
                created_at=datetime.now(timezone.utc)
            )

            # Map source-specific data to trend columns
            if source == "reddit":
                trend.reddit_score = trend_data.get("score")
                trend.reddit_comments = trend_data.get("comments")
                trend.reddit_upvote_ratio = trend_data.get("upvote_ratio")
                trend.reddit_subreddit = trend_data.get("subreddit")
                trend.reddit_velocity_score = trend_data.get("velocity_score")
                trend.reddit_spike_detected = trend_data.get("spike_detected", False)

            elif source == "youtube":
                trend.youtube_views = trend_data.get("views")
                trend.youtube_likes = trend_data.get("likes")
                trend.youtube_comments = trend_data.get("comments")
                trend.youtube_channel = trend_data.get("channel")
                trend.youtube_engagement_rate = trend_data.get("engagement_rate")
                trend.youtube_spike_detected = trend_data.get("spike_detected", False)

            elif source == "google_trends":
                trend.google_trends_interest = trend_data.get("current_interest")
                trend.google_trends_spike_score = trend_data.get("spike_score")
                trend.google_trends_spike_detected = trend_data.get("spike_detected", False)

            elif source == "similarweb":
                trend.similarweb_traffic = trend_data.get("total_visits")
                trend.similarweb_sources = trend_data.get("traffic_sources")
                trend.similarweb_bonus_applied = trend_data.get("traffic_spike_detected", False)

            db.add(trend)
            trends_stored += 1

    await db.commit()

    logger.info(
        f"Stored {trends_stored} trends",
        extra={
            "event": "store_trends_complete",
            "collection_id": str(collection_id),
            "trends_stored": trends_stored
        }
    )


async def update_collection_status(
    db: AsyncSession,
    collection_id: UUID,
    results: Dict[str, CollectionResult],
    start_time: datetime
):
    """Update collection record with completion status and metrics.

    Args:
        db: Database session
        collection_id: UUID of the collection run
        results: Dictionary mapping collector name to CollectionResult
        start_time: When the collection started
    """
    # Get collection record
    stmt = select(DataCollection).where(DataCollection.id == collection_id)
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()

    if not collection:
        logger.error(
            "Cannot update collection status - collection not found",
            extra={
                "event": "collection_not_found",
                "collection_id": str(collection_id)
            }
        )
        return

    # Calculate metrics
    reddit_result = results.get("reddit", CollectionResult("reddit", []))
    youtube_result = results.get("youtube", CollectionResult("youtube", []))
    google_trends_result = results.get("google_trends", CollectionResult("google_trends", []))

    reddit_calls = reddit_result.total_calls
    youtube_quota = youtube_result.total_calls
    google_trends_calls = google_trends_result.total_calls

    # Update record
    collection.status = "completed"
    collection.completed_at = datetime.now(timezone.utc)
    collection.reddit_api_calls = reddit_calls
    collection.youtube_api_quota_used = youtube_quota
    collection.google_trends_api_calls = google_trends_calls

    # Log any errors
    errors = []
    for source, result in results.items():
        if result.errors:
            errors.append({
                "source": source,
                "errors": result.errors
            })

    if errors:
        collection.errors = errors

    await db.commit()

    # Calculate duration
    duration_minutes = (datetime.now(timezone.utc) - start_time).total_seconds() / 60

    logger.info(
        "Collection status updated to completed",
        extra={
            "event": "collection_status_updated",
            "collection_id": str(collection_id),
            "duration_minutes": round(duration_minutes, 2),
            "reddit_calls": reddit_calls,
            "youtube_quota": youtube_quota,
            "google_trends_calls": google_trends_calls,
            "has_errors": len(errors) > 0
        }
    )


async def mark_collection_failed(
    db: AsyncSession,
    collection_id: UUID,
    error_message: str
):
    """Mark collection as failed.

    Args:
        db: Database session
        collection_id: UUID of the collection run
        error_message: Error message describing the failure
    """
    stmt = select(DataCollection).where(DataCollection.id == collection_id)
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()

    if not collection:
        logger.error(
            "Cannot mark collection as failed - collection not found",
            extra={
                "event": "collection_not_found",
                "collection_id": str(collection_id),
                "error": error_message
            }
        )
        return

    collection.status = "failed"
    collection.completed_at = datetime.now(timezone.utc)
    collection.errors = [{"error": error_message}]

    await db.commit()

    logger.error(
        "Collection marked as failed",
        extra={
            "event": "collection_failed",
            "collection_id": str(collection_id),
            "error": error_message
        }
    )


async def run_collection(collection_id: UUID):
    """Background task to run data collection.

    Args:
        collection_id: UUID of the collection run to execute
    """
    start_time = datetime.now(timezone.utc)

    logger.info(
        "Manual collection triggered",
        extra={
            "event": "manual_collection_start",
            "collection_id": str(collection_id),
            "topics_count": len(DEFAULT_TOPICS)
        }
    )

    # Get new DB session for background task
    async for db in get_db():
        try:
            # Initialize collectors
            reddit_collector = RedditCollector(db_session=db)
            youtube_collector = YouTubeCollector(db_session=db)
            google_trends_collector = GoogleTrendsCollector(db_session=db)
            similarweb_collector = SimilarWebCollector(db_session=db)

            # Initialize orchestrator
            orchestrator = CollectionOrchestrator(
                collectors=[
                    reddit_collector,
                    youtube_collector,
                    google_trends_collector,
                    similarweb_collector
                ],
                db_session=db
            )

            logger.info(
                "Orchestrator initialized with 4 collectors",
                extra={
                    "event": "orchestrator_init",
                    "collection_id": str(collection_id),
                    "collectors": ["reddit", "youtube", "google_trends", "similarweb"]
                }
            )

            # Run collection
            results = await orchestrator.collect_all(
                topics=DEFAULT_TOPICS,
                collection_id=collection_id
            )

            # Store trends
            await store_trends(db, collection_id, results)

            # Update collection status
            await update_collection_status(db, collection_id, results, start_time)

            # Calculate total trends
            total_trends = sum(
                len([d for d in result.data if d is not None])
                for result in results.values()
            )

            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() / 60

            logger.info(
                f"Collection complete: {total_trends} trends found",
                extra={
                    "event": "manual_collection_complete",
                    "collection_id": str(collection_id),
                    "trends_found": total_trends,
                    "duration_minutes": round(duration, 2),
                    "api_success_rates": {
                        source: result.success_rate
                        for source, result in results.items()
                    }
                }
            )

        except Exception as e:
            logger.exception(
                "Collection failed with exception",
                extra={
                    "event": "manual_collection_failed",
                    "collection_id": str(collection_id),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            await mark_collection_failed(db, collection_id, str(e))

        break  # Exit after first iteration


async def increment_failure_count(db: AsyncSession):
    """Track consecutive failed scheduled collections.

    Uses api_quota_usage table with api_name='scheduler_failures' to track
    consecutive failures for alerting purposes.

    Args:
        db: Database session
    """
    from app.models.api_quota_usage import ApiQuotaUsage
    from sqlalchemy import insert
    from datetime import date

    stmt = insert(ApiQuotaUsage).values(
        api_name='scheduler_failures',
        date=date.today(),
        units_used=1
    ).on_conflict_do_update(
        index_elements=['api_name', 'date'],
        set_={'units_used': ApiQuotaUsage.units_used + 1}
    )

    await db.execute(stmt)
    await db.commit()

    logger.info("Incremented scheduler failure count")


async def reset_failure_count(db: AsyncSession):
    """Reset failure count on successful collection.

    Args:
        db: Database session
    """
    from app.models.api_quota_usage import ApiQuotaUsage
    from sqlalchemy import delete

    stmt = delete(ApiQuotaUsage).where(
        ApiQuotaUsage.api_name == 'scheduler_failures'
    )

    await db.execute(stmt)
    await db.commit()

    logger.info("Reset scheduler failure count after successful collection")


async def check_failure_alert_threshold(db: AsyncSession):
    """Send alert if failed 2 days in a row.

    Checks the last 2 days of scheduler_failures records and logs a CRITICAL
    alert if both days had failures, indicating a systemic issue.

    Args:
        db: Database session
    """
    from app.models.api_quota_usage import ApiQuotaUsage
    from sqlalchemy import select
    from datetime import date, timedelta

    # Check last 2 days
    today = date.today()
    yesterday = today - timedelta(days=1)

    stmt = select(ApiQuotaUsage).where(
        ApiQuotaUsage.api_name == 'scheduler_failures',
        ApiQuotaUsage.date.in_([today, yesterday])
    ).order_by(ApiQuotaUsage.date.desc())

    result = await db.execute(stmt)
    failures = result.scalars().all()

    if len(failures) == 2 and failures[0].units_used > 0 and failures[1].units_used > 0:
        # 2 consecutive days with failures
        logger.critical(
            "ALERT: Scheduled collection failed 2 days in a row",
            extra={
                "event": "scheduled_collection_alert",
                "alert_type": "consecutive_failures",
                "days_failed": 2,
                "today_failures": failures[0].units_used,
                "yesterday_failures": failures[1].units_used,
                "action_required": "Manual investigation needed"
            }
        )
        # TODO Phase 2: Send email alert via SendGrid


async def trigger_daily_collection():
    """Scheduled job function - runs at 7:30 AM daily.

    This function is called by APScheduler and triggers the same
    data collection logic as the manual POST /collect endpoint.

    Prevents duplicate collections and logs all events for monitoring.
    Implements retry logic on failure (see trigger_daily_collection_retry).
    """
    try:
        async for db in get_db():
            try:
                # Check for existing in-progress collection
                stmt = select(DataCollection).where(
                    DataCollection.status == "in_progress"
                )
                result = await db.execute(stmt)
                existing_collection = result.scalar_one_or_none()

                if existing_collection:
                    logger.warning(
                        "Skipped scheduled collection - previous collection still in progress",
                        extra={
                            "event": "scheduled_collection_skipped",
                            "reason": "in_progress_collection_exists",
                            "existing_collection_id": str(existing_collection.id),
                            "existing_started_at": existing_collection.started_at.isoformat(),
                            "duration_so_far_minutes": (
                                datetime.now(timezone.utc) - existing_collection.started_at
                            ).total_seconds() / 60
                        }
                    )
                    return

                # Log scheduled collection start
                logger.info(
                    "Starting scheduled daily collection",
                    extra={
                        "event": "scheduled_collection_start",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "scheduled_time": "07:30 AM Pacific",
                        "trigger_type": "automated"
                    }
                )

                # Create collection record
                collection = DataCollection(
                    id=uuid4(),
                    started_at=datetime.now(timezone.utc),
                    status="in_progress"
                )
                db.add(collection)
                await db.commit()
                await db.refresh(collection)

                # Run collection (reuse existing background task)
                await run_collection(collection.id)

                # Reset failure count on success
                await reset_failure_count(db)

                logger.info(
                    "Scheduled daily collection completed successfully",
                    extra={
                        "event": "scheduled_collection_complete",
                        "collection_id": str(collection.id)
                    }
                )

            except Exception as e:
                logger.exception(
                    "Scheduled collection failed with exception",
                    extra={
                        "event": "scheduled_collection_failed",
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )

                # Track failure and check alert threshold
                await increment_failure_count(db)
                await check_failure_alert_threshold(db)

                # Schedule retry job (one-time, 30 minutes from now)
                from app.scheduler import scheduler
                from datetime import timedelta

                retry_time = datetime.now(timezone.utc) + timedelta(minutes=30)

                scheduler.add_job(
                    func=trigger_daily_collection_retry,
                    trigger='date',
                    run_date=retry_time,
                    id='daily_collection_retry',
                    name='Retry failed daily collection',
                    replace_existing=True,  # Replace if retry already scheduled
                    max_instances=1
                )

                logger.info(
                    "Scheduled collection retry",
                    extra={
                        "event": "scheduled_collection_retry_scheduled",
                        "retry_time": retry_time.isoformat(),
                        "retry_in_minutes": 30
                    }
                )

            break  # Exit async generator after first iteration
    except Exception as db_error:
        # Catch database connection failures and other errors not caught in inner try
        logger.exception(
            "Scheduled collection failed with database or infrastructure error",
            extra={
                "event": "scheduled_collection_infrastructure_failure",
                "error": str(db_error),
                "error_type": type(db_error).__name__
            }
        )

        # Schedule retry even for database failures
        from app.scheduler import scheduler
        from datetime import timedelta

        retry_time = datetime.now(timezone.utc) + timedelta(minutes=30)

        scheduler.add_job(
            func=trigger_daily_collection_retry,
            trigger='date',
            run_date=retry_time,
            id='daily_collection_retry',
            name='Retry failed daily collection',
            replace_existing=True,
            max_instances=1
        )

        logger.info(
            "Scheduled collection retry after infrastructure failure",
            extra={
                "event": "scheduled_collection_retry_scheduled",
                "retry_time": retry_time.isoformat(),
                "retry_in_minutes": 30
            }
        )


async def trigger_daily_collection_retry():
    """Retry function for failed scheduled collections.

    This function is identical to trigger_daily_collection but:
    1. Does NOT schedule another retry (prevents infinite loop)
    2. Logs retry attempt explicitly

    Called by APScheduler 30 minutes after a failed collection attempt.
    """
    logger.info(
        "Starting scheduled collection RETRY",
        extra={
            "event": "scheduled_collection_retry_start",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retry_attempt": 1
        }
    )

    async for db in get_db():
        try:
            # Check for existing in-progress collection
            stmt = select(DataCollection).where(
                DataCollection.status == "in_progress"
            )
            result = await db.execute(stmt)
            existing_collection = result.scalar_one_or_none()

            if existing_collection:
                logger.warning(
                    "Skipped retry - collection still in progress",
                    extra={
                        "event": "scheduled_collection_retry_skipped",
                        "existing_collection_id": str(existing_collection.id)
                    }
                )
                return

            # Create collection record
            collection = DataCollection(
                id=uuid4(),
                started_at=datetime.now(timezone.utc),
                status="in_progress"
            )
            db.add(collection)
            await db.commit()
            await db.refresh(collection)

            # Run collection
            await run_collection(collection.id)

            # Reset failure count on successful retry
            await reset_failure_count(db)

            logger.info(
                "Scheduled collection RETRY completed successfully",
                extra={
                    "event": "scheduled_collection_retry_complete",
                    "collection_id": str(collection.id)
                }
            )

        except Exception as e:
            logger.exception(
                "Scheduled collection RETRY failed (no more retries)",
                extra={
                    "event": "scheduled_collection_retry_failed",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )

            # Track failure (no more retries)
            await increment_failure_count(db)
            await check_failure_alert_threshold(db)

        break  # Exit async generator after first iteration


@router.post("/collect", response_model=CollectionResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_collection(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CollectionResponse:
    """Manually trigger data collection from all 4 APIs.

    Runs collectors in parallel for Reddit, YouTube, Google Trends, and SimilarWeb.
    Collection typically completes in 20-25 minutes.

    **Authentication:** Requires JWT token in Authorization header

    **Returns:**
        CollectionResponse with collection_id, status, and expected completion time

    **Raises:**
        409 Conflict: If collection already in progress
        401 Unauthorized: If JWT token is missing or invalid
    """
    # Check if collection already running
    stmt = select(DataCollection).where(
        DataCollection.status == "in_progress"
    )
    result = await db.execute(stmt)
    existing_collection = result.scalar_one_or_none()

    if existing_collection:
        logger.warning(
            "Collection already in progress",
            extra={
                "event": "collection_409_conflict",
                "existing_collection_id": str(existing_collection.id),
                "requested_by": current_user.username
            }
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Collection already in progress"
        )

    # Create new collection record
    collection = DataCollection(
        id=uuid4(),
        started_at=datetime.now(timezone.utc),
        status="in_progress"
    )
    db.add(collection)
    await db.commit()
    await db.refresh(collection)

    logger.info(
        "Collection triggered by user",
        extra={
            "event": "collection_triggered",
            "collection_id": str(collection.id),
            "user": current_user.username
        }
    )

    # Add background task
    background_tasks.add_task(
        run_collection,
        collection_id=collection.id
    )

    return CollectionResponse(
        collection_id=collection.id,
        status="in_progress",
        started_at=collection.started_at,
        message="Collection started. This will take approximately 20-25 minutes."
    )


@router.get("/collections/{collection_id}", response_model=CollectionStatusResponse)
async def get_collection_status(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CollectionStatusResponse:
    """Get status of a collection run.

    **Authentication:** Requires JWT token in Authorization header

    **Args:**
        collection_id: UUID of the collection to check

    **Returns:**
        CollectionStatusResponse with status, trends_found, duration, and errors

    **Raises:**
        404 Not Found: If collection ID doesn't exist
        401 Unauthorized: If JWT token is missing or invalid
    """
    # Get collection record
    stmt = select(DataCollection).where(DataCollection.id == collection_id)
    result = await db.execute(stmt)
    collection = result.scalar_one_or_none()

    if not collection:
        logger.warning(
            "Collection not found",
            extra={
                "event": "collection_not_found",
                "collection_id": str(collection_id),
                "requested_by": current_user.username
            }
        )
        raise HTTPException(status_code=404, detail="Collection not found")

    # Count trends
    trends_stmt = select(func.count(Trend.id)).where(Trend.collection_id == collection_id)
    trends_result = await db.execute(trends_stmt)
    trends_count = trends_result.scalar()

    # Calculate duration
    if collection.completed_at:
        duration = (collection.completed_at - collection.started_at).total_seconds() / 60
    else:
        duration = (datetime.now(timezone.utc) - collection.started_at).total_seconds() / 60

    logger.info(
        "Collection status requested",
        extra={
            "event": "collection_status_requested",
            "collection_id": str(collection_id),
            "status": collection.status,
            "requested_by": current_user.username
        }
    )

    return CollectionStatusResponse(
        collection_id=collection.id,
        status=collection.status,
        started_at=collection.started_at,
        completed_at=collection.completed_at,
        trends_found=trends_count,
        duration_minutes=round(duration, 2),
        errors=collection.errors
    )
