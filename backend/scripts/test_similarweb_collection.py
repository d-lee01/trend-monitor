"""Manual integration test for SimilarWeb collector.

Usage:
    python -m scripts.test_similarweb_collection
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.collectors.similarweb_collector import SimilarWebCollector, DEFAULT_DOMAINS
from app.database import get_db


async def main():
    """Run SimilarWeb collection test."""
    print("=" * 60)
    print("SimilarWeb Collector Integration Test")
    print("=" * 60)

    # Get database session
    async for db in get_db():
        # Initialize collector
        print("\n1. Initializing SimilarWebCollector...")
        try:
            collector = SimilarWebCollector(db_session=db)
            print("   ✅ SimilarWebCollector initialized successfully")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            print("\n⚠️  Please set SIMILARWEB_API_KEY environment variable")
            return

        # Health check
        print("\n2. Running health check...")
        is_healthy = await collector.health_check()
        print(f"   Health check: {'✅ PASSED' if is_healthy else '❌ FAILED'}")

        if not is_healthy:
            print("\n⚠️  SimilarWeb API not accessible. Check API key.")
            return

        # Get rate limit info
        print("\n3. Checking rate limit info...")
        rate_info = await collector.get_rate_limit_info()
        print(f"   Quota type: {rate_info.quota_type}")

        # Collect from first 3 domains (faster test)
        test_domains = DEFAULT_DOMAINS[:3]
        print(f"\n4. Collecting from {len(test_domains)} domains...")
        print(f"   Domains: {', '.join(test_domains)}")

        result = await collector.collect(topics=test_domains)

        # Display results
        print("\n5. Collection Results:")
        print(f"   Source: {result.source}")
        print(f"   Domains collected: {len(result.data)}")
        print(f"   Success rate: {result.success_rate:.1%}")
        print(f"   Successful calls: {result.successful_calls}/{result.total_calls}")
        print(f"   Duration: {result.duration_seconds:.2f}s")

        if result.errors:
            print(f"\n   Errors:")
            for error in result.errors:
                print(f"   - {error}")

        # Show sample domains
        if result.data:
            print(f"\n6. Sample Domains:")
            for i, domain_data in enumerate(result.data[:3], 1):
                print(f"\n   Domain {i}:")
                print(f"   Name: {domain_data['domain']}")
                print(f"   Total visits: {domain_data['total_visits']:,}")
                print(f"   7-day average: {domain_data['seven_day_avg_visits']:,}")
                print(f"   Traffic change: {domain_data['traffic_change_percentage']:+.1f}%")
                print(f"   Spike detected: {'🔥 YES' if domain_data['traffic_spike_detected'] else '❌ NO'}")
                print(f"   Engagement rate: {domain_data['engagement_rate']:.2f}")

        print("\n" + "=" * 60)
        print("✅ Integration test complete!")
        print("=" * 60)

        break  # Exit after first db session


if __name__ == "__main__":
    asyncio.run(main())
