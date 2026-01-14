"""User model - authentication and user management."""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User account for authentication."""

    __tablename__ = "users"

    # Authentication
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Activity tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
