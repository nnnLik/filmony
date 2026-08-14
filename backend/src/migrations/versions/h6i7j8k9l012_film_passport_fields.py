"""film: Kinopoisk passport metadata sidecar table

Revision ID: h6i7j8k9l012
Revises: g5h6i7j8k901

Avoid ALTER TABLE film — prod app role may not own that legacy table.
Passport fields live in film_kinopoisk_passport (FK to film.id).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'h6i7j8k9l012'
down_revision: str | Sequence[str] | None = 'g5h6i7j8k901'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_table('film_kinopoisk_passport')
