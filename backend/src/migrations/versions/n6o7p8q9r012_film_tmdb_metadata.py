"""film: TMDB metadata columns and snapshots

Revision ID: n6o7p8q9r012
Revises: l7m8n9o0p123
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'n6o7p8q9r012'
down_revision: str | Sequence[str] | None = 'l7m8n9o0p123'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('film', sa.Column('imdb_id', sa.String(length=16), nullable=True))
    op.add_column('film', sa.Column('tmdb_id', sa.Integer(), nullable=True))
    op.add_column('film', sa.Column('primary_director_tmdb_id', sa.Integer(), nullable=True))
    op.add_column('film', sa.Column('tmdb_detail_snapshot_json', sa.JSON(), nullable=True))
    op.add_column('film', sa.Column('tmdb_synced_at', sa.DateTime(), nullable=True))
    op.create_index('ix_film_imdb_id', 'film', ['imdb_id'], unique=False)
    op.create_index('ix_film_tmdb_id', 'film', ['tmdb_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_film_tmdb_id', table_name='film')
    op.drop_index('ix_film_imdb_id', table_name='film')
    op.drop_column('film', 'tmdb_synced_at')
    op.drop_column('film', 'tmdb_detail_snapshot_json')
    op.drop_column('film', 'primary_director_tmdb_id')
    op.drop_column('film', 'tmdb_id')
    op.drop_column('film', 'imdb_id')
