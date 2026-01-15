"""Trend model - stores collected trend data and calculated scores."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean, CheckConstraint, Float, ForeignKey, Index, Integer,
    String, Text, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from .data_collection import DataCollection


class Trend(Base, UUIDMixin, TimestampMixin):
    """Trend data from cross-platform collection."""

    __tablename__ = "trends"

    # Basic Info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("data_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Reddit Metrics (raw)
    reddit_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reddit_comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reddit_upvote_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reddit_subreddit: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # YouTube Metrics (raw)
    youtube_views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    youtube_likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    youtube_comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    youtube_channel: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    youtube_engagement_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    youtube_video_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    youtube_thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    youtube_topic: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    youtube_published_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Google Trends Metrics (raw)
    google_trends_interest: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    google_trends_related_queries: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # SimilarWeb Metrics (raw)
    similarweb_traffic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    similarweb_sources: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Normalized Scores (0-100 scale)
    reddit_velocity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    youtube_traction_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    google_trends_spike_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    similarweb_bonus_applied: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Composite Momentum Score
    momentum_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, index=True)
    confidence_level: Mapped[Optional[str]] = mapped_column(
        String(10),
        CheckConstraint("confidence_level IN ('high', 'medium', 'low')", name="ck_trends_valid_confidence"),
        nullable=True,
        index=True
    )

    # AI Generated Brief
    ai_brief: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_brief_generated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    collection: Mapped["DataCollection"] = relationship("DataCollection", back_populates="trends")

    # Indexes for query performance
    __table_args__ = (
        Index("idx_momentum_score_desc", momentum_score.desc()),
        Index("idx_created_at_desc", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index("idx_confidence_level", confidence_level),
    )

    def __repr__(self) -> str:
        return f"<Trend(id={self.id}, title='{self.title[:50]}...', momentum_score={self.momentum_score})>"
