"""Create ratings table.

Revision ID: 001_add_ratings
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_ratings'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ratings table for storing user ratings."""
    op.create_table(
        'ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('media_hash', sa.String(64), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=False,
                  server_default='local'),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('media_hash', 'user_id',
                            name='uq_ratings_media_user')
    )
    op.create_index('ix_ratings_media_hash', 'ratings',
                    ['media_hash'])


def downgrade() -> None:
    """Drop ratings table."""
    op.drop_index('ix_ratings_media_hash', table_name='ratings')
    op.drop_table('ratings')
