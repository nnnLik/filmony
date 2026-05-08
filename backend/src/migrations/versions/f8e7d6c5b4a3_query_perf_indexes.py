"""Indexes for feed, reactions, watchlist; drop redundant b-tree indexes.

Revision ID: f8e7d6c5b4a3
Revises: e7f9a8b01234
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'f8e7d6c5b4a3'
down_revision: str | Sequence[str] | None = 'e7f9a8b01234'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        'ix_movie_card_user_id_created_at_id',
        'movie_card',
        ['user_id', 'created_at', 'id'],
        unique=False,
        postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
    )
    op.create_index(
        'ix_movie_card_created_at_id',
        'movie_card',
        ['created_at', 'id'],
        unique=False,
        postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
    )
    op.create_index(
        'ix_user_reaction_user_target_kind',
        'user_reaction',
        ['user_id', 'target_kind', 'target_id'],
        unique=False,
    )
    op.drop_index(op.f('ix_user_reaction_user_id'), table_name='user_reaction')
    op.drop_index(op.f('ix_user_watchlist_film_user_id'), table_name='user_watchlist_film')
    op.drop_index(op.f('ix_user_watchlist_film_film_id'), table_name='user_watchlist_film')


def downgrade() -> None:
    op.create_index(
        op.f('ix_user_watchlist_film_film_id'),
        'user_watchlist_film',
        ['film_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_user_watchlist_film_user_id'),
        'user_watchlist_film',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_user_reaction_user_id'),
        'user_reaction',
        ['user_id'],
        unique=False,
    )
    op.drop_index('ix_user_reaction_user_target_kind', table_name='user_reaction')
    op.drop_index('ix_movie_card_created_at_id', table_name='movie_card')
    op.drop_index('ix_movie_card_user_id_created_at_id', table_name='movie_card')
