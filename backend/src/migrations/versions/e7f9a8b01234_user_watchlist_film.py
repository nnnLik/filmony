"""User watchlist (films to watch, no rating).

Revision ID: e7f9a8b01234
Revises: d1e2f3a45678
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'e7f9a8b01234'
down_revision: str | Sequence[str] | None = 'd1e2f3a45678'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'user_watchlist_film',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('film_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ['film_id'],
            ['film.id'],
            name=op.f('fk_user_watchlist_film_film_id_film'),
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
            name=op.f('fk_user_watchlist_film_user_id_user'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'film_id', name='uq_user_watchlist_film_user_film'),
    )
    op.create_index(
        op.f('ix_user_watchlist_film_film_id'), 'user_watchlist_film', ['film_id'], unique=False
    )
    op.create_index(
        op.f('ix_user_watchlist_film_user_id'), 'user_watchlist_film', ['user_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_user_watchlist_film_user_id'), table_name='user_watchlist_film')
    op.drop_index(op.f('ix_user_watchlist_film_film_id'), table_name='user_watchlist_film')
    op.drop_table('user_watchlist_film')
