"""watch_session co-view sessions and feed_post.watch_session_id.

Revision ID: d5e6f7a89012
Revises: c4d5e6f7a890
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'd5e6f7a89012'
down_revision: str | Sequence[str] | None = 'c4d5e6f7a890'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'watch_session',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('initiator_user_id', sa.Uuid(), nullable=False),
        sa.Column('anchor_film_id', sa.Integer(), nullable=True),
        sa.Column('anchor_catalog_item_id', sa.Integer(), nullable=True),
        sa.Column('participant_user_ids', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('status', sa.String(length=16), server_default='planned', nullable=False),
        sa.Column('source_watchlist_entry_id', sa.Integer(), nullable=True),
        sa.Column('first_rated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('nudge_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('feed_post_id', sa.Integer(), nullable=True),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint(
            '(anchor_film_id IS NOT NULL AND anchor_catalog_item_id IS NULL) OR '
            '(anchor_film_id IS NULL AND anchor_catalog_item_id IS NOT NULL)',
            name='ck_watch_session_exactly_one_anchor',
        ),
        sa.ForeignKeyConstraint(['anchor_catalog_item_id'], ['catalog_item.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['anchor_film_id'], ['film.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['feed_post_id'],
            ['feed_post.id'],
            ondelete='SET NULL',
            name='fk_watch_session_feed_post_id',
        ),
        sa.ForeignKeyConstraint(['initiator_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['source_watchlist_entry_id'],
            ['watchlist_entry.id'],
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_watch_session_initiator_user_id',
        'watch_session',
        ['initiator_user_id'],
    )
    op.create_index(
        'ix_watch_session_anchor_film_id',
        'watch_session',
        ['anchor_film_id'],
    )
    op.create_index(
        'ix_watch_session_anchor_catalog_item_id',
        'watch_session',
        ['anchor_catalog_item_id'],
    )
    op.create_index('ix_watch_session_status', 'watch_session', ['status'])
    op.create_index(
        'ix_watch_session_source_watchlist_entry_id',
        'watch_session',
        ['source_watchlist_entry_id'],
    )
    op.create_index('ix_watch_session_feed_post_id', 'watch_session', ['feed_post_id'])
    op.create_index(
        'ix_watch_session_status_first_rated_at',
        'watch_session',
        ['status', 'first_rated_at'],
    )

    op.add_column('feed_post', sa.Column('watch_session_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_feed_post_watch_session_id',
        'feed_post',
        'watch_session',
        ['watch_session_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        op.f('ix_feed_post_watch_session_id'),
        'feed_post',
        ['watch_session_id'],
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_feed_post_watch_session_id'), table_name='feed_post')
    op.drop_constraint('fk_feed_post_watch_session_id', 'feed_post', type_='foreignkey')
    op.drop_column('feed_post', 'watch_session_id')

    op.drop_index('ix_watch_session_status_first_rated_at', table_name='watch_session')
    op.drop_index('ix_watch_session_feed_post_id', table_name='watch_session')
    op.drop_index('ix_watch_session_source_watchlist_entry_id', table_name='watch_session')
    op.drop_index('ix_watch_session_status', table_name='watch_session')
    op.drop_index('ix_watch_session_anchor_catalog_item_id', table_name='watch_session')
    op.drop_index('ix_watch_session_anchor_film_id', table_name='watch_session')
    op.drop_index('ix_watch_session_initiator_user_id', table_name='watch_session')
    op.drop_table('watch_session')
