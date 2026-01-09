"""Collection orchestrator for parallel multi-source data collection."""
import asyncio
import logging
from typing import List, Dict
from datetime import datetime, timezone
from uuid import UUID

from app.collectors.base import DataCollector, CollectionResult
from app.models.data_collection import DataCollection
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CollectionOrchestrator:
    """Orchestrates parallel data collection from multiple API sources.

    Coordinates multiple DataCollector instances to run in parallel using
    asyncio.gather(), tracking metrics and handling failures gracefully.

    Example:
        orchestrator = CollectionOrchestrator(
            collectors=[reddit_collector, youtube_collector],
            db_session=db
        )

        results = await orchestrator.collect_all(topics=["trending", "viral"])
        # Returns: {"reddit": CollectionResult(...), "youtube": CollectionResult(...)}
    """

    def __init__(
        self,
        collectors: List[DataCollector],
        db_session: AsyncSession
    ):
        """Initialize orchestrator with collectors.

        Args:
            collectors: List of DataCollector instances to coordinate
            db_session: Database session for tracking collection runs
        """
        self.collectors = collectors
        self.db_session = db_session

    async def collect_all(
        self,
        topics: List[str],
        collection_id: UUID
    ) -> Dict[str, CollectionResult]:
        """Collect data from all collectors in parallel.

        Uses asyncio.gather() with return_exceptions=True to ensure one
        collector's failure doesn't crash the entire collection.

        Args:
            topics: List of topics/keywords to collect
            collection_id: UUID of DataCollection record tracking this run

        Returns:
            Dictionary mapping collector name to CollectionResult

        Example:
            {
                "reddit": CollectionResult(source="reddit", data=[...], success_rate=0.95),
                "youtube": CollectionResult(source="youtube", data=[...], success_rate=1.0),
                "google_trends": CollectionResult(source="google_trends", data=[], success_rate=0.0)  # Failed
            }
        """
        start_time = datetime.now(timezone.utc)

        logger.info(
            f"Starting parallel collection with {len(self.collectors)} collectors",
            extra={
                "event": "collection_start",
                "collection_id": str(collection_id),
                "num_collectors": len(self.collectors),
                "num_topics": len(topics)
            }
        )

        # Create tasks for parallel execution
        tasks = [
            collector.collect(topics)
            for collector in self.collectors
        ]

        # Run all collectors in parallel with exception handling
        results_or_exceptions = await asyncio.gather(
            *tasks,
            return_exceptions=True  # Don't let one failure crash others
        )

        # Process results
        results = {}
        total_trends_found = 0
        failed_collectors = []

        for collector, result_or_exception in zip(self.collectors, results_or_exceptions):
            if isinstance(result_or_exception, Exception):
                # Collector raised unhandled exception
                logger.error(
                    f"Collector {collector.name} crashed: {str(result_or_exception)}",
                    extra={
                        "event": "collector_crash",
                        "collector": collector.name,
                        "error": str(result_or_exception),
                        "error_type": type(result_or_exception).__name__
                    }
                )

                # Create failed result for graceful degradation
                results[collector.name] = CollectionResult(
                    source=collector.name,
                    data=[],
                    success_rate=-1.0,  # Auto-calculate (will be 0.0)
                    total_calls=len(topics),
                    successful_calls=0,
                    failed_calls=len(topics),
                    errors=[str(result_or_exception)]
                )
                failed_collectors.append(collector.name)

            elif isinstance(result_or_exception, CollectionResult):
                # Collector completed successfully (may have partial failures)
                result = result_or_exception
                results[collector.name] = result

                # Count non-None data points
                trends_found = len([d for d in result.data if d is not None])
                total_trends_found += trends_found

                if result.success_rate < 1.0:
                    logger.warning(
                        f"Collector {collector.name} had partial failures: {result.success_rate:.1%} success rate",
                        extra={
                            "event": "partial_collection_failure",
                            "collector": collector.name,
                            "success_rate": result.success_rate,
                            "successful_calls": result.successful_calls,
                            "failed_calls": result.failed_calls
                        }
                    )

        # Calculate overall metrics
        duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        duration_minutes = duration_seconds / 60

        # Calculate API-specific metrics for database
        reddit_calls = results.get("reddit", CollectionResult("reddit", [])).total_calls
        youtube_quota = results.get("youtube", CollectionResult("youtube", [])).total_calls  # 1 unit per call
        google_trends_calls = results.get("google_trends", CollectionResult("google_trends", [])).total_calls

        logger.info(
            f"Collection complete: {total_trends_found} trends found in {duration_minutes:.1f} minutes",
            extra={
                "event": "collection_complete",
                "collection_id": str(collection_id),
                "duration_minutes": duration_minutes,
                "trends_found": total_trends_found,
                "failed_collectors": failed_collectors,
                "reddit_api_calls": reddit_calls,
                "youtube_api_quota_used": youtube_quota,
                "google_trends_api_calls": google_trends_calls
            }
        )

        return results
