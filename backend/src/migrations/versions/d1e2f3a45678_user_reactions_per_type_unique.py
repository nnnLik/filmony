"""Allow multiple reactions per viewer per movie card / comment target.

Revision ID: d1e2f3a45678
Revises: c4d5e6f789ab
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'd1e2f3a45678'
down_revision: str | Sequence[str] | None = 'c4d5e6f789ab'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint('uq_user_reaction_target', 'user_reaction', type_='unique')
    op.create_unique_constraint(
        'uq_user_reaction_user_target_kind_type',
        'user_reaction',
        ['user_id', 'target_kind', 'target_id', 'reaction_type_id'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_user_reaction_user_target_kind_type', 'user_reaction', type_='unique')
    op.create_unique_constraint(
        'uq_user_reaction_target',
        'user_reaction',
        ['user_id', 'target_kind', 'target_id'],
    )
