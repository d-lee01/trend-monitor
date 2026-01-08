"""Authentication API endpoints for login and user profile."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserProfile
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT access token.

    This endpoint follows the OAuth2 Password Flow specification.
    It accepts form-encoded credentials and returns a JWT bearer token.

    Args:
        form_data: OAuth2 form data with username and password
        db: Database session dependency

    Returns:
        TokenResponse: JWT access token and token type

    Raises:
        HTTPException 401: If credentials are invalid

    Example:
        POST /auth/login
        Content-Type: application/x-www-form-urlencoded

        username=dave&password=changeme123

        Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
    """
    # Query user by username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    # Verify user exists and password matches
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login timestamp
    user.last_login = datetime.utcnow()
    await db.commit()

    # Create JWT token with username in 'sub' (subject) claim
    access_token = create_access_token(data={"sub": user.username})

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user profile.

    This endpoint requires a valid JWT token in the Authorization header.
    It returns the profile of the authenticated user.

    Args:
        current_user: Authenticated user from JWT token (injected by dependency)

    Returns:
        UserProfile: Username and user ID

    Example:
        GET /auth/me
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        Response:
        {
            "username": "dave",
            "user_id": "123e4567-e89b-12d3-a456-426614174000"
        }
    """
    return UserProfile(
        username=current_user.username,
        user_id=str(current_user.id)
    )
