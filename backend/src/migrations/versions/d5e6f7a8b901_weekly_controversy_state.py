"""Add weekly_controversy_state for weekly digest idempotency.

Revision ID: d5e6f7a8b901
Revises: d5e6f7a89012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'd5e6f7a8b901'
down_revision: str | Sequence[str] | None = 'd5e6f7a89012'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'weekly_controversy_state',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('anchor_film_id', sa.Integer(), nullable=True),
        sa.Column('anchor_catalog_item_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('spread', sa.Float(), nullable=True),
        sa.Column('rater_count', sa.Integer(), nullable=True),
        sa.Column('min_rating', sa.Float(), nullable=True),
        sa.Column('max_rating', sa.Float(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['anchor_catalog_item_id'], ['catalog_item.id'], ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(['anchor_film_id'], ['film.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'week_start', name='uq_weekly_controversy_state_user_week'),
    )
    op.create_index(
        'ix_weekly_controversy_state_user_id',
        'weekly_controversy_state',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        'ix_weekly_controversy_state_week_start',
        'weekly_controversy_state',
        ['week_start'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_weekly_controversy_state_week_start', table_name='weekly_controversy_state')
    op.drop_index('ix_weekly_controversy_state_user_id', table_name='weekly_controversy_state')
    op.drop_table('weekly_controversy_state')
