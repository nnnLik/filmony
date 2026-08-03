"""Index on film.primary_director_kinopoisk_id for director catalog queries.

Revision ID: h3i4j5k6l789
Revises: g2h3i4j5k678
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = 'h3i4j5k6l789'
down_revision: str | Sequence[str] | None = 'g2h3i4j5k678'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        'ix_film_primary_director_kinopoisk_id',
        'film',
        ['primary_director_kinopoisk_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_film_primary_director_kinopoisk_id', table_name='film')
