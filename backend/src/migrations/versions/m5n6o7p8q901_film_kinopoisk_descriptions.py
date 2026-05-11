"""film: short_description and description from Kinopoisk.

Revision ID: m5n6o7p8q901
Revises: l4m5n6o7p890
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'm5n6o7p8q901'
down_revision: str | Sequence[str] | None = 'l4m5n6o7p890'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'film',
        sa.Column('short_description', sa.Text(), nullable=True),
    )
    op.add_column(
        'film',
        sa.Column('description', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('film', 'description')
    op.drop_column('film', 'short_description')
