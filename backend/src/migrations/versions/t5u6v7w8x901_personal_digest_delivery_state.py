"""Add personal_digest_delivery_state for digest Telegram idempotency.

Revision ID: t5u6v7w8x901
Revises: s4t5u6v7w890
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 't5u6v7w8x901'
down_revision: str | Sequence[str] | None = 's4t5u6v7w890'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'personal_digest_delivery_state',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('period', sa.String(length=8), nullable=False),
        sa.Column('period_key', sa.String(length=16), nullable=False),
        sa.Column(
            'sent_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('payload_hash', sa.String(length=64), nullable=True),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id',
            'period',
            'period_key',
            name='uq_personal_digest_delivery_user_period_key',
        ),
        comment='Idempotent personal digest sends (week|month)',
    )
    op.create_index(
        'ix_personal_digest_delivery_state_user_id',
        'personal_digest_delivery_state',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        'ix_personal_digest_delivery_state_user_id',
        table_name='personal_digest_delivery_state',
    )
    op.drop_table('personal_digest_delivery_state')
