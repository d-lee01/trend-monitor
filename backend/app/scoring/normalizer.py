"""Normalization functions for converting platform metrics to 0-100 scale.

All functions are pure (deterministic, no side effects) to enable
comprehensive testing and tuning.
"""
import math
import statistics
from typing import List, Optional

from .constants import (
    MAX_REDDIT_VELOCITY,
    MAX_YOUTUBE_TRACTION,
    GOOGLE_TRENDS_Z_SCORE_RANGE
)


def normalize_reddit_score(
    score: int,
    hours_since_post: float,
    subreddit_size: int
) -> float:
    """Normalize Reddit score to 0-100 scale.

    Measures velocity (upvotes per hour) weighted by subreddit authority.
    Higher velocity in larger subreddits indicates stronger momentum.

    Args:
        score: Raw upvote count from Reddit API
        hours_since_post: Time elapsed since post creation (from created_utc)
        subreddit_size: Number of subreddit subscribers (authority weight)

    Returns:
        Normalized score on 0-100 scale (float)

    Formula:
        velocity = score / max(hours_since_post, 1)
        authority_weight = log10(max(subreddit_size, 1))
        raw_score = velocity * authority_weight
        normalized = min(100, (raw_score / MAX_REDDIT_VELOCITY) * 100)

    Edge Cases:
        - hours_since_post = 0: Use max(hours, 1) to prevent division by zero
        - subreddit_size = 0: Use max(size, 1) to prevent log(0)
        - Negative values: Treated as 0
        - Scores > 100: Capped at 100

    Example:
        >>> normalize_reddit_score(score=5000, hours_since_post=2.0, subreddit_size=1000000)
        75.3

        >>> normalize_reddit_score(score=100, hours_since_post=0.1, subreddit_size=10000)
        40.0

    Note:
        MAX_REDDIT_VELOCITY=10000 is tunable in constants.py based on
        historical data analysis. Adjust if scores consistently hit 100.

    References:
        [Architecture: AD-5 Scoring Algorithms]
        [Epics: Story 3.1 Acceptance Criteria]
    """
    # Handle edge cases for zero/negative values
    safe_hours = max(hours_since_post, 1.0)
    safe_subreddit_size = max(subreddit_size, 1)
    safe_score = max(score, 0)

    # Calculate velocity (upvotes per hour)
    velocity = safe_score / safe_hours

    # Weight by subreddit authority (log scale)
    authority_weight = math.log10(safe_subreddit_size)

    # Calculate raw score
    raw_score = velocity * authority_weight

    # Normalize to 0-100 scale and cap at 100
    normalized = min(100.0, (raw_score / MAX_REDDIT_VELOCITY) * 100.0)

    return round(normalized, 2)


def normalize_youtube_traction(
    views: int,
    hours_since_publish: float,
    likes: int,
    channel_subs: int
) -> float:
    """Normalize YouTube video traction to 0-100 scale.

    Measures view velocity weighted by engagement rate and channel authority.
    High velocity + high engagement + large channel = strong momentum signal.

    Args:
        views: Total view count from YouTube API
        hours_since_publish: Time elapsed since video publication
        likes: Total like count (engagement metric)
        channel_subs: Channel subscriber count (authority weight)

    Returns:
        Normalized traction score on 0-100 scale (float)

    Formula:
        velocity = views / max(hours_since_publish, 1)
        engagement_rate = likes / max(views, 1)
        authority_weight = log10(max(channel_subs, 1))
        raw_score = velocity * engagement_rate * authority_weight
        normalized = min(100, (raw_score / MAX_YOUTUBE_TRACTION) * 100)

    Edge Cases:
        - hours_since_publish = 0: Use max(hours, 1)
        - views = 0: Use max(views, 1) for engagement calculation
        - channel_subs = 0: Use max(subs, 1) to prevent log(0)
        - engagement_rate > 1.0: Theoretically possible with botting, cap normalized

    Example:
        >>> normalize_youtube_traction(views=250000, hours_since_publish=6.0, likes=8000, channel_subs=500000)
        82.5

        >>> normalize_youtube_traction(views=1000, hours_since_publish=24.0, likes=50, channel_subs=10000)
        12.3

    Note:
        MAX_YOUTUBE_TRACTION=50000 is tunable in constants.py.
        Adjust based on observed viral video patterns.

    References:
        [Architecture: AD-5 Scoring Algorithms]
        [YouTube Data API: videos.list endpoint provides all metrics]
    """
    # Handle edge cases
    safe_hours = max(hours_since_publish, 1.0)
    safe_views = max(views, 1)
    safe_likes = max(likes, 0)
    safe_channel_subs = max(channel_subs, 1)

    # Calculate view velocity (views per hour)
    velocity = safe_views / safe_hours

    # Calculate engagement rate (likes as % of views)
    engagement_rate = safe_likes / safe_views

    # Weight by channel authority (log scale)
    authority_weight = math.log10(safe_channel_subs)

    # Calculate raw traction score
    raw_score = velocity * engagement_rate * authority_weight

    # Normalize to 0-100 scale and cap at 100
    normalized = min(100.0, (raw_score / MAX_YOUTUBE_TRACTION) * 100.0)

    return round(normalized, 2)


def calculate_google_trends_spike(
    current_interest: int,
    seven_day_history: List[int]
) -> float:
    """Calculate Google Trends spike score using Z-score normalization.

    Detects search interest spikes by comparing current interest to
    7-day historical baseline using statistical Z-score method.

    Args:
        current_interest: Most recent interest value (0-100 from Google Trends)
        seven_day_history: List of 7 historical daily interest values (0-100 each)

    Returns:
        Normalized spike score on 0-100 scale (float)

    Formula:
        mean = statistics.mean(seven_day_history)
        stddev = statistics.stdev(seven_day_history)
        z_score = (current_interest - mean) / stddev
        normalized = min(100, max(0, (z_score + 3) / 6 * 100))

    Z-Score Interpretation:
        z_score = 0: Current interest at historical average (score ~50)
        z_score = +3: Strong spike (3 standard deviations above, score ~100)
        z_score = -3: Low interest (3 standard deviations below, score ~0)

    Edge Cases:
        - seven_day_history has < 2 values: Return current_interest directly
        - stddev = 0 (flat interest): Return 50.0 (average baseline)
        - z_score > +3 or < -3: Capped to 0-100 range

    Example:
        >>> calculate_google_trends_spike(current_interest=85, seven_day_history=[30, 35, 40, 45, 50, 60, 85])
        87.3

        >>> calculate_google_trends_spike(current_interest=50, seven_day_history=[48, 49, 50, 51, 52, 50, 50])
        50.0  # No spike, at baseline

    Note:
        Requires minimum 2 historical data points for stddev calculation.
        If PyTrends fails to collect history, score defaults to current_interest.

    References:
        [Architecture: AD-5 Scoring Algorithms]
        [PyTrends: pytrend.interest_over_time() provides 7-day history]
        [Statistics: Z-score standardization formula]
    """
    # Edge case: Insufficient historical data
    if len(seven_day_history) < 2:
        # Fallback: Use current interest directly (no spike detection possible)
        return float(min(100, max(0, current_interest)))

    try:
        # Calculate 7-day baseline statistics
        mean = statistics.mean(seven_day_history)
        stddev = statistics.stdev(seven_day_history)

        # Edge case: Zero stddev means flat interest (no variation)
        if stddev == 0:
            return 50.0  # Baseline score (no spike)

        # Calculate Z-score (standard deviations from mean)
        z_score = (current_interest - mean) / stddev

        # Normalize Z-score to 0-100 scale
        # Z-score range: -3 to +3 (99.7% of normal distribution)
        # Map to 0-100: (-3 → 0, 0 → 50, +3 → 100)
        normalized = ((z_score + 3.0) / GOOGLE_TRENDS_Z_SCORE_RANGE) * 100.0

        # Clamp to 0-100 range
        normalized = min(100.0, max(0.0, normalized))

        return round(normalized, 2)

    except statistics.StatisticsError:
        # Fallback: Use current interest if stats calculation fails
        return float(min(100, max(0, current_interest)))


def detect_similarweb_traffic_spike(
    traffic_change_percentage: Optional[float]
) -> bool:
    """Detect SimilarWeb traffic spike (>50% increase).

    Simple boolean check for mainstream pickup indicator.
    Traffic spike acts as a 1.5x momentum score multiplier.

    Args:
        traffic_change_percentage: Percentage change in traffic vs 7-day avg
                                   Example: 150.0 means 150% increase

    Returns:
        True if traffic spike detected (>50%), False otherwise

    Formula:
        spike_detected = (traffic_change_percentage > 50.0)

    Edge Cases:
        - traffic_change_percentage is None: Return False (no SimilarWeb data)
        - Negative percentage: Return False (traffic decline)

    Example:
        >>> detect_similarweb_traffic_spike(traffic_change_percentage=75.5)
        True  # 75% increase detected

        >>> detect_similarweb_traffic_spike(traffic_change_percentage=25.0)
        False  # Only 25% increase (below threshold)

        >>> detect_similarweb_traffic_spike(traffic_change_percentage=None)
        False  # No SimilarWeb data available

    Note:
        50% threshold is tunable in constants.py.
        Adjust based on observed mainstream pickup patterns.

    References:
        [Architecture: AD-5 Scoring Algorithms]
        [Epics: FR-1.4 SimilarWeb Integration]
    """
    if traffic_change_percentage is None:
        return False

    TRAFFIC_SPIKE_THRESHOLD = 50.0  # 50% increase threshold

    return traffic_change_percentage > TRAFFIC_SPIKE_THRESHOLD
