"""Fix stuck collection in database."""
from sqlalchemy import create_engine, text
from app.config import settings

# Use sync engine for simple script
engine = create_engine(settings.database_url.replace('postgresql+asyncpg', 'postgresql'))

with engine.connect() as conn:
    result = conn.execute(text(
        """UPDATE data_collections
           SET status = 'failed',
               completed_at = NOW(),
               error_message = 'Collection interrupted by deployment'
           WHERE id = 'aa396207-36b0-4d6f-96a0-fd7979c31472'
           AND status = 'in_progress'"""
    ))
    conn.commit()
    print(f'✓ Updated {result.rowcount} collection(s) to failed status')
