"""Temporary admin endpoints for bootstrapping - REMOVE IN PRODUCTION."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.core.security import get_password_hash

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    username: str
    password: str


@router.post("/create-user")
async def create_user_endpoint(
    user_data: CreateUserRequest,
    db: AsyncSession = Depends(get_db)
):
    """Temporary endpoint to create users - REMOVE IN PRODUCTION.

    This is a temporary endpoint to bootstrap the initial user.
    In production, this should be removed or protected with proper admin auth.
    """
    try:
        # Check if user already exists
        result = await db.execute(select(User).where(User.username == user_data.username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            return {
                "status": "exists",
                "message": f"User '{user_data.username}' already exists",
                "user_id": str(existing_user.id)
            }

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            password_hash=hashed_password
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return {
            "status": "created",
            "message": f"User '{user_data.username}' created successfully",
            "user_id": str(user.id)
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
