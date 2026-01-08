"""FastAPI dependencies for authentication and authorization."""
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

# OAuth2 scheme configuration
# tokenUrl="/auth/login" tells FastAPI where to find the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user from JWT token.

    This function:
    1. Extracts JWT token from Authorization header (via oauth2_scheme)
    2. Decodes and validates the JWT token
    3. Fetches the user from database
    4. Returns the User object for use in route handlers

    Args:
        token: JWT token extracted from Authorization: Bearer <token> header
        db: Database session dependency

    Returns:
        User: Authenticated user object from database

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found

    Usage in routes:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.username}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode JWT token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Extract username from 'sub' claim
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # Check if token expired (jose library handles this in decode, but explicit check for custom message)
    exp = payload.get("exp")
    if exp and datetime.utcnow().timestamp() > exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
