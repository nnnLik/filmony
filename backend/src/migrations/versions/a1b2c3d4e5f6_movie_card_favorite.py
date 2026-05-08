"""Movie card favorite flag and marked-at timestamp.

Revision ID: a1b2c3d4e5f6
Revises: f8e7d6c5b4a3
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = 'f8e7d6c5b4a3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'movie_card',
        sa.Column('is_favorite', sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        'movie_card', sa.Column('favorite_marked_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        'ix_movie_card_user_favorites_order',
        'movie_card',
        ['user_id', 'favorite_marked_at', 'id'],
        unique=False,
        postgresql_ops={'favorite_marked_at': 'DESC NULLS LAST', 'id': 'DESC'},
        postgresql_where=sa.text('is_favorite IS TRUE'),
    )


def downgrade() -> None:
    op.drop_index('ix_movie_card_user_favorites_order', table_name='movie_card')
    op.drop_column('movie_card', 'favorite_marked_at')
    op.drop_column('movie_card', 'is_favorite')
