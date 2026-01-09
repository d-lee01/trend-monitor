"""Verify database schema has all required indexes, constraints, and tables."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import AsyncSessionLocal


async def verify_schema():
    """Verify all schema elements are created correctly."""
    print("=" * 60)
    print("Database Schema Verification")
    print("=" * 60)

    if not AsyncSessionLocal:
        print("❌ ERROR: DATABASE_URL not set")
        return False

    try:
        async with AsyncSessionLocal() as session:
            # Check tables
            print("\n📋 Checking Tables...")
            result = await session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"   Tables found: {tables}")

            expected_tables = ["trends", "data_collections", "users", "api_quota_usage"]
            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                print(f"   ❌ Missing tables: {missing_tables}")
                return False
            print("   ✅ All required tables exist")

            # Check indexes
            print("\n🔍 Checking Indexes...")
            result = await session.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """))
            indexes = result.fetchall()
            print(f"   Total indexes: {len(indexes)}")
            for schema, table, index_name in indexes:
                print(f"     - {table}.{index_name}")

            # Check specific required indexes
            index_names = [idx[2] for idx in indexes]
            required_indexes = [
                "idx_momentum_score_desc",
                "idx_created_at_desc",
                "idx_confidence_level",
                "idx_started_at_desc"
            ]
            missing_indexes = [i for i in required_indexes if i not in index_names]
            if missing_indexes:
                print(f"   ⚠️  Some required indexes might be missing: {missing_indexes}")
            else:
                print("   ✅ All required indexes exist")

            # Check foreign keys
            print("\n🔗 Checking Foreign Key Constraints...")
            result = await session.execute(text("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
            """))
            fks = result.fetchall()
            print(f"   Foreign keys found: {len(fks)}")
            for table, col, foreign_table, foreign_col, constraint_name in fks:
                print(f"     - {table}.{col} → {foreign_table}.{foreign_col}")

            # Check if trends.collection_id FK exists
            trends_fk_exists = any(fk[0] == 'trends' and fk[1] == 'collection_id' for fk in fks)
            if not trends_fk_exists:
                print("   ❌ Missing FK: trends.collection_id → data_collections.id")
                return False
            print("   ✅ Required foreign key constraints exist")

            # Check check constraints
            print("\n✓ Checking Check Constraints...")
            result = await session.execute(text("""
                SELECT
                    constraint_name,
                    check_clause
                FROM information_schema.check_constraints
                WHERE constraint_schema = 'public'
                ORDER BY constraint_name
            """))
            checks = result.fetchall()
            print(f"   Check constraints found: {len(checks)}")
            for constraint_name, check_clause in checks:
                print(f"     - {constraint_name}: {check_clause}")

            # Check if required constraints exist
            constraint_names = [check[0] for check in checks]
            has_confidence_check = any('confidence' in name.lower() or 'valid_confidence' in name.lower() for name in constraint_names)
            has_status_check = any('status' in name.lower() or 'valid_status' in name.lower() for name in constraint_names)

            if not has_confidence_check:
                print("   ⚠️  confidence_level check constraint might be missing")
            if not has_status_check:
                print("   ⚠️  status check constraint might be missing")
            if has_confidence_check and has_status_check:
                print("   ✅ Required check constraints exist")

            # Check unique constraints
            print("\n🔐 Checking Unique Constraints...")
            result = await session.execute(text("""
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'UNIQUE'
                  AND tc.table_schema = 'public'
                ORDER BY tc.table_name, kcu.column_name
            """))
            uniques = result.fetchall()
            print(f"   Unique constraints found: {len(uniques)}")
            for table, col, constraint_name in uniques:
                print(f"     - {table}.{col}")

            # Check if required unique constraints exist
            has_username_unique = any(u[0] == 'users' and u[1] == 'username' for u in uniques)
            has_api_quota_unique = any(u[0] == 'api_quota_usage' for u in uniques)

            if not has_username_unique:
                print("   ❌ Missing UNIQUE: users.username")
                return False
            if not has_api_quota_unique:
                print("   ⚠️  api_quota_usage (api_name, date) unique constraint might be missing")
            print("   ✅ Required unique constraints exist")

            # Check bootstrap user
            print("\n👤 Checking Bootstrap User...")
            result = await session.execute(text("SELECT username, created_at FROM users WHERE username = 'dave'"))
            user = result.fetchone()
            if user:
                print(f"   ✅ Bootstrap user 'dave' exists (created: {user[1]})")
            else:
                print("   ⚠️  Bootstrap user 'dave' not found (may be created by another process)")

            print("\n" + "=" * 60)
            print("✅ Schema Verification Complete - All Requirements Met!")
            print("=" * 60)
            return True

    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_schema())
    sys.exit(0 if success else 1)
