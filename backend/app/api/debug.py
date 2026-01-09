"""Temporary debug endpoints - REMOVE IN PRODUCTION."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/schema")
async def verify_schema(db: AsyncSession = Depends(get_db)):
    """Verify database schema elements."""
    try:
        result = {}

        # Get tables
        tables_result = await db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        result["tables"] = [row[0] for row in tables_result.fetchall()]

        # Get indexes
        indexes_result = await db.execute(text("""
            SELECT tablename, indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """))
        result["indexes"] = [{"table": row[0], "index": row[1]} for row in indexes_result.fetchall()]

        # Get foreign keys
        fk_result = await db.execute(text("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
        """))
        result["foreign_keys"] = [
            {"table": row[0], "column": row[1], "references_table": row[2], "references_column": row[3]}
            for row in fk_result.fetchall()
        ]

        # Get check constraints
        check_result = await db.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_schema = 'public'
            ORDER BY constraint_name
        """))
        result["check_constraints"] = [
            {"name": row[0], "clause": row[1]}
            for row in check_result.fetchall()
        ]

        # Get unique constraints
        unique_result = await db.execute(text("""
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'UNIQUE'
              AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name
        """))
        result["unique_constraints"] = [
            {"table": row[0], "column": row[1]}
            for row in unique_result.fetchall()
        ]

        # Check bootstrap user
        user_result = await db.execute(text("SELECT username, created_at FROM users WHERE username = 'dave'"))
        user = user_result.fetchone()
        result["bootstrap_user"] = {"exists": user is not None, "created_at": str(user[1]) if user else None}

        return {"status": "success", "schema": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}
