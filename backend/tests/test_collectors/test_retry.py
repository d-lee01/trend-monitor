"""Tests for retry decorator with exponential backoff."""
import pytest
from unittest.mock import AsyncMock
from app.collectors.retry import retry_with_backoff


@pytest.mark.asyncio
async def test_retry_succeeds_on_first_attempt():
    """Test that retry succeeds immediately if no exception."""
    mock_func = AsyncMock(return_value="success")

    @retry_with_backoff(max_attempts=3)
    async def test_func():
        return await mock_func()

    result = await test_func()

    assert result == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retry_retries_on_failure():
    """Test that retry attempts exponential backoff."""
    attempts = []

    async def failing_func():
        attempts.append(len(attempts) + 1)
        if len(attempts) < 3:
            raise Exception(f"Fail {len(attempts)}")
        return "success"

    @retry_with_backoff(max_attempts=3, backoff_base=0.1)  # Fast backoff for testing
    async def test_func():
        return await failing_func()

    result = await test_func()

    assert result == "success"
    assert len(attempts) == 3


@pytest.mark.asyncio
async def test_retry_returns_none_after_max_attempts():
    """Test that retry returns None after exhausting attempts."""
    async def always_failing_func():
        raise Exception("Always fails")

    @retry_with_backoff(max_attempts=3, backoff_base=0.1)
    async def test_func():
        return await always_failing_func()

    result = await test_func()

    assert result is None


@pytest.mark.asyncio
async def test_retry_with_specific_exception_types():
    """Test that retry only catches specified exception types."""
    async def func_with_value_error():
        raise ValueError("Value error")

    @retry_with_backoff(max_attempts=3, exceptions=(ValueError,), backoff_base=0.1)
    async def test_func():
        return await func_with_value_error()

    result = await test_func()
    assert result is None  # Should retry and return None


@pytest.mark.asyncio
async def test_retry_does_not_catch_unspecified_exceptions():
    """Test that unspecified exceptions are not caught."""
    async def func_with_type_error():
        raise TypeError("Type error")

    @retry_with_backoff(max_attempts=3, exceptions=(ValueError,), backoff_base=0.1)
    async def test_func():
        return await func_with_type_error()

    # TypeError should not be caught
    with pytest.raises(TypeError):
        await test_func()


@pytest.mark.asyncio
async def test_retry_exponential_backoff_timing():
    """Test that exponential backoff follows correct timing."""
    import time

    attempts_with_time = []

    async def failing_func():
        attempts_with_time.append(time.time())
        if len(attempts_with_time) < 3:
            raise Exception("Fail")
        return "success"

    @retry_with_backoff(max_attempts=3, backoff_base=0.1)  # 0.1, 0.01 second delays
    async def test_func():
        return await failing_func()

    start = time.time()
    result = await test_func()
    total_time = time.time() - start

    assert result == "success"
    assert len(attempts_with_time) == 3

    # Check backoff delays (0.1^1 = 0.1s, 0.1^2 = 0.01s)
    # Total should be at least 0.11 seconds
    assert total_time >= 0.1


@pytest.mark.asyncio
async def test_retry_preserves_function_name():
    """Test that decorator preserves original function name."""
    @retry_with_backoff(max_attempts=3)
    async def my_custom_function():
        return "result"

    assert my_custom_function.__name__ == "my_custom_function"


@pytest.mark.asyncio
async def test_retry_with_default_parameters():
    """Test retry with default parameters (3 attempts, base 2)."""
    attempt_count = 0

    async def func():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise Exception("Fail")
        return "success"

    @retry_with_backoff()  # Use defaults
    async def test_func():
        return await func()

    result = await test_func()

    assert result == "success"
    assert attempt_count == 2
