"""Cross-platform momentum score calculation.

Combines normalized scores from all platforms into a single
momentum score with confidence level indicator.
"""
from typing import Optional, Tuple

from .constants import (
    REDDIT_WEIGHT,
    YOUTUBE_WEIGHT,
    GOOGLE_TRENDS_WEIGHT,
    SIMILARWEB_BONUS_MULTIPLIER,
    SIGNAL_PRESENCE_THRESHOLD
)


def calculate_momentum_score(
    reddit_velocity: float,
    youtube_traction: float,
    google_trends_spike: float,
    similarweb_traffic_spike: bool
) -> Tuple[float, str]:
    """Calculate cross-platform momentum score with confidence level.

    Combines normalized platform scores using weighted average,
    with SimilarWeb bonus multiplier for mainstream pickup.

    Args:
        reddit_velocity: Reddit velocity score (0-100)
        youtube_traction: YouTube traction score (0-100)
        google_trends_spike: Google Trends spike score (0-100)
        similarweb_traffic_spike: SimilarWeb traffic spike detected (bool)

    Returns:
        Tuple of (momentum_score, confidence_level)
        - momentum_score: Float 0-150 (150 max with SimilarWeb bonus)
        - confidence_level: 'high', 'medium', 'low', or 'unknown'

    Formula:
        base_score = (reddit * 0.33 + youtube * 0.33 + google_trends * 0.34)
        if similarweb_traffic_spike:
            final_score = base_score * 1.5
        else:
            final_score = base_score

    Confidence Levels:
        - high (🔥): All 4 platform signals present (each > 50)
        - medium (⚡): 2-3 platform signals present
        - low (👀): Only 1 platform signal present
        - unknown: No signals present (all scores < 50)

    Example:
        >>> calculate_momentum_score(reddit_velocity=78.0, youtube_traction=82.0,
        ...                          google_trends_spike=85.0, similarweb_traffic_spike=True)
        (122.25, 'high')  # All 4 signals, bonus applied

        >>> calculate_momentum_score(reddit_velocity=65.0, youtube_traction=30.0,
        ...                          google_trends_spike=45.0, similarweb_traffic_spike=False)
        (46.7, 'low')  # Only Reddit signal strong

    Note:
        Weights (0.33, 0.33, 0.34) are tunable in constants.py.
        SimilarWeb bonus (1.5x) amplifies score when mainstream pickup detected.

    References:
        [Architecture: AD-5 Scoring Algorithms]
        [Epics: FR-2.3 Composite Score Calculation]
    """
    # Calculate weighted average of platform scores
    base_score = (
        reddit_velocity * REDDIT_WEIGHT +
        youtube_traction * YOUTUBE_WEIGHT +
        google_trends_spike * GOOGLE_TRENDS_WEIGHT
    )

    # Apply SimilarWeb bonus multiplier if traffic spike detected
    if similarweb_traffic_spike:
        final_score = base_score * SIMILARWEB_BONUS_MULTIPLIER
    else:
        final_score = base_score

    # Determine confidence level based on signal convergence
    signals_present = sum([
        reddit_velocity > SIGNAL_PRESENCE_THRESHOLD,
        youtube_traction > SIGNAL_PRESENCE_THRESHOLD,
        google_trends_spike > SIGNAL_PRESENCE_THRESHOLD,
        similarweb_traffic_spike  # Boolean already True/False
    ])

    if signals_present >= 4:
        confidence = 'high'
    elif signals_present >= 2:
        confidence = 'medium'
    elif signals_present >= 1:
        confidence = 'low'
    else:
        confidence = 'unknown'

    return (round(final_score, 2), confidence)


def calculate_momentum_score_safe(
    reddit_velocity: Optional[float],
    youtube_traction: Optional[float],
    google_trends_spike: Optional[float],
    similarweb_traffic_spike: bool
) -> Tuple[float, str]:
    """Calculate momentum score with graceful handling of missing data.

    Safely handles cases where one or more platform APIs failed to
    collect data. Calculates score using renormalized weights based on
    available platforms.

    Args:
        reddit_velocity: Reddit velocity score (0-100) or None if unavailable
        youtube_traction: YouTube traction score (0-100) or None if unavailable
        google_trends_spike: Google Trends spike score (0-100) or None if unavailable
        similarweb_traffic_spike: SimilarWeb traffic spike detected (bool)

    Returns:
        Tuple of (momentum_score, confidence_level)

    Graceful Degradation:
        - Weights are renormalized based on available platforms
        - If Reddit + YouTube + Google: Use original weights (0.33, 0.33, 0.34)
        - If 2 platforms available: Renormalize their weights to sum to 1.0
        - If 1 platform available: Use that score directly (weight = 1.0)
        - If 0 platforms available: Return (0.0, 'unknown')

    Example:
        >>> calculate_momentum_score_safe(reddit_velocity=75.0, youtube_traction=None,
        ...                               google_trends_spike=80.0, similarweb_traffic_spike=False)
        (77.5, 'medium')  # Weights renormalized: Reddit=0.49, Google=0.51

        >>> calculate_momentum_score_safe(reddit_velocity=None, youtube_traction=None,
        ...                               google_trends_spike=None, similarweb_traffic_spike=False)
        (0.0, 'unknown')  # All platforms failed

    Note:
        This function enables graceful degradation per AD-9 architecture requirement.
        Renormalized weights maintain the proportional contribution of each platform.

    References:
        [Architecture: AD-9 Error Handling and Graceful Degradation]
        [Epics: Story 2.1 Graceful Degradation Requirements]
    """
    # Build list of (score, weight) tuples for available platforms
    available_platforms = []
    if reddit_velocity is not None:
        available_platforms.append((reddit_velocity, REDDIT_WEIGHT))
    if youtube_traction is not None:
        available_platforms.append((youtube_traction, YOUTUBE_WEIGHT))
    if google_trends_spike is not None:
        available_platforms.append((google_trends_spike, GOOGLE_TRENDS_WEIGHT))

    # Edge case: No platform data available
    if len(available_platforms) == 0:
        return (0.0, 'unknown')

    # Calculate total weight of available platforms
    total_weight = sum(weight for _, weight in available_platforms)

    # Calculate weighted average with renormalized weights
    base_score = sum(score * (weight / total_weight) for score, weight in available_platforms)

    # Apply SimilarWeb bonus if applicable
    if similarweb_traffic_spike:
        final_score = base_score * SIMILARWEB_BONUS_MULTIPLIER
    else:
        final_score = base_score

    # Determine confidence level (less strict with missing data)
    signals_present = sum([
        reddit_velocity is not None and reddit_velocity > SIGNAL_PRESENCE_THRESHOLD,
        youtube_traction is not None and youtube_traction > SIGNAL_PRESENCE_THRESHOLD,
        google_trends_spike is not None and google_trends_spike > SIGNAL_PRESENCE_THRESHOLD,
        similarweb_traffic_spike
    ])

    # Adjusted confidence thresholds for missing data
    if signals_present >= 3:
        confidence = 'high'
    elif signals_present >= 2:
        confidence = 'medium'
    elif signals_present >= 1:
        confidence = 'low'
    else:
        confidence = 'unknown'

    return (round(final_score, 2), confidence)
