"""Edge case tests for scoring algorithms."""
import pytest
from app.scoring.normalizer import normalize_reddit_score
from app.scoring.momentum import calculate_momentum_score


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_hours_reddit(self):
        """Test Reddit score with zero hours (just posted)."""
        score = normalize_reddit_score(score=100, hours_since_post=0.0, subreddit_size=10000)
        assert 0 <= score <= 100  # Should not crash

    def test_negative_score_reddit(self):
        """Test Reddit score with negative value (shouldn't happen but handle gracefully)."""
        score = normalize_reddit_score(score=-50, hours_since_post=1.0, subreddit_size=10000)
        assert score == 0  # Negative scores treated as 0

    def test_extremely_large_score(self):
        """Test Reddit score with extremely large values."""
        score = normalize_reddit_score(score=1000000, hours_since_post=0.1, subreddit_size=50000000)
        assert score == 100.0  # Should be capped at 100

    def test_momentum_score_all_zeros(self):
        """Test momentum calculation with all zero scores."""
        score, confidence = calculate_momentum_score(
            reddit_velocity=0.0,
            youtube_traction=0.0,
            google_trends_spike=0.0,
            similarweb_traffic_spike=False
        )
        assert score == 0.0
        assert confidence == 'unknown'
