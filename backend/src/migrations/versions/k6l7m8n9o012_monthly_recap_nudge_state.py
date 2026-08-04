"""Add monthly_recap_nudge_state for Telegram recap nudge idempotency.

Revision ID: k6l7m8n9o012
Revises: i4j5k6l7m890
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'k6l7m8n9o012'
down_revision: str | Sequence[str] | None = 'i4j5k6l7m890'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'monthly_recap_nudge_state',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column(
            'sent_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year', 'month', name='uq_monthly_recap_nudge_user_month'),
    )
    op.create_index(
        'ix_monthly_recap_nudge_state_user_id',
        'monthly_recap_nudge_state',
        ['user_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_monthly_recap_nudge_state_user_id', table_name='monthly_recap_nudge_state')
    op.drop_table('monthly_recap_nudge_state')
