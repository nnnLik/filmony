"""Partial indexes on user_card.completed_at for global/profile feed sort.

Revision ID: j8k9l0m1n234
Revises: i7j8k9l0m123
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'j8k9l0m1n234'
down_revision: str | Sequence[str] | None = 'i7j8k9l0m123'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        'ix_user_card_completed_at_id',
        'user_card',
        ['completed_at', 'id'],
        unique=False,
        postgresql_ops={'completed_at': 'DESC', 'id': 'DESC'},
        postgresql_where=sa.text('is_planned IS FALSE AND completed_at IS NOT NULL'),
    )
    op.create_index(
        'ix_user_card_user_id_completed_at_id',
        'user_card',
        ['user_id', 'completed_at', 'id'],
        unique=False,
        postgresql_ops={'completed_at': 'DESC', 'id': 'DESC'},
        postgresql_where=sa.text('is_planned IS FALSE'),
    )


def downgrade() -> None:
    op.drop_index('ix_user_card_user_id_completed_at_id', table_name='user_card')
    op.drop_index('ix_user_card_completed_at_id', table_name='user_card')
