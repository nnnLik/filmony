"""film: Kinopoisk passport metadata columns

Revision ID: h6i7j8k9l012
Revises: g5h6i7j8k901
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
    op.add_column('film', sa.Column('film_length', sa.Integer(), nullable=True))
    op.add_column('film', sa.Column('slogan', sa.Text(), nullable=True))
    op.add_column('film', sa.Column('rating_kinopoisk', sa.Float(), nullable=True))
    op.add_column('film', sa.Column('rating_imdb', sa.Float(), nullable=True))
    op.add_column('film', sa.Column('rating_age_limits', sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column('film', 'rating_age_limits')
    op.drop_column('film', 'rating_imdb')
    op.drop_column('film', 'rating_kinopoisk')
    op.drop_column('film', 'slogan')
    op.drop_column('film', 'film_length')
