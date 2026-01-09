"""Manual integration test for Reddit collector.

Usage:
    python -m scripts.test_reddit_collection
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.collectors.reddit_collector import RedditCollector, DEFAULT_SUBREDDITS


async def main():
    """Run Reddit collection test."""
    print("=" * 60)
    print("Reddit Collector Integration Test")
    print("=" * 60)

    # Initialize collector
    print("\n1. Initializing RedditCollector...")
    collector = RedditCollector()

    # Health check
    print("\n2. Running health check...")
    is_healthy = await collector.health_check()
    print(f"   Health check: {'✅ PASSED' if is_healthy else '❌ FAILED'}")

    if not is_healthy:
        print("\n⚠️  Reddit API not accessible. Check credentials.")
        return

    # Get rate limit info
    print("\n3. Checking rate limit...")
    rate_info = await collector.get_rate_limit_info()
    print(f"   Rate limit: {rate_info.remaining}/{rate_info.limit} remaining")

    # Collect from first 3 subreddits (faster test)
    test_subreddits = DEFAULT_SUBREDDITS[:3]
    print(f"\n4. Collecting from {len(test_subreddits)} subreddits...")
    print(f"   Subreddits: {', '.join(test_subreddits)}")

    result = await collector.collect(topics=test_subreddits)

    # Display results
    print("\n5. Collection Results:")
    print(f"   Source: {result.source}")
    print(f"   Posts collected: {len(result.data)}")
    print(f"   Success rate: {result.success_rate:.1%}")
    print(f"   Successful calls: {result.successful_calls}/{result.total_calls}")
    print(f"   Duration: {result.duration_seconds:.2f}s")

    if result.errors:
        print(f"\n   Errors:")
        for error in result.errors:
            print(f"   - {error}")

    # Show sample posts
    if result.data:
        print(f"\n6. Sample Posts:")
        for i, post in enumerate(result.data[:5], 1):
            print(f"\n   Post {i}:")
            print(f"   Title: {post['title'][:60]}...")
            print(f"   Subreddit: r/{post['subreddit_name']}")
            print(f"   Score: {post['score']:,} | Comments: {post['num_comments']:,}")
            print(f"   Upvote ratio: {post['upvote_ratio']:.1%}")
            print(f"   Hours since post: {post['hours_since_post']:.1f}h")

    print("\n" + "=" * 60)
    print("✅ Integration test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
