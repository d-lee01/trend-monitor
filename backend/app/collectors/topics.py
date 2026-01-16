"""Topics for trend monitoring across different platforms.

Each platform uses a different set of topics optimized for its content type:
- YouTube: Categorized topics (travel, news, all) for Holiday Extras
- Reddit: 10 default subreddits for trending posts
- Google Trends: Generic trending search terms (disabled for now)
"""

from typing import Dict, List

# YouTube Topics with Categories - Curated for Holiday Extras (travel company)
# Categories: "travel", "news", or topic itself (for "all" section)

YOUTUBE_TOPICS_WITH_CATEGORIES: List[Dict[str, str]] = [
    # Core Travel Pain Points (What HX Solves)
    {"topic": "airport parking tips", "category": "travel"},
    {"topic": "airport lounge worth it", "category": "travel"},
    {"topic": "travel insurance explained", "category": "travel"},
    {"topic": "airport hotel deals", "category": "travel"},

    # Viral Travel Content (Jump On These)
    {"topic": "airport secrets", "category": "travel"},
    {"topic": "travel scam", "category": "travel"},
    {"topic": "things I regret travel", "category": "travel"},
    {"topic": "flight attendant tips", "category": "travel"},

    # UK-Specific + Seasonal Hooks
    {"topic": "UK holiday", "category": "travel"},
    {"topic": "half term holiday", "category": "travel"},
    {"topic": "Ryanair", "category": "travel"},

    # Travel News & Industry Updates
    {"topic": "travel news 2026", "category": "news"},
    {"topic": "airline news today", "category": "news"},
    {"topic": "airport strikes", "category": "news"},
    {"topic": "flight cancellations", "category": "news"},
]

# Extract just the topics for backward compatibility
YOUTUBE_TOPICS = [item["topic"] for item in YOUTUBE_TOPICS_WITH_CATEGORIES]

# Category mapping for quick lookup
YOUTUBE_TOPIC_CATEGORIES = {item["topic"]: item["category"] for item in YOUTUBE_TOPICS_WITH_CATEGORIES}

# Reddit Subreddits - Default subreddits to monitor for trending posts
REDDIT_SUBREDDITS = [
    "all",
    "popular",
    "videos",
    "movies",
    "television",
    "music",
    "news",
    "technology",
    "gaming",
    "sports"
]

# Default topics - Use YouTube topics as the primary list for orchestrator
# Reddit will override with its own subreddit list
DEFAULT_TOPICS = YOUTUBE_TOPICS

# Topic categories for UI grouping
YOUTUBE_CATEGORIES = {
    "Core Travel": YOUTUBE_TOPICS[0:4],
    "Viral Travel Content": YOUTUBE_TOPICS[4:8],
    "UK & Seasonal": YOUTUBE_TOPICS[8:11],
    "Travel News": YOUTUBE_TOPICS[11:15]
}

# Verify counts
assert len(YOUTUBE_TOPICS) == 15, f"Expected 15 YouTube topics, found {len(YOUTUBE_TOPICS)}"
assert len(REDDIT_SUBREDDITS) == 10, f"Expected 10 Reddit subreddits, found {len(REDDIT_SUBREDDITS)}"
