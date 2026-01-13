"""Schema for AI brief generation responses."""
from datetime import datetime
from pydantic import BaseModel, Field


class BriefResponse(BaseModel):
    """Response model for trend brief generation endpoint.

    Attributes:
        ai_brief: The generated 3-sentence trend explanation
        generated_at: Timestamp when brief was created
        cached: Whether brief was retrieved from cache (True) or freshly generated (False)
    """

    ai_brief: str = Field(
        ...,
        description="AI-generated 3-sentence explanation of the trend",
        min_length=10
    )
    generated_at: datetime = Field(
        ...,
        description="ISO 8601 timestamp when brief was generated"
    )
    cached: bool = Field(
        ...,
        description="True if brief was cached, False if freshly generated"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ai_brief": "AI Coding Assistants are specialized tools that help developers write code faster. They're trending because major platforms show massive engagement: Reddit score 15,234, YouTube views 2,534,000, Google Trends interest 87. This trend is particularly big on developer-focused platforms and tech communities worldwide.",
                "generated_at": "2026-01-13T14:23:45.123456Z",
                "cached": False
            }
        }
