"""Retry decorator with exponential backoff for API calls."""
import asyncio
import logging
from functools import wraps
from typing import Optional, Type, Tuple, Callable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    backoff_base: int = 2,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """Decorator for retrying async functions with exponential backoff.

    Implements exponential backoff: 2s, 4s, 8s for default settings.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        backoff_base: Base for exponential backoff in seconds (default: 2)
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated async function with retry logic

    Example:
        @retry_with_backoff(max_attempts=3, backoff_base=2)
        async def fetch_reddit_data(topic: str):
            response = await reddit.get(topic)
            return response

    Backoff Formula:
        delay = backoff_base ^ attempt_number
        attempt 1: 2^1 = 2 seconds
        attempt 2: 2^2 = 4 seconds
        attempt 3: 2^3 = 8 seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                start_time = datetime.now(timezone.utc)
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

                    # Log successful call
                    logger.info(
                        "API call succeeded",
                        extra={
                            "event": "api_call",
                            "function": func.__name__,
                            "attempt": attempt,
                            "success": True,
                            "duration_ms": duration_ms
                        }
                    )

                    return result

                except exceptions as e:
                    last_exception = e
                    duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

                    # Log failed attempt
                    logger.warning(
                        f"API call failed (attempt {attempt}/{max_attempts}): {str(e)}",
                        extra={
                            "event": "api_call",
                            "function": func.__name__,
                            "attempt": attempt,
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "duration_ms": duration_ms
                        }
                    )

                    # Don't sleep on last attempt
                    if attempt < max_attempts:
                        backoff_seconds = backoff_base ** attempt
                        logger.info(f"Retrying in {backoff_seconds}s...")
                        await asyncio.sleep(backoff_seconds)

            # All attempts failed - log final failure
            logger.error(
                f"API call failed after {max_attempts} attempts",
                extra={
                    "event": "api_call_exhausted",
                    "function": func.__name__,
                    "max_attempts": max_attempts,
                    "final_error": str(last_exception)
                }
            )

            # Return None for graceful degradation
            return None

        return wrapper
    return decorator
