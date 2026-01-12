"""Integration tests for score calculation after data collection.

NOTE: These tests use AsyncMock for database sessions to avoid pytest-asyncio
fixture compatibility issues. This approach tests the scoring logic thoroughly
but does not verify actual database persistence (column types, constraints, etc.).

Phase 2 Enhancement: Add at least one integration test using a real database
fixture (e.g., pytest-postgresql) to verify end-to-end persistence including:
- CHECK constraint validation (confidence_level values)
- JSONB column storage
- Foreign key relationships
- Transaction rollback behavior
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.api.collection import calculate_and_update_scores
from app.models.trend import Trend


@pytest.mark.asyncio
class TestScoreCalculationIntegration:
    """Integration tests for scoring after data collection."""

    async def test_scores_all_platforms_success(self):
        """Test scoring when all 4 platforms collected data successfully."""
        # Setup: Create mock database session
        mock_db = AsyncMock()
        collection_id = uuid4()

        # Create mock trend with all platform data
        trend = Trend(
            id=uuid4(),
            title="Test Trend - All Platforms",
            collection_id=collection_id,
            created_at=datetime.now(timezone.utc),
            reddit_score=5000,
            reddit_subreddit="videos",
            youtube_views=250000,
            youtube_likes=8000,
            google_trends_interest=85,
            similarweb_bonus_applied=True
        )

        # Mock database queries - collection validation, then trends query
        mock_collection_result = MagicMock()
        mock_collection_result.scalar_one_or_none.return_value = MagicMock(id=collection_id)

        mock_trends_result = MagicMock()
        mock_trends_result.scalars().all.return_value = [trend]

        # First call returns collection, second call returns trends
        mock_db.execute = AsyncMock(side_effect=[mock_collection_result, mock_trends_result])
        mock_db.commit = AsyncMock()

        # Act: Calculate scores
        result = await calculate_and_update_scores(collection_id, mock_db)

        # Assert: Scores calculated
        assert trend.reddit_velocity_score is not None
        assert trend.reddit_velocity_score > 0
        assert trend.youtube_traction_score is not None
        assert trend.youtube_traction_score > 0
        assert trend.google_trends_spike_score is not None
        assert trend.google_trends_spike_score > 0
        assert trend.momentum_score > 0
        assert trend.confidence_level == "high"  # All 4 signals
        assert result["trends_scored"] == 1
        assert result["duration_seconds"] >= 0  # Duration should be non-negative
        assert result["degraded_count"] == 0

    async def test_scores_reddit_missing(self):
        """Test graceful degradation when Reddit API failed."""
        mock_db = AsyncMock()
        collection_id = uuid4()

        trend = Trend(
            id=uuid4(),
            title="Test Trend - Reddit Missing",
            collection_id=collection_id,
            created_at=datetime.now(timezone.utc),
            reddit_score=None,  # Reddit failed
            youtube_views=250000,
            youtube_likes=8000,
            google_trends_interest=85,
            similarweb_bonus_applied=False
        )

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [trend]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Act
        result = await calculate_and_update_scores(collection_id, mock_db)

        # Assert: Uses safe function
        assert trend.reddit_velocity_score is None
        assert trend.youtube_traction_score is not None
        assert trend.google_trends_spike_score is not None
        assert trend.momentum_score > 0
        assert trend.confidence_level in ["medium", "low"]
        assert result["degraded_count"] == 1

    async def test_scores_youtube_missing(self):
        """Test graceful degradation when YouTube API failed."""
        mock_db = AsyncMock()
        collection_id = uuid4()

        trend = Trend(
            id=uuid4(),
            title="Test Trend - YouTube Missing",
            collection_id=collection_id,
            created_at=datetime.now(timezone.utc),
            reddit_score=5000,
            youtube_views=None,  # YouTube failed
            youtube_likes=None,
            google_trends_interest=85,
            similarweb_bonus_applied=True
        )

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [trend]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Act
        result = await calculate_and_update_scores(collection_id, mock_db)

        # Assert
        assert trend.reddit_velocity_score is not None
        assert trend.youtube_traction_score is None
        assert trend.google_trends_spike_score is not None
        assert trend.momentum_score > 0
        assert result["degraded_count"] == 1

    async def test_scores_all_platforms_missing(self):
        """Test scoring when all platforms failed."""
        mock_db = AsyncMock()
        collection_id = uuid4()

        trend = Trend(
            id=uuid4(),
            title="Test Trend - All Missing",
            collection_id=collection_id,
            created_at=datetime.now(timezone.utc),
            reddit_score=None,
            youtube_views=None,
            youtube_likes=None,
            google_trends_interest=None,
            similarweb_bonus_applied=False
        )

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [trend]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Act
        result = await calculate_and_update_scores(collection_id, mock_db)

        # Assert: Maps 'unknown' to 'low' for DB compatibility
        assert trend.reddit_velocity_score is None
        assert trend.youtube_traction_score is None
        assert trend.google_trends_spike_score is None
        assert trend.momentum_score == 0.0
        assert trend.confidence_level == "low"  # Mapped from 'unknown'
        assert result["degraded_count"] == 1

    async def test_scores_no_trends_in_collection(self):
        """Test scoring when collection has no trends."""
        mock_db = AsyncMock()
        collection_id = uuid4()

        # Mock collection validation
        mock_collection_result = MagicMock()
        mock_collection_result.scalar_one_or_none.return_value = MagicMock(id=collection_id)

        # Mock empty trends result
        mock_trends_result = MagicMock()
        mock_trends_result.scalars().all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[mock_collection_result, mock_trends_result])

        # Act
        result = await calculate_and_update_scores(collection_id, mock_db)

        # Assert
        assert result["trends_scored"] == 0
        assert result["duration_seconds"] == 0.0
        assert result["degraded_count"] == 0

    async def test_scores_invalid_collection_id(self):
        """Test scoring with non-existent collection ID."""
        mock_db = AsyncMock()
        collection_id = uuid4()

        # Mock collection not found
        mock_collection_result = MagicMock()
        mock_collection_result.scalar_one_or_none.return_value = None

        mock_db.execute = AsyncMock(return_value=mock_collection_result)

        # Act & Assert
        with pytest.raises(ValueError, match=f"Collection {collection_id} does not exist"):
            await calculate_and_update_scores(collection_id, mock_db)

    async def test_scores_multiple_trends_batch_update(self):
        """Test batch scoring of multiple trends."""
        mock_db = AsyncMock()
        collection_id = uuid4()

        # Create 10 trends with varying platform availability
        trends = []
        for i in range(10):
            trend = Trend(
                id=uuid4(),
                title=f"Test Trend {i}",
                collection_id=collection_id,
                created_at=datetime.now(timezone.utc),
                reddit_score=5000 if i % 2 == 0 else None,
                youtube_views=250000 if i % 3 == 0 else None,
                youtube_likes=8000 if i % 3 == 0 else None,
                google_trends_interest=85 if i % 4 == 0 else None,
                similarweb_bonus_applied=(i % 5 == 0)
            )
            trends.append(trend)

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = trends
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Act
        result = await calculate_and_update_scores(collection_id, mock_db)

        # Assert
        assert result["trends_scored"] == 10
        assert result["duration_seconds"] < 5  # < 5 seconds total (well under requirement)
        assert result["degraded_count"] > 0  # Some trends have missing data

        # Verify all trends have momentum scores
        for trend in trends:
            assert trend.momentum_score is not None
            assert trend.confidence_level in ["high", "medium", "low"]

        # Verify commit was called once (batch update)
        mock_db.commit.assert_called_once()

    @pytest.mark.parametrize("reddit,youtube,google,similarweb,expected_conf", [
        (5000, 250000, 85, True, "high"),
        (5000, 250000, 85, False, "medium"),
        (5000, 250000, None, False, "medium"),
        (5000, None, None, False, "low"),
        (None, None, None, False, "low"),  # Mapped from 'unknown'
    ])
    async def test_confidence_with_varying_platforms(
        self, reddit, youtube, google, similarweb, expected_conf
    ):
        """Test confidence level calculation with different platform availability."""
        mock_db = AsyncMock()
        collection_id = uuid4()

        trend = Trend(
            id=uuid4(),
            title="Test Trend",
            collection_id=collection_id,
            created_at=datetime.now(timezone.utc),
            reddit_score=reddit,
            youtube_views=youtube,
            youtube_likes=8000 if youtube else None,
            google_trends_interest=google,
            similarweb_bonus_applied=similarweb
        )

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [trend]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Act
        await calculate_and_update_scores(collection_id, mock_db)

        # Assert
        assert trend.confidence_level == expected_conf

    async def test_similarweb_bonus_applied(self):
        """Test SimilarWeb traffic spike bonus is applied."""
        mock_db = AsyncMock()
        collection_id = uuid4()

        # Create two identical trends except for SimilarWeb bonus
        trend_without_bonus = Trend(
            id=uuid4(),
            title="Test Trend - No Bonus",
            collection_id=collection_id,
            created_at=datetime.now(timezone.utc),
            reddit_score=5000,
            youtube_views=250000,
            youtube_likes=8000,
            google_trends_interest=85,
            similarweb_bonus_applied=False
        )

        trend_with_bonus = Trend(
            id=uuid4(),
            title="Test Trend - With Bonus",
            collection_id=collection_id,
            created_at=datetime.now(timezone.utc),
            reddit_score=5000,
            youtube_views=250000,
            youtube_likes=8000,
            google_trends_interest=85,
            similarweb_bonus_applied=True
        )

        # Test without bonus
        mock_result1 = MagicMock()
        mock_result1.scalars().all.return_value = [trend_without_bonus]
        mock_db.execute = AsyncMock(return_value=mock_result1)
        await calculate_and_update_scores(collection_id, mock_db)

        # Test with bonus
        mock_result2 = MagicMock()
        mock_result2.scalars().all.return_value = [trend_with_bonus]
        mock_db.execute = AsyncMock(return_value=mock_result2)
        await calculate_and_update_scores(collection_id, mock_db)

        # Assert: SimilarWeb bonus multiplies momentum score by 1.5
        assert trend_with_bonus.momentum_score == pytest.approx(
            trend_without_bonus.momentum_score * 1.5,
            abs=0.1
        )

        # SimilarWeb counts as 4th signal
        assert trend_without_bonus.confidence_level == "medium"  # 3 signals
        assert trend_with_bonus.confidence_level == "high"  # 4 signals
