"""film: primary director poster URL from Kinopoisk staff

Revision ID: o7p8q9r0s123
Revises: n6o7p8q9r012
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'o7p8q9r0s123'
down_revision: str | Sequence[str] | None = 'n6o7p8q9r012'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'film',
        sa.Column('primary_director_poster_url', sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('film', 'primary_director_poster_url')
