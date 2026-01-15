"""add_youtube_metadata_fields

Revision ID: 98d2bdf1d033
Revises: f9d7499f1d79
Create Date: 2026-01-15 11:15:48.760168+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98d2bdf1d033'
down_revision: Union[str, None] = 'f9d7499f1d79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add YouTube metadata fields to trends table
    op.add_column('trends', sa.Column('youtube_comments', sa.Integer(), nullable=True))
    op.add_column('trends', sa.Column('youtube_engagement_rate', sa.Float(), nullable=True))
    op.add_column('trends', sa.Column('youtube_video_id', sa.String(length=20), nullable=True))
    op.add_column('trends', sa.Column('youtube_thumbnail_url', sa.String(length=500), nullable=True))
    op.add_column('trends', sa.Column('youtube_topic', sa.String(length=200), nullable=True))
    op.add_column('trends', sa.Column('youtube_published_at', sa.TIMESTAMP(timezone=True), nullable=True))

    # Create index on youtube_topic for faster filtering
    op.create_index('idx_youtube_topic', 'trends', ['youtube_topic'])


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_youtube_topic', table_name='trends')

    # Remove YouTube metadata fields
    op.drop_column('trends', 'youtube_published_at')
    op.drop_column('trends', 'youtube_topic')
    op.drop_column('trends', 'youtube_thumbnail_url')
    op.drop_column('trends', 'youtube_video_id')
    op.drop_column('trends', 'youtube_engagement_rate')
    op.drop_column('trends', 'youtube_comments')
