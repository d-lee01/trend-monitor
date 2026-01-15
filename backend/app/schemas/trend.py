"""Pydantic schemas for trend API responses."""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class TrendListResponse(BaseModel):
    """Response schema for GET /trends endpoint (Top 10 list)."""

    id: UUID = Field(..., description="Unique trend identifier")
    title: str = Field(..., max_length=500, description="Trend title")
    confidence_level: str = Field(..., description="Confidence level: 'high' | 'medium' | 'low'")
    momentum_score: float = Field(..., description="Composite momentum score (0-150+)")
    reddit_score: Optional[int] = Field(None, description="Raw Reddit upvotes (None if API failed)")
    youtube_views: Optional[int] = Field(None, description="Raw YouTube views (None if API failed)")
    google_trends_interest: Optional[int] = Field(None, description="Google Trends interest 0-100 (None if API failed)")
    similarweb_traffic: Optional[int] = Field(None, description="SimilarWeb traffic volume (None if API failed)")
    created_at: datetime = Field(..., description="Timestamp when trend was discovered")

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "New Python Framework Released",
                "confidence_level": "high",
                "momentum_score": 87.5,
                "reddit_score": 15234,
                "youtube_views": 2534000,
                "google_trends_interest": 87,
                "similarweb_traffic": 1250000,
                "created_at": "2026-01-12T07:45:00Z"
            }
        }


class TrendDetailResponse(BaseModel):
    """Response schema for GET /trends/{id} endpoint (single trend detail)."""

    # Basic info
    id: UUID = Field(..., description="Unique trend identifier")
    title: str = Field(..., max_length=500, description="Trend title")
    collection_id: UUID = Field(..., description="Data collection that discovered this trend")
    created_at: datetime = Field(..., description="Timestamp when trend was discovered")

    # Reddit metrics
    reddit_score: Optional[int] = Field(None, description="Raw Reddit upvotes")
    reddit_comments: Optional[int] = Field(None, description="Number of Reddit comments")
    reddit_upvote_ratio: Optional[float] = Field(None, description="Reddit upvote ratio (0.0-1.0)")
    reddit_subreddit: Optional[str] = Field(None, max_length=100, description="Subreddit where posted")

    # YouTube metrics
    youtube_views: Optional[int] = Field(None, description="YouTube video views")
    youtube_likes: Optional[int] = Field(None, description="YouTube video likes")
    youtube_channel: Optional[str] = Field(None, max_length=200, description="YouTube channel name")

    # Google Trends metrics
    google_trends_interest: Optional[int] = Field(None, description="Google Trends interest 0-100")
    google_trends_related_queries: Optional[dict] = Field(None, description="Related queries JSONB data")

    # SimilarWeb metrics
    similarweb_traffic: Optional[int] = Field(None, description="SimilarWeb traffic volume")
    similarweb_sources: Optional[dict] = Field(None, description="Traffic sources breakdown JSONB")

    # Calculated scores
    reddit_velocity_score: Optional[float] = Field(None, description="Normalized Reddit velocity score (0-100)")
    youtube_traction_score: Optional[float] = Field(None, description="Normalized YouTube traction score (0-100)")
    google_trends_spike_score: Optional[float] = Field(None, description="Google Trends spike score (0-100)")
    similarweb_bonus_applied: Optional[bool] = Field(None, description="Whether SimilarWeb traffic spike bonus was applied")

    # Composite scores (required - calculated in Story 3.2)
    momentum_score: float = Field(..., description="Composite cross-platform momentum score")
    confidence_level: str = Field(..., description="Confidence level: 'high' | 'medium' | 'low'")

    # AI-generated content
    ai_brief: Optional[str] = Field(None, description="AI-generated trend explanation (Story 4.1)")
    ai_brief_generated_at: Optional[datetime] = Field(None, description="When AI brief was generated")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "New Python Framework Released",
                "collection_id": "abc12345-e29b-41d4-a716-446655440000",
                "created_at": "2026-01-12T07:45:00Z",
                "reddit_score": 15234,
                "reddit_comments": 892,
                "reddit_upvote_ratio": 0.95,
                "reddit_subreddit": "programming",
                "youtube_views": 2534000,
                "youtube_likes": 125000,
                "youtube_channel": "TechExplained",
                "google_trends_interest": 87,
                "google_trends_related_queries": {"queries": ["python", "framework"]},
                "similarweb_traffic": 1250000,
                "similarweb_sources": {"social": 0.6, "direct": 0.4},
                "reddit_velocity_score": 78.5,
                "youtube_traction_score": 82.3,
                "google_trends_spike_score": 85.1,
                "similarweb_bonus_applied": True,
                "momentum_score": 87.5,
                "confidence_level": "high",
                "ai_brief": None,
                "ai_brief_generated_at": None
            }
        }


class YouTubeVideoResponse(BaseModel):
    """Response schema for YouTube videos endpoint."""

    id: UUID = Field(..., description="Trend ID (unique identifier)")
    video_id: str = Field(..., max_length=20, description="YouTube video ID")
    video_title: str = Field(..., max_length=500, description="Video title")
    channel: str = Field(..., max_length=200, description="YouTube channel name")
    thumbnail_url: str = Field(..., max_length=500, description="Video thumbnail URL")
    topic: str = Field(..., max_length=200, description="Topic/search term that found this video")
    views: int = Field(..., description="View count")
    likes: int = Field(..., description="Like count")
    comments: Optional[int] = Field(None, description="Comment count (may be disabled)")
    engagement_rate: float = Field(..., description="Engagement rate (likes/views)")
    published_at: datetime = Field(..., description="When video was published")
    created_at: datetime = Field(..., description="When video was discovered")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "video_id": "dQw4w9WgXcQ",
                "video_title": "10 Airport Parking Secrets You NEED to Know!",
                "channel": "Travel Hacks Daily",
                "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/default.jpg",
                "topic": "airport parking tips",
                "views": 125000,
                "likes": 8500,
                "comments": 342,
                "engagement_rate": 0.068,
                "published_at": "2026-01-14T10:30:00Z",
                "created_at": "2026-01-15T08:45:00Z"
            }
        }


class CollectionSummaryResponse(BaseModel):
    """Response schema for GET /collections/latest endpoint."""

    id: UUID = Field(..., description="Data collection unique identifier")
    started_at: datetime = Field(..., description="When collection started")
    completed_at: Optional[datetime] = Field(None, description="When collection completed")
    status: str = Field(..., description="Collection status: 'pending' | 'running' | 'completed' | 'failed'")
    trends_found: int = Field(..., description="Number of trends discovered in this collection")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "xyz12345-e29b-41d4-a716-446655440000",
                "started_at": "2026-01-12T07:30:00Z",
                "completed_at": "2026-01-12T07:52:34Z",
                "status": "completed",
                "trends_found": 47
            }
        }
