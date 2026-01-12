"""Pydantic schemas for request/response validation."""
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile
from app.schemas.trend import TrendListResponse, TrendDetailResponse, CollectionSummaryResponse

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "UserProfile",
    "TrendListResponse",
    "TrendDetailResponse",
    "CollectionSummaryResponse",
]
