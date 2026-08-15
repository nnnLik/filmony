"""film: move Kinopoisk passport columns onto film; drop sidecar

Revision ID: i7j8k9l0m123
Revises: h6i7j8k9l012

Prod app role now owns legacy film table (see deploy ownership fix).
Sidecar film_kinopoisk_passport was empty at cutover; copy step is idempotent.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'i7j8k9l0m123'
down_revision: str | Sequence[str] | None = 'h6i7j8k9l012'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('film', sa.Column('film_length', sa.Integer(), nullable=True))
    op.add_column('film', sa.Column('slogan', sa.Text(), nullable=True))
    op.add_column('film', sa.Column('rating_kinopoisk', sa.Float(), nullable=True))
    op.add_column('film', sa.Column('rating_imdb', sa.Float(), nullable=True))
    op.add_column('film', sa.Column('rating_age_limits', sa.String(length=16), nullable=True))

    op.execute(
        """
        UPDATE film AS f
        SET
            film_length = p.film_length,
            slogan = p.slogan,
            rating_kinopoisk = p.rating_kinopoisk,
            rating_imdb = p.rating_imdb,
            rating_age_limits = p.rating_age_limits
        FROM film_kinopoisk_passport AS p
        WHERE p.film_id = f.id
        """
    )

    op.drop_table('film_kinopoisk_passport')


def downgrade() -> None:
    op.create_table(
        'film_kinopoisk_passport',
        sa.Column('film_id', sa.Integer(), nullable=False),
        sa.Column('film_length', sa.Integer(), nullable=True),
        sa.Column('slogan', sa.Text(), nullable=True),
        sa.Column('rating_kinopoisk', sa.Float(), nullable=True),
        sa.Column('rating_imdb', sa.Float(), nullable=True),
        sa.Column('rating_age_limits', sa.String(length=16), nullable=True),
        sa.ForeignKeyConstraint(['film_id'], ['film.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('film_id'),
    )

    op.execute(
        """
        INSERT INTO film_kinopoisk_passport (
            film_id,
            film_length,
            slogan,
            rating_kinopoisk,
            rating_imdb,
            rating_age_limits
        )
        SELECT
            id,
            film_length,
            slogan,
            rating_kinopoisk,
            rating_imdb,
            rating_age_limits
        FROM film
        WHERE
            film_length IS NOT NULL
            OR slogan IS NOT NULL
            OR rating_kinopoisk IS NOT NULL
            OR rating_imdb IS NOT NULL
            OR rating_age_limits IS NOT NULL
        """
    )

    op.drop_column('film', 'rating_age_limits')
    op.drop_column('film', 'rating_imdb')
    op.drop_column('film', 'rating_kinopoisk')
    op.drop_column('film', 'slogan')
    op.drop_column('film', 'film_length')
