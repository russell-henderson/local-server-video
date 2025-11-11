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
        sa.Column('filename', sa.String(255), nullable=False,
                  primary_key=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(['filename'], ['videos.filename'],
                                ondelete='CASCADE')
    )
    # Add CHECK constraint for rating range (1-5)
    op.execute(
        'ALTER TABLE ratings ADD CONSTRAINT check_rating_range '
        'CHECK (rating >= 1 AND rating <= 5)'
    )


def downgrade() -> None:
    """Drop ratings table."""
    op.drop_table('ratings')
