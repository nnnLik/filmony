"""Watchlist entries for provider-aware cards.

Revision ID: w1x2y3z4a01
Revises: z9y8x7w65431
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'w1x2y3z4a01'
down_revision: str | Sequence[str] | None = 'z9y8x7w65431'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'watchlist_entry',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('card_id', sa.String(length=128), nullable=False),
        sa.Column('provider_meta', sa.JSON(), nullable=False),
        sa.Column('watch_tag', sa.String(length=32), nullable=False),
        sa.Column('watch_with_user_id', sa.Uuid(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
            name=op.f('fk_watchlist_entry_user_id_user'),
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['watch_with_user_id'],
            ['user.id'],
            name=op.f('fk_watchlist_entry_watch_with_user_id_user'),
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_watchlist_entry_user_id'), 'watchlist_entry', ['user_id'], unique=False
    )
    op.create_index(
        op.f('ix_watchlist_entry_card_id'), 'watchlist_entry', ['card_id'], unique=False
    )
    op.create_index(
        'uq_watchlist_entry_user_card',
        'watchlist_entry',
        ['user_id', 'card_id'],
        unique=True,
    )
    op.create_index(
        'ix_watchlist_entry_user_id_created_at_id',
        'watchlist_entry',
        ['user_id', 'created_at', 'id'],
        unique=False,
        postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
    )


def downgrade() -> None:
    op.drop_index('ix_watchlist_entry_user_id_created_at_id', table_name='watchlist_entry')
    op.drop_index('uq_watchlist_entry_user_card', table_name='watchlist_entry')
    op.drop_index(op.f('ix_watchlist_entry_card_id'), table_name='watchlist_entry')
    op.drop_index(op.f('ix_watchlist_entry_user_id'), table_name='watchlist_entry')
    op.drop_table('watchlist_entry')
