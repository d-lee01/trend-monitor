"""Unit tests for momentum score calculation."""
import pytest
from app.scoring.momentum import (
    calculate_momentum_score,
    calculate_momentum_score_safe
)


class TestCalculateMomentumScore:
    """Test cross-platform momentum score calculation."""

    def test_all_signals_high_confidence(self):
        """Test momentum score with all 4 signals present."""
        score, confidence = calculate_momentum_score(
            reddit_velocity=78.0,
            youtube_traction=82.0,
            google_trends_spike=85.0,
            similarweb_traffic_spike=True
        )
        assert confidence == 'high'
        assert score > 100  # SimilarWeb bonus applied (1.5x)

    def test_medium_confidence_two_signals(self):
        """Test momentum score with 2-3 signals."""
        score, confidence = calculate_momentum_score(
            reddit_velocity=65.0,
            youtube_traction=30.0,
            google_trends_spike=55.0,
            similarweb_traffic_spike=False
        )
        assert confidence == 'medium'
        assert 0 < score < 100

    def test_low_confidence_one_signal(self):
        """Test momentum score with only 1 signal."""
        score, confidence = calculate_momentum_score(
            reddit_velocity=60.0,
            youtube_traction=20.0,
            google_trends_spike=15.0,
            similarweb_traffic_spike=False
        )
        assert confidence == 'low'

    def test_unknown_confidence_no_signals(self):
        """Test momentum score with no signals."""
        score, confidence = calculate_momentum_score(
            reddit_velocity=10.0,
            youtube_traction=15.0,
            google_trends_spike=20.0,
            similarweb_traffic_spike=False
        )
        assert confidence == 'unknown'

    def test_similarweb_bonus_multiplier(self):
        """Test SimilarWeb bonus (1.5x) application."""
        score_without_bonus, _ = calculate_momentum_score(
            reddit_velocity=50.0,
            youtube_traction=50.0,
            google_trends_spike=50.0,
            similarweb_traffic_spike=False
        )
        score_with_bonus, _ = calculate_momentum_score(
            reddit_velocity=50.0,
            youtube_traction=50.0,
            google_trends_spike=50.0,
            similarweb_traffic_spike=True
        )
        assert score_with_bonus == score_without_bonus * 1.5


class TestCalculateMomentumScoreSafe:
    """Test safe momentum score with missing data handling."""

    def test_one_platform_missing(self):
        """Test calculation when one platform failed."""
        score, confidence = calculate_momentum_score_safe(
            reddit_velocity=75.0,
            youtube_traction=None,  # YouTube failed
            google_trends_spike=80.0,
            similarweb_traffic_spike=False
        )
        assert score > 0
        assert confidence in ['low', 'medium', 'high']

    def test_two_platforms_missing(self):
        """Test calculation when two platforms failed."""
        score, confidence = calculate_momentum_score_safe(
            reddit_velocity=65.0,
            youtube_traction=None,
            google_trends_spike=None,
            similarweb_traffic_spike=False
        )
        assert score > 0
        assert confidence in ['low', 'unknown']

    def test_all_platforms_missing(self):
        """Test graceful degradation when all platforms failed."""
        score, confidence = calculate_momentum_score_safe(
            reddit_velocity=None,
            youtube_traction=None,
            google_trends_spike=None,
            similarweb_traffic_spike=False
        )
        assert score == 0.0
        assert confidence == 'unknown'

    def test_only_similarweb_available(self):
        """Test when only SimilarWeb spike detected."""
        score, confidence = calculate_momentum_score_safe(
            reddit_velocity=None,
            youtube_traction=None,
            google_trends_spike=None,
            similarweb_traffic_spike=True
        )
        # With no base scores, SimilarWeb bonus has nothing to multiply
        assert score == 0.0
