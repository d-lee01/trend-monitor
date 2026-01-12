"""Scoring module for trend-monitor.

Pure function algorithms for normalizing platform metrics and
calculating cross-platform momentum scores with confidence levels.

All functions are deterministic and testable with no side effects.

Usage:
    from app.scoring import (
        normalize_reddit_score,
        normalize_youtube_traction,
        calculate_google_trends_spike,
        detect_similarweb_traffic_spike,
        calculate_momentum_score,
        calculate_momentum_score_safe
    )

    # Calculate individual platform scores
    reddit_score = normalize_reddit_score(5000, 2.0, 1000000)
    youtube_score = normalize_youtube_traction(250000, 6.0, 8000, 500000)
    google_score = calculate_google_trends_spike(85, [30, 35, 40, 45, 50, 60, 85])
    similarweb_spike = detect_similarweb_traffic_spike(75.5)

    # Calculate composite momentum score
    momentum, confidence = calculate_momentum_score(
        reddit_score, youtube_score, google_score, similarweb_spike
    )

References:
    Architecture: AD-5 Scoring Algorithm as Pure Functions
    Epics: Story 3.1 Scoring Algorithm Implementation
"""

from .normalizer import (
    normalize_reddit_score,
    normalize_youtube_traction,
    calculate_google_trends_spike,
    detect_similarweb_traffic_spike
)
from .momentum import (
    calculate_momentum_score,
    calculate_momentum_score_safe
)
from .constants import (
    MAX_REDDIT_VELOCITY,
    MAX_YOUTUBE_TRACTION,
    GOOGLE_TRENDS_Z_SCORE_RANGE,
    REDDIT_WEIGHT,
    YOUTUBE_WEIGHT,
    GOOGLE_TRENDS_WEIGHT,
    SIMILARWEB_BONUS_MULTIPLIER,
    SIGNAL_PRESENCE_THRESHOLD
)

__all__ = [
    # Normalization functions
    'normalize_reddit_score',
    'normalize_youtube_traction',
    'calculate_google_trends_spike',
    'detect_similarweb_traffic_spike',

    # Momentum calculation
    'calculate_momentum_score',
    'calculate_momentum_score_safe',

    # Constants (for testing/tuning)
    'MAX_REDDIT_VELOCITY',
    'MAX_YOUTUBE_TRACTION',
    'GOOGLE_TRENDS_Z_SCORE_RANGE',
    'REDDIT_WEIGHT',
    'YOUTUBE_WEIGHT',
    'GOOGLE_TRENDS_WEIGHT',
    'SIMILARWEB_BONUS_MULTIPLIER',
    'SIGNAL_PRESENCE_THRESHOLD',
]
