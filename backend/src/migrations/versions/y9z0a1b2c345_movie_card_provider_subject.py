"""movie_card provider + external_id (card-level catalog subject)

Revision ID: y9z0a1b2c345
Revises: w3x4y5z6a012
Create Date: 2026-05-14

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'y9z0a1b2c345'
down_revision: str | Sequence[str] | None = 'w3x4y5z6a012'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'movie_card',
        sa.Column('provider', sa.String(length=64), nullable=True),
    )
    op.add_column(
        'movie_card',
        sa.Column('external_id', sa.String(length=255), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE movie_card AS mc
            SET provider = ci.provider,
                external_id = ci.external_id
            FROM catalog_item AS ci
            WHERE mc.catalog_item_id = ci.id
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE movie_card AS mc
            SET provider = 'kinopoisk',
                external_id = CAST(f.kinopoisk_id AS VARCHAR)
            FROM film AS f
            WHERE mc.film_id = f.id
              AND mc.catalog_item_id IS NULL
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE movie_card
            SET provider = 'no_provider',
                external_id = NULL
            WHERE film_id IS NULL
              AND catalog_item_id IS NULL
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE movie_card
            SET provider = 'no_provider',
                external_id = NULL
            WHERE provider IS NULL
            """
        )
    )

    op.alter_column('movie_card', 'provider', existing_type=sa.String(length=64), nullable=False)

    op.create_index(
        op.f('ix_movie_card_provider'),
        'movie_card',
        ['provider'],
        unique=False,
    )

    op.create_index(
        'uq_movie_card_user_provider_external_kinopoisk_partial',
        'movie_card',
        ['user_id', 'provider', 'external_id'],
        unique=True,
        postgresql_where=sa.text("provider = 'kinopoisk' AND external_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        'uq_movie_card_user_provider_external_kinopoisk_partial',
        table_name='movie_card',
    )
    op.drop_index(op.f('ix_movie_card_provider'), table_name='movie_card')
    op.drop_column('movie_card', 'external_id')
    op.drop_column('movie_card', 'provider')
