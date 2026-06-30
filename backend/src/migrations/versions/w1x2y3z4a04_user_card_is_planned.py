"""Add user_card.is_planned for watchlist feed card snippets.

Revision ID: w1x2y3z4a04
Revises: w1x2y3z4a03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'w1x2y3z4a04'
down_revision: str | Sequence[str] | None = 'w1x2y3z4a03'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'user_card',
        sa.Column('is_planned', sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('user_card', 'is_planned')
