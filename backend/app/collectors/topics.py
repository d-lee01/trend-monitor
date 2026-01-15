"""Topics for trend monitoring across different platforms.

Each platform uses a different set of topics optimized for its content type:
- YouTube: 15 curated topics for Holiday Extras content opportunities
- Reddit: 10 default subreddits for trending posts
- Google Trends: Generic trending search terms (disabled for now)
"""

# YouTube Topics - Curated for Holiday Extras (travel company)
# Goal: Spot trending content to hijack, adapt, or react to for brand awareness
YOUTUBE_TOPICS = [
    # Core Travel Pain Points (What HX Solves)
    "airport parking tips",
    "airport lounge worth it",
    "travel insurance explained",
    "airport hotel deals",

    # Viral Travel Content (Jump On These)
    "airport secrets",
    "travel scam",
    "things I regret travel",
    "flight attendant tips",

    # Trending Formats to Hijack
    "rating tier list",
    "day in the life vlog",
    "expensive vs cheap",
    "what £100 gets you",

    # UK-Specific + Seasonal Hooks
    "UK holiday",
    "half term holiday",
    "Ryanair"
]

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
    "Trending Formats": YOUTUBE_TOPICS[8:12],
    "UK & Seasonal": YOUTUBE_TOPICS[12:15]
}

# Verify counts
assert len(YOUTUBE_TOPICS) == 15, f"Expected 15 YouTube topics, found {len(YOUTUBE_TOPICS)}"
assert len(REDDIT_SUBREDDITS) == 10, f"Expected 10 Reddit subreddits, found {len(REDDIT_SUBREDDITS)}"
