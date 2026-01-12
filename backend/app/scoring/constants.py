"""Tunable constants for scoring algorithms.

These constants are based on initial research and can be adjusted
based on real-world hit rate data. Track algorithm versions when
changing these values for A/B testing.

Version: v1.0 (Initial implementation)
"""

# Normalization thresholds (adjust based on historical data)
MAX_REDDIT_VELOCITY = 10000.0  # Max expected velocity score
MAX_YOUTUBE_TRACTION = 50000.0  # Max expected traction score
GOOGLE_TRENDS_Z_SCORE_RANGE = 6.0  # Z-score range (-3 to +3)
TRAFFIC_SPIKE_THRESHOLD = 50.0  # SimilarWeb traffic spike threshold (%)

# Momentum score weights (must sum to ~1.0)
REDDIT_WEIGHT = 0.33
YOUTUBE_WEIGHT = 0.33
GOOGLE_TRENDS_WEIGHT = 0.34
SIMILARWEB_BONUS_MULTIPLIER = 1.5

# Confidence thresholds
SIGNAL_PRESENCE_THRESHOLD = 50.0  # Score > 50 counts as "signal present"

# Default authority weights (used when actual values unavailable from API)
# These represent "established community" and "active creator" baselines
# In production, collectors should fetch actual values from Reddit/YouTube APIs
DEFAULT_SUBREDDIT_SIZE = 1000000  # Median large subreddit (~1M subscribers)
DEFAULT_CHANNEL_SUBSCRIBERS = 100000  # Median active channel (~100K subs)
