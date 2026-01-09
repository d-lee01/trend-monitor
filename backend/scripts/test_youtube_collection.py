"""Manual integration test for YouTube collector.

Usage:
    python -m scripts.test_youtube_collection
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.collectors.youtube_collector import YouTubeCollector, DEFAULT_CHANNELS
from app.database import get_db


async def main():
    """Run YouTube collection test."""
    print("=" * 60)
    print("YouTube Collector Integration Test")
    print("=" * 60)

    # Get database session
    async for db in get_db():
        # Initialize collector
        print("\n1. Initializing YouTubeCollector...")
        try:
            collector = YouTubeCollector(db_session=db)
            print("   ✅ YouTubeCollector initialized successfully")
        except ValueError as e:
            print(f"   ❌ FAILED: {e}")
            print("\n⚠️  Please set YOUTUBE_API_KEY environment variable")
            return

        # Health check
        print("\n2. Running health check...")
        is_healthy = await collector.health_check()
        print(f"   Health check: {'✅ PASSED' if is_healthy else '❌ FAILED'}")

        if not is_healthy:
            print("\n⚠️  YouTube API not accessible. Check API key.")
            return

        # Get rate limit info
        print("\n3. Checking quota usage...")
        rate_info = await collector.get_rate_limit_info()
        print(f"   Quota: {rate_info.remaining}/{rate_info.limit} remaining")
        print(f"   Quota used: {rate_info.limit - rate_info.remaining}")

        # Warn if quota high
        if rate_info.remaining < 2000:
            print(f"   ⚠️  WARNING: Low quota remaining ({rate_info.remaining})")

        # Collect from first 3 channels (faster test)
        test_channels = DEFAULT_CHANNELS[:3]
        print(f"\n4. Collecting from {len(test_channels)} channels...")
        print(f"   Channels: {', '.join(ch[:20] + '...' for ch in test_channels)}")

        result = await collector.collect(topics=test_channels)

        # Display results
        print("\n5. Collection Results:")
        print(f"   Source: {result.source}")
        print(f"   Videos collected: {len(result.data)}")
        print(f"   Success rate: {result.success_rate:.1%}")
        print(f"   Successful calls: {result.successful_calls}/{result.total_calls}")
        print(f"   Duration: {result.duration_seconds:.2f}s")

        if result.errors:
            print(f"\n   Errors:")
            for error in result.errors:
                print(f"   - {error}")

        # Show sample videos
        if result.data:
            print(f"\n6. Sample Videos:")
            for i, video in enumerate(result.data[:5], 1):
                print(f"\n   Video {i}:")
                print(f"   Title: {video['video_title'][:60]}...")
                print(f"   Channel: {video['channel_title']}")
                print(f"   Views: {video['view_count']:,} | Likes: {video['like_count']:,}")
                print(f"   Engagement: {video['engagement_rate']:.2%}")
                print(f"   Hours since publish: {video['hours_since_publish']:.1f}h")
                print(f"   Subscribers: {video['channel_subscriber_count']:,}")

        # Check quota usage again
        print("\n7. Final Quota Check:")
        final_rate_info = await collector.get_rate_limit_info()
        quota_used = final_rate_info.limit - final_rate_info.remaining
        print(f"   Quota used: {quota_used}")
        print(f"   Remaining: {final_rate_info.remaining}/{final_rate_info.limit}")

        print("\n" + "=" * 60)
        print("✅ Integration test complete!")
        print("=" * 60)

        break  # Exit after first db session


if __name__ == "__main__":
    asyncio.run(main())
