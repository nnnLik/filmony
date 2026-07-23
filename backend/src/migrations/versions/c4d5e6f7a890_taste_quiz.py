"""Add taste quiz tables for guess-rating sessions and knowledge edges.

Revision ID: c4d5e6f7a890
Revises: b3c4d5e6f789
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c4d5e6f7a890'
down_revision: str | Sequence[str] | None = 'b3c4d5e6f789'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'taste_quiz_pair_progress',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guesser_user_id', sa.Uuid(), nullable=False),
        sa.Column('owner_user_id', sa.Uuid(), nullable=False),
        sa.Column('points_sum', sa.Float(), server_default='0', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('played_card_ids', sa.JSON(), server_default='[]', nullable=False),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint('guesser_user_id <> owner_user_id', name='ck_taste_quiz_no_self_pair'),
        sa.CheckConstraint('attempts >= 0', name='ck_taste_quiz_attempts_nonneg'),
        sa.CheckConstraint('points_sum >= 0', name='ck_taste_quiz_points_nonneg'),
        sa.ForeignKeyConstraint(['guesser_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('guesser_user_id', 'owner_user_id', name='uq_taste_quiz_pair_progress'),
    )
    op.create_index(
        'ix_taste_quiz_pair_progress_guesser_user_id',
        'taste_quiz_pair_progress',
        ['guesser_user_id'],
    )
    op.create_index(
        'ix_taste_quiz_pair_progress_owner_user_id',
        'taste_quiz_pair_progress',
        ['owner_user_id'],
    )

    op.create_table(
        'taste_quiz_session',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('guesser_user_id', sa.Uuid(), nullable=False),
        sa.Column('owner_user_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=16), server_default='active', nullable=False),
        sa.Column('round_points', sa.Float(), server_default='0', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['guesser_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_taste_quiz_session_guesser_user_id', 'taste_quiz_session', ['guesser_user_id'])
    op.create_index('ix_taste_quiz_session_owner_user_id', 'taste_quiz_session', ['owner_user_id'])
    op.create_index('ix_taste_quiz_session_status', 'taste_quiz_session', ['status'])
    op.create_index(
        'ix_taste_quiz_session_active_pair',
        'taste_quiz_session',
        ['guesser_user_id', 'owner_user_id', 'status'],
    )

    op.create_table(
        'taste_quiz_session_card',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('card_id', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('snapshot_title', sa.String(length=255), nullable=False),
        sa.Column('snapshot_poster_url', sa.String(length=2048), nullable=True),
        sa.Column('snapshot_company', sa.String(length=32), nullable=False),
        sa.Column('snapshot_mood_before', sa.String(length=32), nullable=False),
        sa.Column('snapshot_owner_rating', sa.Float(), nullable=False),
        sa.Column('snapshot_mood_after', sa.String(length=32), nullable=False),
        sa.Column('snapshot_watch_note', sa.Text(), server_default='', nullable=False),
        sa.Column('guess_rating', sa.Float(), nullable=True),
        sa.Column('points', sa.Float(), nullable=True),
        sa.Column('verdict_key', sa.String(length=16), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['taste_quiz_session.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['card_id'], ['user_card.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_taste_quiz_session_card_session_id', 'taste_quiz_session_card', ['session_id'])
    op.create_index('ix_taste_quiz_session_card_card_id', 'taste_quiz_session_card', ['card_id'])

    op.create_table(
        'taste_quiz_invite',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('owner_user_id', sa.Uuid(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['owner_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )
    op.create_index('ix_taste_quiz_invite_owner_user_id', 'taste_quiz_invite', ['owner_user_id'])
    op.create_index('ix_taste_quiz_invite_token', 'taste_quiz_invite', ['token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_taste_quiz_invite_token', table_name='taste_quiz_invite')
    op.drop_index('ix_taste_quiz_invite_owner_user_id', table_name='taste_quiz_invite')
    op.drop_table('taste_quiz_invite')
    op.drop_index('ix_taste_quiz_session_card_card_id', table_name='taste_quiz_session_card')
    op.drop_index('ix_taste_quiz_session_card_session_id', table_name='taste_quiz_session_card')
    op.drop_table('taste_quiz_session_card')
    op.drop_index('ix_taste_quiz_session_active_pair', table_name='taste_quiz_session')
    op.drop_index('ix_taste_quiz_session_status', table_name='taste_quiz_session')
    op.drop_index('ix_taste_quiz_session_owner_user_id', table_name='taste_quiz_session')
    op.drop_index('ix_taste_quiz_session_guesser_user_id', table_name='taste_quiz_session')
    op.drop_table('taste_quiz_session')
    op.drop_index('ix_taste_quiz_pair_progress_owner_user_id', table_name='taste_quiz_pair_progress')
    op.drop_index('ix_taste_quiz_pair_progress_guesser_user_id', table_name='taste_quiz_pair_progress')
    op.drop_table('taste_quiz_pair_progress')
