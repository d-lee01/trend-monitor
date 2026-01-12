"""Unit tests for scoring normalization functions."""
import pytest
import math
from app.scoring.normalizer import (
    normalize_reddit_score,
    normalize_youtube_traction,
    calculate_google_trends_spike,
    detect_similarweb_traffic_spike
)


class TestNormalizeRedditScore:
    """Test Reddit velocity score normalization."""

    def test_typical_viral_post(self):
        """Test scoring of typical viral Reddit post."""
        score = normalize_reddit_score(
            score=5000,
            hours_since_post=2.0,
            subreddit_size=1000000
        )
        assert 0 <= score <= 100
        assert score > 50  # Should be "high"

    def test_zero_hours_edge_case(self):
        """Test post just published (near 0 hours)."""
        score = normalize_reddit_score(
            score=100,
            hours_since_post=0.1,
            subreddit_size=10000
        )
        assert score > 0
        assert score <= 100

    def test_old_post_decay(self):
        """Test score decay over time."""
        score = normalize_reddit_score(
            score=100,
            hours_since_post=1000.0,
            subreddit_size=10000
        )
        assert score < 1  # Should decay significantly

    def test_small_subreddit_authority_weight(self):
        """Test authority weight for small vs large subreddits."""
        small_sub_score = normalize_reddit_score(
            score=100,
            hours_since_post=1.0,
            subreddit_size=1000  # Small subreddit
        )
        large_sub_score = normalize_reddit_score(
            score=100,
            hours_since_post=1.0,
            subreddit_size=1000000  # Large subreddit
        )
        assert large_sub_score > small_sub_score

    @pytest.mark.parametrize("score,hours,subs,expected_min,expected_max", [
        (100, 1.0, 1000, 0, 100),
        (0, 1.0, 1000, 0, 10),
        (1000, 0.5, 100000, 50, 100),
        (10000, 1.0, 10000000, 50, 100),
    ])
    def test_parametrized_scores(self, score, hours, subs, expected_min, expected_max):
        """Test multiple scenarios with parametrize."""
        result = normalize_reddit_score(score, hours, subs)
        assert expected_min <= result <= expected_max


class TestNormalizeYouTubeTraction:
    """Test YouTube traction score normalization."""

    def test_typical_viral_video(self):
        """Test typical viral YouTube video."""
        score = normalize_youtube_traction(
            views=250000,
            hours_since_publish=6.0,
            likes=8000,
            channel_subs=500000
        )
        assert 0 <= score <= 100
        assert score > 10  # Realistic threshold for given MAX_YOUTUBE_TRACTION

    def test_high_engagement_rate(self):
        """Test video with high engagement rate (likes/views)."""
        high_engagement = normalize_youtube_traction(
            views=10000,
            hours_since_publish=1.0,
            likes=1000,  # 10% engagement rate
            channel_subs=100000
        )
        low_engagement = normalize_youtube_traction(
            views=10000,
            hours_since_publish=1.0,
            likes=100,  # 1% engagement rate
            channel_subs=100000
        )
        assert high_engagement > low_engagement

    def test_zero_views_edge_case(self):
        """Test video with zero views (just published)."""
        score = normalize_youtube_traction(
            views=0,
            hours_since_publish=0.1,
            likes=0,
            channel_subs=1000
        )
        assert score == 0  # Zero views should result in zero score

    @pytest.mark.parametrize("views,hours,likes,subs", [
        (1000, 1.0, 50, 10000),
        (100000, 12.0, 2000, 500000),
        (50, 0.5, 5, 1000),
    ])
    def test_score_range(self, views, hours, likes, subs):
        """Test all scores fall within 0-100 range."""
        score = normalize_youtube_traction(views, hours, likes, subs)
        assert 0 <= score <= 100


class TestCalculateGoogleTrendsSpike:
    """Test Google Trends spike detection using Z-score."""

    def test_strong_spike_detection(self):
        """Test detection of strong spike (3 std devs above mean)."""
        score = calculate_google_trends_spike(
            current_interest=85,
            seven_day_history=[30, 35, 40, 45, 50, 60, 85]
        )
        assert score > 70  # Strong spike should score high

    def test_no_spike_baseline(self):
        """Test flat interest (no spike)."""
        score = calculate_google_trends_spike(
            current_interest=50,
            seven_day_history=[48, 49, 50, 51, 52, 50, 50]
        )
        assert 45 <= score <= 55  # Should be around baseline (50)

    def test_declining_interest(self):
        """Test declining interest (negative spike)."""
        score = calculate_google_trends_spike(
            current_interest=20,
            seven_day_history=[60, 65, 70, 75, 80, 75, 20]
        )
        assert score < 30  # Declining interest should score low

    def test_insufficient_historical_data(self):
        """Test fallback when insufficient history."""
        score = calculate_google_trends_spike(
            current_interest=75,
            seven_day_history=[50]  # Only 1 data point
        )
        assert score == 75  # Should return current_interest directly

    def test_zero_stddev_edge_case(self):
        """Test flat interest with zero standard deviation."""
        score = calculate_google_trends_spike(
            current_interest=50,
            seven_day_history=[50, 50, 50, 50, 50, 50, 50]
        )
        assert score == 50.0  # Should return baseline


class TestDetectSimilarWebTrafficSpike:
    """Test SimilarWeb traffic spike detection."""

    def test_spike_detected_above_threshold(self):
        """Test spike detection when change > 50%."""
        result = detect_similarweb_traffic_spike(traffic_change_percentage=75.5)
        assert result is True

    def test_no_spike_below_threshold(self):
        """Test no spike when change < 50%."""
        result = detect_similarweb_traffic_spike(traffic_change_percentage=25.0)
        assert result is False

    def test_exactly_at_threshold(self):
        """Test edge case at exactly 50% threshold."""
        result = detect_similarweb_traffic_spike(traffic_change_percentage=50.0)
        assert result is False  # Must be > 50%, not >= 50%

    def test_none_traffic_change(self):
        """Test missing SimilarWeb data (None)."""
        result = detect_similarweb_traffic_spike(traffic_change_percentage=None)
        assert result is False

    def test_negative_traffic_change(self):
        """Test traffic decline (negative percentage)."""
        result = detect_similarweb_traffic_spike(traffic_change_percentage=-30.0)
        assert result is False
