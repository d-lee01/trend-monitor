"""Manual integration test for Google Trends collector.

Usage:
    python -m scripts.test_google_trends_collection
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.collectors.google_trends_collector import GoogleTrendsCollector, DEFAULT_TOPICS
from app.database import get_db


async def main():
    """Run Google Trends collection test."""
    print("=" * 60)
    print("Google Trends Collector Integration Test")
    print("=" * 60)

    # Get database session
    async for db in get_db():
        # Initialize collector
        print("\n1. Initializing GoogleTrendsCollector...")
        try:
            collector = GoogleTrendsCollector(db_session=db)
            print("   ✅ GoogleTrendsCollector initialized successfully")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            return

        # Health check
        print("\n2. Running health check...")
        is_healthy = await collector.health_check()
        print(f"   Health check: {'✅ PASSED' if is_healthy else '❌ FAILED'}")

        if not is_healthy:
            print("\n⚠️  Google Trends not accessible via PyTrends.")
            print("   This may be temporary throttling or a library issue.")
            return

        # Get rate limit info
        print("\n3. Checking rate limit info...")
        rate_info = await collector.get_rate_limit_info()
        print(f"   Rate limit: {rate_info.limit}s per request")
        print(f"   Quota type: {rate_info.quota_type}")

        # Collect from first 3 topics (faster test)
        test_topics = DEFAULT_TOPICS[:3]
        print(f"\n4. Collecting from {len(test_topics)} topics...")
        print(f"   Topics: {', '.join(test_topics)}")
        print(f"   ⚠️  This will take ~3 minutes (60s delay between requests)")

        result = await collector.collect(topics=test_topics)

        # Display results
        print("\n5. Collection Results:")
        print(f"   Source: {result.source}")
        print(f"   Topics collected: {len(result.data)}")
        print(f"   Success rate: {result.success_rate:.1%}")
        print(f"   Successful calls: {result.successful_calls}/{result.total_calls}")
        print(f"   Duration: {result.duration_seconds:.2f}s ({result.duration_seconds/60:.1f} min)")

        if result.errors:
            print(f"\n   Errors:")
            for error in result.errors:
                print(f"   - {error}")

        # Show sample topics
        if result.data:
            print(f"\n6. Sample Topics:")
            for i, topic_data in enumerate(result.data[:3], 1):
                print(f"\n   Topic {i}:")
                print(f"   Name: {topic_data['topic']}")
                print(f"   Current interest: {topic_data['current_interest']}/100")
                print(f"   7-day average: {topic_data['average_interest']:.1f}")
                print(f"   Spike detected: {'🔥 YES' if topic_data['spike_detected'] else '❌ NO'}")
                print(f"   Spike score: {topic_data['spike_score']:.1f}")
                print(f"   History: {topic_data['seven_day_history']}")

        print("\n" + "=" * 60)
        print("✅ Integration test complete!")
        print("=" * 60)

        break  # Exit after first db session


if __name__ == "__main__":
    asyncio.run(main())
