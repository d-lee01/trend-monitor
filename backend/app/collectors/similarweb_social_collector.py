"""SimilarWeb social traction collector - tracks companies gaining social media momentum."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import requests
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import DataCollector, CollectionResult
from app.collectors.retry import retry_with_backoff
from app.config import settings

logger = logging.getLogger(__name__)

# Categories to monitor for trending companies
DEFAULT_CATEGORIES = [
    "AI_Chatbots_and_Tools",
    "Computers_Electronics_and_Technology~Programming_and_Developer_Software",
    "E-commerce_and_Shopping~Marketplace",
    "Finance~Investing",
    "Health~Mental_Health",
    "Games~Video_Games_Consoles_and_Accessories"
]

# Social platforms to track for traction signals
KEY_SOCIAL_PLATFORMS = [
    "youtube.com",
    "reddit.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "discord.com",
    "instagram.com",
    "github.com",
    "linkedin.com",
    "facebook.com"
]

# Growth thresholds for flagging viral traction
VIRAL_GROWTH_THRESHOLD = 100.0  # 100% growth = viral
HIGH_GROWTH_THRESHOLD = 50.0    # 50% growth = high traction


class SimilarWebSocialCollector(DataCollector):
    """Collects social media traction data for top companies in trending categories.

    This collector identifies which companies are gaining viral social media traction
    by monitoring top sites in key categories and analyzing their social referral traffic.

    Key Features:
    - Tracks top 100 companies per category monthly
    - Analyzes social referral traffic from 10+ platforms
    - Flags explosive growth (>100% = viral, >50% = high traction)
    - Provides platform-specific insights (TikTok vs Discord vs GitHub)

    Example:
        collector = SimilarWebSocialCollector(db_session)
        result = await collector.collect(categories=DEFAULT_CATEGORIES)
        # Returns companies with social traction signals
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize SimilarWeb social traction collector.

        Args:
            db_session: Database session (not currently used, but required for interface consistency)
        """
        super().__init__(name="similarweb_social")

        # Validate API key
        if not settings.similarweb_api_key or settings.similarweb_api_key == "placeholder":
            raise ValueError(
                "SimilarWeb API key not configured. "
                "Set SIMILARWEB_API_KEY environment variable."
            )

        self.api_key = settings.similarweb_api_key
        self.base_url = "https://api.similarweb.com"

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            "api-key": self.api_key,
            "Accept": "application/json"
        })

        logger.info(
            "SimilarWeb social collector initialized",
            extra={
                "event": "collector_init",
                "api": "similarweb_social"
            }
        )

    @retry_with_backoff(max_attempts=3, backoff_base=2)
    async def _fetch_top_sites(self, category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch top sites in a category.

        Args:
            category: SimilarWeb category identifier
            limit: Number of top sites to retrieve (max 100)

        Returns:
            List of domains with rankings
        """
        # Get last month's data (SimilarWeb monthly updates)
        now = datetime.now(timezone.utc)
        # Use previous month since current month data may not be available
        if now.month == 1:
            year = now.year - 1
            month = 12
        else:
            year = now.year
            month = now.month - 1

        date_str = f"{year}-{month:02d}"

        url = f"{self.base_url}/v1/TopSites/{category}"
        params = {
            "country": "world",
            "start_date": date_str,
            "end_date": date_str,
            "limit": limit
        }

        logger.debug(
            f"Fetching top {limit} sites in category: {category}",
            extra={
                "event": "api_call_start",
                "api": "similarweb_social",
                "category": category,
                "date": date_str
            }
        )

        response = await asyncio.to_thread(
            lambda: self.session.get(url, params=params, timeout=(10, 30))
        )
        response.raise_for_status()
        data = response.json()

        # Extract site list
        sites = data.get("sites", [])

        logger.info(
            f"Retrieved {len(sites)} top sites from category: {category}",
            extra={
                "event": "top_sites_retrieved",
                "api": "similarweb_social",
                "category": category,
                "sites_count": len(sites)
            }
        )

        return sites

    @retry_with_backoff(max_attempts=3, backoff_base=2)
    async def _fetch_social_referrals(self, domain: str) -> Optional[Dict[str, Any]]:
        """Fetch social referral traffic for a domain.

        Args:
            domain: Website domain to analyze

        Returns:
            Dictionary with social platform traffic data, or None if failed
        """
        # Get last month's data
        now = datetime.now(timezone.utc)
        if now.month == 1:
            year = now.year - 1
            month = 12
        else:
            year = now.year
            month = now.month - 1

        date_str = f"{year}-{month:02d}"

        url = f"{self.base_url}/v1/website/{domain}/traffic-sources/social"
        params = {
            "country": "world",
            "start_date": date_str,
            "end_date": date_str
        }

        try:
            response = await asyncio.to_thread(
                lambda: self.session.get(url, params=params, timeout=(10, 30))
            )
            response.raise_for_status()
            data = response.json()

            return data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(
                    f"Domain '{domain}' not found in SimilarWeb",
                    extra={
                        "event": "domain_not_found",
                        "api": "similarweb_social",
                        "domain": domain
                    }
                )
                return None
            raise

    def _analyze_social_traction(
        self,
        domain: str,
        rank: int,
        category: str,
        social_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze social traction signals from referral data.

        Args:
            domain: Website domain
            rank: Domain's rank in category
            category: Category name
            social_data: Social referrals API response

        Returns:
            Dictionary with traction analysis and signals
        """
        social_sources = social_data.get("social", [])
        total_visits = social_data.get("visits", 0)

        # Extract key platform metrics
        platform_metrics = {}
        total_social_share = 0.0
        viral_platforms = []
        high_growth_platforms = []

        for source in social_sources:
            page = source.get("page", "")
            share = source.get("share", 0.0) * 100  # Convert to percentage
            change = source.get("change", 0.0) * 100  # Convert to percentage

            # Track key social platforms
            if page in KEY_SOCIAL_PLATFORMS:
                platform_metrics[page] = {
                    "share": round(share, 3),
                    "growth": round(change, 1)
                }
                total_social_share += share

                # Flag viral growth
                if change >= VIRAL_GROWTH_THRESHOLD:
                    viral_platforms.append({
                        "platform": page,
                        "growth": round(change, 1),
                        "share": round(share, 3)
                    })
                elif change >= HIGH_GROWTH_THRESHOLD:
                    high_growth_platforms.append({
                        "platform": page,
                        "growth": round(change, 1),
                        "share": round(share, 3)
                    })

        # Determine overall traction signal
        if viral_platforms:
            trend_signal = "VIRAL"
            signal_reason = f"{len(viral_platforms)} platform(s) with >100% growth"
        elif len(high_growth_platforms) >= 2:
            trend_signal = "HIGH_TRACTION"
            signal_reason = f"{len(high_growth_platforms)} platforms with >50% growth"
        elif high_growth_platforms:
            trend_signal = "GROWING"
            signal_reason = f"{len(high_growth_platforms)} platform with >50% growth"
        else:
            trend_signal = "STABLE"
            signal_reason = "No significant social growth detected"

        result = {
            "domain": domain,
            "rank": rank,
            "category": category,
            "total_visits": total_visits,
            "total_social_share": round(total_social_share, 2),
            "platform_metrics": platform_metrics,
            "viral_platforms": viral_platforms,
            "high_growth_platforms": high_growth_platforms,
            "trend_signal": trend_signal,
            "signal_reason": signal_reason,
            "collected_at": datetime.now(timezone.utc).isoformat()
        }

        logger.info(
            f"Analyzed social traction for {domain}: {trend_signal}",
            extra={
                "event": "traction_analyzed",
                "api": "similarweb_social",
                "domain": domain,
                "signal": trend_signal,
                "viral_count": len(viral_platforms),
                "high_growth_count": len(high_growth_platforms)
            }
        )

        return result

    async def collect(self, topics: List[str] = None) -> CollectionResult:
        """Collect social traction data for top companies in specified categories.

        Note: This collector uses categories (not topics). The topics parameter
        is accepted for interface consistency with other collectors but is ignored.

        Args:
            topics: Ignored (required for DataCollector interface consistency)

        Returns:
            CollectionResult with social traction analysis for trending companies
        """
        # Use default categories (topics parameter is ignored)
        categories = DEFAULT_CATEGORIES

        start_time = datetime.now(timezone.utc)
        all_data = []
        successful_calls = 0
        failed_calls = 0
        errors = []

        logger.info(
            f"Starting social traction collection for {len(categories)} categories",
            extra={
                "event": "collection_start",
                "api": "similarweb_social",
                "num_categories": len(categories)
            }
        )

        for category in categories:
            try:
                # Get top 20 sites in category
                top_sites = await self._fetch_top_sites(category, limit=20)
                successful_calls += 1

                # For each site, get social referral data
                for site_data in top_sites:
                    domain = site_data.get("site", site_data.get("domain", ""))
                    rank = site_data.get("rank", 0)

                    if not domain:
                        continue

                    try:
                        social_data = await self._fetch_social_referrals(domain)

                        if social_data:
                            successful_calls += 1

                            # Analyze traction signals
                            traction_analysis = self._analyze_social_traction(
                                domain=domain,
                                rank=rank,
                                category=category,
                                social_data=social_data
                            )

                            # Only include domains with interesting signals
                            if traction_analysis["trend_signal"] in ["VIRAL", "HIGH_TRACTION", "GROWING"]:
                                all_data.append(traction_analysis)

                                logger.info(
                                    f"Found trending company: {domain} ({traction_analysis['trend_signal']})",
                                    extra={
                                        "event": "trending_company_found",
                                        "api": "similarweb_social",
                                        "domain": domain,
                                        "signal": traction_analysis["trend_signal"],
                                        "category": category
                                    }
                                )
                        else:
                            failed_calls += 1
                            logger.debug(
                                f"No social data available for {domain}",
                                extra={
                                    "event": "no_social_data",
                                    "api": "similarweb_social",
                                    "domain": domain
                                }
                            )

                        # Rate limiting: small delay between requests
                        await asyncio.sleep(0.5)

                    except Exception as e:
                        failed_calls += 1
                        error_msg = f"Failed to collect social data for {domain}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(
                            error_msg,
                            extra={
                                "event": "social_collection_failed",
                                "api": "similarweb_social",
                                "domain": domain,
                                "error": str(e)
                            },
                            exc_info=True
                        )

            except Exception as e:
                failed_calls += 1
                error_msg = f"Failed to fetch top sites for category {category}: {str(e)}"
                errors.append(error_msg)
                logger.error(
                    error_msg,
                    extra={
                        "event": "category_collection_failed",
                        "api": "similarweb_social",
                        "category": category,
                        "error": str(e)
                    },
                    exc_info=True
                )

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        total_calls = successful_calls + failed_calls

        logger.info(
            f"Social traction collection complete: {len(all_data)} trending companies found",
            extra={
                "event": "collection_complete",
                "api": "similarweb_social",
                "trending_companies": len(all_data),
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "duration_seconds": round(duration, 2)
            }
        )

        return CollectionResult(
            source="similarweb_social",
            data=all_data,
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            errors=errors,
            duration_seconds=duration
        )
