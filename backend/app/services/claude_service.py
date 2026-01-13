"""Claude API service for generating trend briefs using Anthropic's Claude API."""
import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, Optional

from anthropic import AsyncAnthropic, APIError, RateLimitError, APITimeoutError

logger = logging.getLogger(__name__)


class ClaudeServiceError(Exception):
    """Base exception for Claude service errors."""
    pass


class ClaudeService:
    """Service for generating AI-powered trend explanations using Claude API.

    This service handles:
    - Prompt engineering for trend briefs
    - API communication with Anthropic's Claude
    - Retry logic with exponential backoff
    - Response validation (3-sentence structure)
    - Token usage tracking for cost monitoring
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = 2.0):
        """Initialize Claude service.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            timeout: Request timeout in seconds (default: 2.0s per Story 4.1)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ClaudeServiceError("ANTHROPIC_API_KEY environment variable not set")

        self.timeout = timeout
        self.model = "claude-sonnet-4-5-20250929"
        self.max_tokens = 150
        self.max_retries = 3

        # Initialize async client
        self.client = AsyncAnthropic(api_key=self.api_key, timeout=self.timeout)

    def _build_prompt(self, trend_data: Dict) -> str:
        """Build structured prompt for Claude API.

        Args:
            trend_data: Dictionary with trend metrics (title, reddit_score, etc.)

        Returns:
            Formatted prompt string following 3-sentence structure
        """
        title = trend_data.get("title", "Unknown trend")
        reddit_score = trend_data.get("reddit_score") or "N/A"
        youtube_views = trend_data.get("youtube_views") or "N/A"
        google_trends = trend_data.get("google_trends_interest") or "N/A"
        similarweb_traffic = trend_data.get("similarweb_traffic") or "N/A"

        # Format numbers for readability
        if isinstance(reddit_score, (int, float)):
            reddit_score = f"{int(reddit_score):,}"
        if isinstance(youtube_views, (int, float)):
            youtube_views = f"{int(youtube_views):,}"
        if isinstance(similarweb_traffic, (int, float)):
            similarweb_traffic = f"{int(similarweb_traffic):,}"

        prompt = f"""Explain this trend in exactly 3 sentences using this structure:

Sentence 1: What is '{title}'?
Sentence 2: Why is it trending? (Include these metrics: Reddit score {reddit_score}, YouTube views {youtube_views}, Google Trends interest {google_trends})
Sentence 3: Where is it big? (Based on platform data: SimilarWeb traffic {similarweb_traffic})

Be concise and factual. Each sentence must end with a period."""

        return prompt

    def _validate_response(self, response_text: str) -> bool:
        """Validate that response has exactly 3 sentences.

        Args:
            response_text: Response from Claude API

        Returns:
            True if response has exactly 3 sentences, False otherwise
        """
        # Split on ". " and count sentences
        # Handle edge case where last sentence might not have trailing space
        sentences = [s.strip() for s in response_text.split(". ") if s.strip()]

        # If last sentence doesn't end with period, it's incomplete
        if not response_text.strip().endswith("."):
            return False

        # Check for exactly 3 sentences
        return len(sentences) == 3

    async def _fetch_with_retry(self, prompt: str) -> tuple[str, int]:
        """Fetch brief from Claude API with exponential backoff retry.

        Args:
            prompt: Prompt string to send to Claude

        Returns:
            Tuple of (generated brief text, actual tokens used)

        Raises:
            ClaudeServiceError: If all retry attempts fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                message = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )

                # Extract text from response
                brief = message.content[0].text

                # Track token usage from actual API response
                tokens_used = message.usage.input_tokens + message.usage.output_tokens

                logger.info(
                    "Claude API call successful",
                    extra={
                        "event": "claude_api_call",
                        "success": True,
                        "tokens_used": tokens_used,
                        "attempt": attempt + 1
                    }
                )

                return brief, tokens_used

            except RateLimitError as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Rate limit hit, retrying in {wait_time}s",
                    extra={
                        "event": "claude_rate_limit",
                        "attempt": attempt + 1,
                        "wait_time": wait_time
                    }
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(wait_time)

            except APITimeoutError as e:
                last_error = e
                logger.error(
                    "Claude API timeout",
                    extra={
                        "event": "claude_timeout",
                        "attempt": attempt + 1,
                        "timeout": self.timeout
                    }
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

            except APIError as e:
                last_error = e
                logger.error(
                    "Claude API error",
                    extra={
                        "event": "claude_api_error",
                        "attempt": attempt + 1,
                        "status_code": getattr(e, "status_code", None),
                        "error": str(e)
                    }
                )
                # Don't retry on 4xx errors (except 429 handled above)
                if hasattr(e, "status_code") and 400 <= e.status_code < 500:
                    break
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        # All retries failed
        raise ClaudeServiceError(f"Failed to generate brief after {self.max_retries} attempts: {last_error}")

    async def generate_brief(self, trend_data: Dict) -> Dict:
        """Generate AI brief for a trend.

        Args:
            trend_data: Dictionary with trend information (title, reddit_score, etc.)

        Returns:
            Dictionary with:
                - brief: The generated 3-sentence explanation
                - tokens_used: Number of tokens consumed
                - duration_ms: API call duration in milliseconds

        Raises:
            ClaudeServiceError: If brief generation fails
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Build prompt
            prompt = self._build_prompt(trend_data)

            # Fetch with retry - returns actual token usage from API
            brief, tokens_used = await self._fetch_with_retry(prompt)

            # Validate response
            if not self._validate_response(brief):
                logger.warning(
                    "Generated brief doesn't have exactly 3 sentences",
                    extra={
                        "event": "brief_validation_failed",
                        "brief_length": len(brief),
                        "sentence_count": len([s for s in brief.split(". ") if s.strip()])
                    }
                )
                # Still return it but log the issue

            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            return {
                "brief": brief,
                "tokens_used": tokens_used,  # Actual token usage from Claude API
                "duration_ms": round(duration, 2)
            }

        except ClaudeServiceError:
            # Re-raise service errors
            raise
        except Exception as e:
            logger.error(
                "Unexpected error generating brief",
                extra={
                    "event": "brief_generation_error",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise ClaudeServiceError(f"Unexpected error: {e}")


# Global service instance (lazy-initialized)
_service: Optional[ClaudeService] = None


def get_claude_service() -> ClaudeService:
    """Get or create global Claude service instance.

    Returns:
        ClaudeService: Singleton service instance
    """
    global _service
    if _service is None:
        _service = ClaudeService()
    return _service
