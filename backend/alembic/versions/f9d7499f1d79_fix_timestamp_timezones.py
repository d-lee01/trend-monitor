"""fix_timestamp_timezones

Revision ID: f9d7499f1d79
Revises: f59d3de35f66
Create Date: 2026-01-14 09:48:25.669867+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9d7499f1d79'
down_revision: Union[str, None] = 'f59d3de35f66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert all TIMESTAMP columns to TIMESTAMP WITH TIME ZONE
    # data_collections table
    op.execute('ALTER TABLE data_collections ALTER COLUMN started_at TYPE TIMESTAMP WITH TIME ZONE')
    op.execute('ALTER TABLE data_collections ALTER COLUMN completed_at TYPE TIMESTAMP WITH TIME ZONE')

    # trends table
    op.execute('ALTER TABLE trends ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE')
    op.execute('ALTER TABLE trends ALTER COLUMN ai_brief_generated_at TYPE TIMESTAMP WITH TIME ZONE')

    # users table
    op.execute('ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE')
    op.execute('ALTER TABLE users ALTER COLUMN last_login TYPE TIMESTAMP WITH TIME ZONE')


def downgrade() -> None:
    # Convert back to TIMESTAMP WITHOUT TIME ZONE
    # data_collections table
    op.execute('ALTER TABLE data_collections ALTER COLUMN started_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE data_collections ALTER COLUMN completed_at TYPE TIMESTAMP WITHOUT TIME ZONE')

    # trends table
    op.execute('ALTER TABLE trends ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE trends ALTER COLUMN ai_brief_generated_at TYPE TIMESTAMP WITHOUT TIME ZONE')

    # users table
    op.execute('ALTER TABLE users ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE')
    op.execute('ALTER TABLE users ALTER COLUMN last_login TYPE TIMESTAMP WITHOUT TIME ZONE')
