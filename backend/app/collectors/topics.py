"""Default topics for trend monitoring across all platforms."""

# Default list of 50 trending topics to monitor
# These topics are tracked across Reddit, YouTube, Google Trends, and SimilarWeb
DEFAULT_TOPICS = [
    # Technology & Innovation
    "artificial intelligence",
    "machine learning",
    "quantum computing",
    "blockchain",
    "cryptocurrency",
    "virtual reality",
    "augmented reality",
    "5G technology",
    "robotics",
    "autonomous vehicles",

    # Climate & Environment
    "climate change",
    "renewable energy",
    "solar power",
    "electric vehicles",
    "carbon emissions",
    "sustainability",
    "environmental policy",
    "green technology",

    # Science & Space
    "space exploration",
    "Mars mission",
    "SpaceX",
    "NASA",
    "gene editing",
    "CRISPR",
    "biotechnology",
    "medical research",

    # Business & Economy
    "stock market",
    "inflation",
    "interest rates",
    "real estate",
    "startup funding",
    "venture capital",
    "remote work",
    "gig economy",

    # Entertainment & Media
    "streaming services",
    "gaming",
    "esports",
    "metaverse",
    "NFT",
    "social media",
    "content creation",
    "influencer marketing",

    # Health & Wellness
    "mental health",
    "fitness",
    "nutrition",
    "healthcare",
    "telemedicine",
    "wellness trends",

    # Politics & Society
    "elections",
    "education reform"
]

# Verify we have exactly 50 topics
assert len(DEFAULT_TOPICS) == 50, f"Expected 50 topics, found {len(DEFAULT_TOPICS)}"
