"""DataCollection model - tracks collection runs and API usage."""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Index, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base, UUIDMixin

if TYPE_CHECKING:
    from .trend import Trend


class DataCollection(Base, UUIDMixin):
    """Data collection run metadata and API usage tracking."""

    __tablename__ = "data_collections"

    # Collection timestamps
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Collection status
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("status IN ('in_progress', 'completed', 'failed')", name="valid_status"),
        nullable=False,
        default="in_progress"
    )

    # Error tracking (JSONB for flexibility)
    errors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # API usage metrics
    reddit_api_calls: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    youtube_api_quota_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    google_trends_api_calls: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

    # Relationships
    trends: Mapped[List["Trend"]] = relationship(
        "Trend",
        back_populates="collection",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_started_at_desc", "started_at", postgresql_ops={"started_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<DataCollection(id={self.id}, status='{self.status}', started_at={self.started_at})>"
