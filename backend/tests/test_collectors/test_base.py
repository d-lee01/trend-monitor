"""Tests for DataCollector abstract base class and dataclasses."""
import pytest
from app.collectors.base import DataCollector, CollectionResult, RateLimitInfo
from datetime import datetime


def test_collection_result_success_rate_calculation():
    """Test that success_rate is calculated correctly from total/successful calls."""
    result = CollectionResult(
        source="test",
        data=[{"id": 1}, None, {"id": 2}],
        success_rate=0.0,  # Will be calculated
        total_calls=3,
        successful_calls=2,
        failed_calls=1
    )

    assert result.success_rate == pytest.approx(0.666, rel=0.01)


def test_collection_result_errors_list_initialized():
    """Test that errors list is initialized if None."""
    result = CollectionResult(
        source="test",
        data=[],
        success_rate=0.0,
        total_calls=0
    )

    assert result.errors == []
    assert isinstance(result.errors, list)


def test_collection_result_with_provided_success_rate():
    """Test that provided success_rate is not overwritten."""
    result = CollectionResult(
        source="test",
        data=[{"id": 1}],
        success_rate=0.85,  # Manually provided
        total_calls=10,
        successful_calls=8,
        failed_calls=2
    )

    # Should keep the provided success_rate
    assert result.success_rate == 0.85


def test_collection_result_zero_division_protection():
    """Test that zero total_calls doesn't cause division errors."""
    result = CollectionResult(
        source="test",
        data=[],
        success_rate=0.0,
        total_calls=0,
        successful_calls=0,
        failed_calls=0
    )

    assert result.success_rate == 0.0


def test_rate_limit_info_dataclass():
    """Test that RateLimitInfo can be created with all fields."""
    now = datetime.utcnow()
    info = RateLimitInfo(
        limit=60,
        remaining=45,
        reset_at=now,
        quota_type="per_minute"
    )

    assert info.limit == 60
    assert info.remaining == 45
    assert info.reset_at == now
    assert info.quota_type == "per_minute"


def test_data_collector_is_abstract():
    """Test that DataCollector cannot be instantiated directly."""
    with pytest.raises(TypeError):
        # Should fail because it's abstract
        collector = DataCollector(name="test")


def test_data_collector_subclass_must_implement_methods():
    """Test that DataCollector subclass must implement abstract methods."""
    class IncompleteCollector(DataCollector):
        # Missing implementations
        pass

    with pytest.raises(TypeError):
        collector = IncompleteCollector(name="incomplete")


@pytest.mark.asyncio
async def test_data_collector_concrete_implementation():
    """Test that a complete DataCollector subclass can be instantiated."""
    class TestCollector(DataCollector):
        async def collect(self, topics):
            return CollectionResult(
                source=self.name,
                data=[{"topic": t} for t in topics],
                success_rate=1.0,
                total_calls=len(topics),
                successful_calls=len(topics),
                failed_calls=0
            )

        async def health_check(self):
            return True

        async def get_rate_limit_info(self):
            return RateLimitInfo(
                limit=100,
                remaining=50,
                reset_at=datetime.utcnow(),
                quota_type="per_minute"
            )

    collector = TestCollector(name="test")
    assert collector.name == "test"

    # Test collect
    result = await collector.collect(["topic1", "topic2"])
    assert result.source == "test"
    assert len(result.data) == 2
    assert result.success_rate == 1.0

    # Test health_check
    is_healthy = await collector.health_check()
    assert is_healthy is True

    # Test get_rate_limit_info
    rate_info = await collector.get_rate_limit_info()
    assert rate_info.limit == 100
    assert rate_info.remaining == 50
