"""ApiQuotaUsage model - tracks daily API quota consumption."""
from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ApiQuotaUsage(Base):
    """Daily API quota usage tracking."""

    __tablename__ = "api_quota_usage"

    # Use SERIAL for auto-incrementing integer PK (not UUID)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # API identification
    api_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Date tracking
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Quota usage
    units_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Ensure one record per API per day
    __table_args__ = (
        UniqueConstraint("api_name", "date", name="uq_api_quota_usage_api_name_date"),
    )

    def __repr__(self) -> str:
        return f"<ApiQuotaUsage(api='{self.api_name}', date={self.date}, units={self.units_used})>"
