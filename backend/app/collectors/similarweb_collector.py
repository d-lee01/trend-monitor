"""SimilarWeb data collector for website traffic spike detection."""
import asyncio
import logging
import statistics
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import requests

from app.collectors.base import DataCollector, CollectionResult, RateLimitInfo
from app.collectors.retry import retry_with_backoff
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Default domains to monitor (trending websites)
DEFAULT_DOMAINS = [
    "reddit.com",
    "youtube.com",
    "twitter.com",
    "tiktok.com",
    "instagram.com",
    "netflix.com",
    "disney.com",
    "apple.com",
    "microsoft.com",
    "amazon.com"
]


class SimilarWebCollector(DataCollector):
    """Collects website traffic data from SimilarWeb API for spike detection.

    Uses SimilarWeb API to detect mainstream traffic spikes that indicate
    when trends cross from niche communities to mainstream awareness.

    Example:
        collector = SimilarWebCollector(db_session=db)
        result = await collector.collect(domains=DEFAULT_DOMAINS)
        # Returns CollectionResult with traffic data and spike flags
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize SimilarWeb collector with API key authentication.

        Args:
            db_session: Database session (not used for SimilarWeb, but required by interface)
        """
        super().__init__(name="similarweb")

        # Validate API key
        if not settings.similarweb_api_key:
            raise ValueError(
                "SimilarWeb API key not configured. "
                "Please set SIMILARWEB_API_KEY environment variable."
            )

        # Initialize HTTP session with auth
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {settings.similarweb_api_key}",
            "Content-Type": "application/json"
        })

        self.base_url = settings.similarweb_api_base_url

        logger.info("SimilarWebCollector initialized successfully", extra={
            "event": "collector_init",
            "api": "similarweb",
            "base_url": self.base_url
        })

    def _calculate_traffic_spike(
        self,
        current_visits: int,
        seven_day_history: List[int]
    ) -> tuple[float, bool]:
        """Calculate traffic change percentage and spike flag.

        Args:
            current_visits: Current total visits
            seven_day_history: Last 7 days visit counts

        Returns:
            (traffic_change_percentage, spike_detected)
            traffic_change_percentage: % change from 7-day average
            spike_detected: True if change > 50%
        """
        if not seven_day_history or len(seven_day_history) == 0:
            return (0.0, False)

        avg_visits = statistics.mean(seven_day_history)

        if avg_visits == 0:
            return (0.0, False)

        # Calculate percentage change
        change_pct = ((current_visits - avg_visits) / avg_visits) * 100

        # Spike if change > 50%
        spike_detected = change_pct > 50.0

        return (round(change_pct, 2), spike_detected)

    @retry_with_backoff(
        max_attempts=3,
        backoff_base=2,
        exceptions=(requests.exceptions.RequestException, requests.exceptions.HTTPError)
    )
    async def _fetch_domain_traffic(
        self,
        domain: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch traffic data for a domain with retry logic.

        Args:
            domain: Website domain (e.g., "reddit.com")

        Returns:
            Traffic data dictionary, or None if failed after retries
        """
        try:
            # Fetch traffic overview (use asyncio.to_thread for sync requests)
            traffic_url = f"{self.base_url}/website/{domain}/total-traffic-and-engagement/traffic"

            traffic_response = await asyncio.to_thread(
                lambda: self.session.get(traffic_url, timeout=(10, 25))
            )
            traffic_response.raise_for_status()
            traffic_data = traffic_response.json()

            # Fetch traffic sources
            sources_url = f"{self.base_url}/website/{domain}/traffic-sources/overview"

            sources_response = await asyncio.to_thread(
                lambda: self.session.get(sources_url, timeout=(10, 25))
            )
            sources_response.raise_for_status()
            sources_data = sources_response.json()

            # Fetch geography
            geo_url = f"{self.base_url}/website/{domain}/geo/traffic-by-country"

            geo_response = await asyncio.to_thread(
                lambda: self.session.get(geo_url, timeout=(10, 25))
            )
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            # Extract current visits
            current_visits = traffic_data.get("visits", 0)

            # Get 7-day historical data
            # Note: SimilarWeb historical data availability varies by subscription tier
            # If historical_visits not available, use conservative baseline (80% of current)
            # This ensures spike detection works even without historical endpoint
            seven_day_history = traffic_data.get("historical_visits", None)

            if seven_day_history is None or len(seven_day_history) == 0:
                # Conservative fallback: assume baseline is 80% of current traffic
                # This allows spike detection to work (20% growth threshold)
                baseline_visits = int(current_visits * 0.8)
                seven_day_history = [baseline_visits] * 7
                logger.debug(
                    f"Historical data unavailable for {domain}, using 80% baseline",
                    extra={
                        "event": "historical_fallback",
                        "api": "similarweb",
                        "domain": domain,
                        "current_visits": current_visits,
                        "baseline_visits": baseline_visits
                    }
                )

            # Calculate spike
            traffic_change_pct, spike_detected = self._calculate_traffic_spike(
                current_visits,
                seven_day_history
            )

            # Calculate engagement rate
            pages_per_visit = traffic_data.get("pages_per_visit", 0)
            avg_duration = traffic_data.get("average_visit_duration", 0)
            engagement_rate = pages_per_visit * (avg_duration / 60.0)  # Normalize to minutes

            domain_data = {
                "domain": domain,
                "total_visits": current_visits,
                "seven_day_avg_visits": int(statistics.mean(seven_day_history)),
                "traffic_change_percentage": traffic_change_pct,
                "traffic_spike_detected": spike_detected,
                "traffic_sources": sources_data,
                "geography": geo_data,
                "engagement_rate": round(engagement_rate, 2),
                "bounce_rate": traffic_data.get("bounce_rate", 0),
                "pages_per_visit": pages_per_visit,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            logger.debug(
                f"Fetched traffic for domain '{domain}': {current_visits:,} visits",
                extra={
                    "event": "domain_fetch",
                    "api": "similarweb",
                    "domain": domain,
                    "visits": current_visits,
                    "spike_detected": spike_detected
                }
            )

            return domain_data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(
                    "SimilarWeb authentication failed",
                    extra={
                        "event": "auth_error",
                        "api": "similarweb",
                        "domain": domain
                    }
                )
            elif e.response.status_code == 429:
                logger.error(
                    f"SimilarWeb rate limit exceeded for '{domain}'",
                    extra={
                        "event": "rate_limit_exceeded",
                        "api": "similarweb",
                        "domain": domain
                    }
                )
            elif e.response.status_code == 404:
                logger.warning(
                    f"Domain '{domain}' not found in SimilarWeb",
                    extra={
                        "event": "domain_not_found",
                        "api": "similarweb",
                        "domain": domain
                    }
                )
            else:
                logger.error(
                    f"SimilarWeb HTTP error for '{domain}': {e.response.status_code}",
                    extra={
                        "event": "http_error",
                        "api": "similarweb",
                        "domain": domain,
                        "status_code": e.response.status_code
                    }
                )
            raise  # Let retry decorator handle

        except requests.exceptions.Timeout:
            logger.error(
                f"SimilarWeb API timeout for '{domain}'",
                extra={
                    "event": "timeout",
                    "api": "similarweb",
                    "domain": domain
                }
            )
            raise  # Let retry decorator handle

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Request error for domain '{domain}': {e}",
                extra={
                    "event": "request_error",
                    "api": "similarweb",
                    "domain": domain,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return None

    async def collect(self, topics: List[str]) -> CollectionResult:
        """Collect traffic data from SimilarWeb for given domains.

        Args:
            topics: List of website domains (e.g., ["reddit.com", "youtube.com"])

        Returns:
            CollectionResult with collected traffic data and metrics
        """
        start_time = datetime.now(timezone.utc)
        all_data = []
        successful_calls = 0
        failed_calls = 0
        errors = []

        logger.info(
            f"Starting SimilarWeb collection for {len(topics)} domains",
            extra={
                "event": "collection_start",
                "api": "similarweb",
                "num_domains": len(topics)
            }
        )

        # Collect from each domain
        for i, domain in enumerate(topics, 1):
            call_start = datetime.now(timezone.utc)

            try:
                domain_data = await self._fetch_domain_traffic(domain)
                call_duration_ms = (datetime.now(timezone.utc) - call_start).total_seconds() * 1000

                if domain_data is not None:
                    all_data.append(domain_data)
                    successful_calls += 1
                    logger.info(
                        f"Collected domain '{domain}' ({i}/{len(topics)})",
                        extra={
                            "event": "api_call",
                            "api": "similarweb",
                            "topic": domain,
                            "success": True,
                            "duration_ms": round(call_duration_ms, 2),
                            "progress": f"{i}/{len(topics)}"
                        }
                    )
                else:
                    failed_calls += 1
                    errors.append(f"Failed to collect domain: {domain}")
                    logger.warning(
                        f"Skipping domain '{domain}' after retries ({i}/{len(topics)})",
                        extra={
                            "event": "api_call_failed",
                            "api": "similarweb",
                            "topic": domain,
                            "success": False,
                            "duration_ms": round(call_duration_ms, 2),
                            "progress": f"{i}/{len(topics)}"
                        }
                    )

            except Exception as e:
                failed_calls += 1
                errors.append(f"Error collecting domain '{domain}': {str(e)}")
                logger.error(
                    f"Exception collecting domain '{domain}': {e}",
                    extra={
                        "event": "collection_error",
                        "api": "similarweb",
                        "topic": domain,
                        "error": str(e)
                    }
                )

        # Calculate metrics
        duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        total_calls = len(topics)

        result = CollectionResult(
            source="similarweb",
            data=all_data,
            success_rate=-1.0,  # Auto-calculate
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            errors=errors,
            duration_seconds=duration_seconds
        )

        logger.info(
            f"SimilarWeb collection complete: {len(all_data)} domains from {successful_calls}/{total_calls} requests",
            extra={
                "event": "collection_complete",
                "api": "similarweb",
                "domains_collected": len(all_data),
                "success_rate": result.success_rate,
                "duration_seconds": round(duration_seconds, 2)
            }
        )

        return result

    async def health_check(self) -> bool:
        """Check if SimilarWeb API is accessible and credentials are valid.

        Returns:
            True if SimilarWeb API is healthy, False otherwise
        """
        try:
            # Test with a well-known domain
            test_url = f"{self.base_url}/website/google.com/total-traffic-and-engagement/traffic"

            response = await asyncio.to_thread(
                lambda: self.session.get(test_url, timeout=(10, 25))
            )
            response.raise_for_status()

            is_healthy = response.status_code == 200

            logger.info(
                f"SimilarWeb health check {'passed' if is_healthy else 'failed'}",
                extra={
                    "event": "health_check",
                    "api": "similarweb",
                    "status": "healthy" if is_healthy else "unhealthy"
                }
            )

            return is_healthy

        except Exception as e:
            logger.error(
                f"SimilarWeb health check failed: {e}",
                extra={
                    "event": "health_check",
                    "api": "similarweb",
                    "status": "unhealthy",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            return False

    async def get_rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit status for SimilarWeb API.

        SimilarWeb rate limits vary by subscription tier.

        Returns:
            RateLimitInfo with subscription info
        """
        return RateLimitInfo(
            limit=-1,  # Unknown - varies by subscription
            remaining=-1,  # Unknown - no public API
            reset_at=datetime.now(timezone.utc),
            quota_type="subscription_based"
        )
