"""movie_card user-owned display fields + Kinopoisk film backfill

Revision ID: w3x4y5z6a012
Revises: u1v2w3x4y890
Create Date: 2026-05-13

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'w3x4y5z6a012'
down_revision: str | Sequence[str] | None = 'u1v2w3x4y890'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('movie_card', sa.Column('display_title', sa.String(length=255), nullable=True))
    op.add_column(
        'movie_card', sa.Column('display_cover_url', sa.String(length=2048), nullable=True)
    )
    op.add_column('movie_card', sa.Column('display_summary', sa.Text(), nullable=True))
    op.add_column('movie_card', sa.Column('source_url', sa.String(length=2048), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE movie_card AS mc
            SET
              display_title = f.title,
              display_cover_url = f.poster_url,
              display_summary = COALESCE(f.short_description, f.description)
            FROM film AS f
            WHERE mc.film_id = f.id
            """
        )
    )


def downgrade() -> None:
    op.drop_column('movie_card', 'source_url')
    op.drop_column('movie_card', 'display_summary')
    op.drop_column('movie_card', 'display_cover_url')
    op.drop_column('movie_card', 'display_title')
