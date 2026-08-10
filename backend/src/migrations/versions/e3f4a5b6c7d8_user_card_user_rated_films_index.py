"""Partial index for rated user_card film lookups.

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'e3f4a5b6c7d8'
down_revision: str | Sequence[str] | None = 'd2e3f4a5b6c7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        'ix_user_card_user_rated_films',
        'user_card',
        ['user_id', 'film_id'],
        unique=False,
        postgresql_where=sa.text(
            'is_planned IS FALSE AND rating >= 1 AND film_id IS NOT NULL',
        ),
    )


def downgrade() -> None:
    op.drop_index('ix_user_card_user_rated_films', table_name='user_card')
