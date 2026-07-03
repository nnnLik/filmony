"""Add subscribed_activity_digest_state for Telegram digest idempotency.

Revision ID: x2y3z4a5b678
Revises: w1x2y3z4a05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'x2y3z4a5b678'
down_revision: str | Sequence[str] | None = 'w1x2y3z4a05'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'subscribed_activity_digest_state',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('recipient_user_id', sa.Uuid(), nullable=False),
        sa.Column('last_digest_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_digest_window_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_digest_window_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_digest_payload_hash', sa.String(length=64), nullable=True),
        sa.Column('last_successful_delivery_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['recipient_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'recipient_user_id', name='uq_subscribed_activity_digest_state_recipient'
        ),
    )
    op.create_index(
        'ix_subscribed_activity_digest_state_recipient_user_id',
        'subscribed_activity_digest_state',
        ['recipient_user_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        'ix_subscribed_activity_digest_state_recipient_user_id',
        table_name='subscribed_activity_digest_state',
    )
    op.drop_table('subscribed_activity_digest_state')
