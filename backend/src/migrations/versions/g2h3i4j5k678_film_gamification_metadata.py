"""film: gamification metadata columns

Revision ID: g2h3i4j5k678
Revises: f1e2d3c4b567
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'g2h3i4j5k678'
down_revision: str | Sequence[str] | None = 'f1e2d3c4b567'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'film',
        sa.Column('countries', sa.JSON(), nullable=False, server_default='[]'),
    )
    op.add_column(
        'film',
        sa.Column('primary_director_kinopoisk_id', sa.Integer(), nullable=True),
    )
    op.add_column(
        'film',
        sa.Column('primary_director_name', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'film',
        sa.Column('franchise_key', sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('film', 'franchise_key')
    op.drop_column('film', 'primary_director_name')
    op.drop_column('film', 'primary_director_kinopoisk_id')
    op.drop_column('film', 'countries')
