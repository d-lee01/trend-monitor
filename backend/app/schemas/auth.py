"""Authentication schemas for request/response validation."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request schema - used for documentation only, OAuth2PasswordRequestForm used in actual endpoint."""
    username: str = Field(..., min_length=3, max_length=100, description="Username for authentication")
    password: str = Field(..., min_length=8, description="Password for authentication")


class TokenResponse(BaseModel):
    """JWT token response schema."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer' for JWT)")


class UserProfile(BaseModel):
    """User profile response schema."""
    username: str = Field(..., description="Username")
    user_id: str = Field(..., description="User ID (UUID)")

    class Config:
        """Pydantic configuration."""
        from_attributes = True  # SQLAlchemy 2.0 compatibility (formerly orm_mode)
