"""Index on film.franchise_key for franchise catalog queries.

Revision ID: i4j5k6l7m890
Revises: h3i4j5k6l789
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = 'i4j5k6l7m890'
down_revision: str | Sequence[str] | None = 'h3i4j5k6l789'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        'ix_film_franchise_key',
        'film',
        ['franchise_key'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_film_franchise_key', table_name='film')
