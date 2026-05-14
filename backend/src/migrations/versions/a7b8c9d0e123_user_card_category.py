"""user_card_category + movie_card.user_card_category_id

Revision ID: a7b8c9d0e123
Revises: y9z0a1b2c345
Create Date: 2026-05-14

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a7b8c9d0e123'
down_revision: str | Sequence[str] | None = 'y9z0a1b2c345'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'user_card_category',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'user_id', sa.Uuid(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False
        ),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_card_category_user_name'),
    )
    op.create_index('ix_user_card_category_user_id', 'user_card_category', ['user_id'])
    op.create_index(
        'ix_user_card_category_user_id_name',
        'user_card_category',
        ['user_id', 'name'],
    )

    op.execute(
        sa.text(
            """
            INSERT INTO user_card_category (user_id, name, created_at)
            SELECT DISTINCT mc.user_id, 'Фильмы', now()
            FROM movie_card AS mc
            """
        )
    )

    op.add_column(
        'movie_card',
        sa.Column('user_card_category_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_movie_card_user_card_category_id',
        'movie_card',
        'user_card_category',
        ['user_card_category_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.create_index(
        'ix_movie_card_user_card_category_id',
        'movie_card',
        ['user_card_category_id'],
    )

    op.execute(
        sa.text(
            """
            UPDATE movie_card AS mc
            SET user_card_category_id = ucc.id
            FROM user_card_category AS ucc
            WHERE ucc.user_id = mc.user_id
              AND ucc.name = 'Фильмы'
            """
        )
    )

    op.alter_column('movie_card', 'user_card_category_id', nullable=False)


def downgrade() -> None:
    op.drop_index('ix_movie_card_user_card_category_id', table_name='movie_card')
    op.drop_constraint('fk_movie_card_user_card_category_id', 'movie_card', type_='foreignkey')
    op.drop_column('movie_card', 'user_card_category_id')
    op.drop_index('ix_user_card_category_user_id_name', table_name='user_card_category')
    op.drop_index('ix_user_card_category_user_id', table_name='user_card_category')
    op.drop_table('user_card_category')
