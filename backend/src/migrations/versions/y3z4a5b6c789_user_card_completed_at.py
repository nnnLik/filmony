"""Add user_card.completed_at for activity heatmap aggregation.

Revision ID: y3z4a5b6c789
Revises: x2y3z4a5b678
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'y3z4a5b6c789'
down_revision: str | Sequence[str] | None = 'x2y3z4a5b678'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'user_card',
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE user_card
            SET completed_at = created_at
            WHERE is_planned IS FALSE AND completed_at IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_column('user_card', 'completed_at')
