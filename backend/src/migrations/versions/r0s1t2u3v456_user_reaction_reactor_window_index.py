"""Partial index for reaction reactor embed window queries (partition + order by id desc).

Revision ID: r0s1t2u3v456
Revises: p3q4r5s6t890
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = 'r0s1t2u3v456'
down_revision: str | Sequence[str] | None = 'p3q4r5s6t890'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        'ix_user_reaction_target_kind_type_id',
        'user_reaction',
        ['target_kind', 'target_id', 'reaction_type_id', 'id'],
        unique=False,
        postgresql_ops={'id': 'DESC'},
    )


def downgrade() -> None:
    op.drop_index('ix_user_reaction_target_kind_type_id', table_name='user_reaction')
