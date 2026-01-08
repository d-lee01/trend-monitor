"""Security utilities for password hashing and JWT token management."""
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

# Password hashing context with bcrypt (12 rounds)
# 12 rounds = 2^12 iterations = good balance of security vs performance (~250ms per hash)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password using bcrypt.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password from database

    Returns:
        True if password matches, False otherwise

    Note:
        Uses constant-time comparison to prevent timing attacks (handled by passlib)
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt with 12 rounds.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hashed password suitable for database storage

    Note:
        Each call returns a different hash due to random salt, but all will verify correctly
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with expiration.

    Args:
        data: Dictionary of claims to encode in JWT (typically {"sub": username})
        expires_delta: Optional custom expiration time, defaults to JWT_EXPIRATION_DAYS from config

    Returns:
        Encoded JWT token string

    Example:
        token = create_access_token(data={"sub": "dave"})
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_expiration_days)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary of claims if token is valid, None if invalid or expired

    Note:
        Automatically validates token signature and expiration using jose library
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
