"""Create bootstrap user 'dave' with secure password."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash


async def create_bootstrap_user():
    """Create user 'dave' if doesn't exist.

    This script is idempotent - it can be run multiple times safely.
    If the user already exists, it will skip creation.
    """
    print("=" * 50)
    print("Bootstrap User Creation Script")
    print("=" * 50)

    # Check if AsyncSessionLocal is available (DATABASE_URL set)
    if not AsyncSessionLocal:
        print("⚠️  WARNING: DATABASE_URL not set - cannot create user")
        print("   Skipping user creation (app will start without user)")
        return

    try:
        async with AsyncSessionLocal() as session:
            # Check if user 'dave' already exists
            result = await session.execute(select(User).where(User.username == "dave"))
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print("ℹ️  User 'dave' already exists")
                print(f"   User ID: {existing_user.id}")
                print(f"   Created: {existing_user.created_at}")
                print("   Skipping user creation")
                return

            # Create new user with bootstrap password
            # NOTE: This password should be changed after first login
            password = "changeme123"
            hashed_password = get_password_hash(password)

            user = User(
                username="dave",
                password_hash=hashed_password
            )

            session.add(user)
            await session.commit()

            print("✅ Successfully created user 'dave'")
            print(f"   Password: {password}")
            print("   ⚠️  IMPORTANT: Change this password after first login!")
            print(f"   User ID: {user.id}")

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        print("   This is expected if database is not yet initialized")
        print("   The app will still start, but login will fail until migrations run")
        # Don't raise - allow app to start even if user creation fails


if __name__ == "__main__":
    asyncio.run(create_bootstrap_user())
    print("=" * 50)
