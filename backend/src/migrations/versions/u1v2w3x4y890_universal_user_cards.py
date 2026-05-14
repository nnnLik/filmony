"""universal user cards schema: catalog_item + movie_card.catalog_item_id

Revision ID: u1v2w3x4y890
Revises: n0o1p2q3r678
Create Date: 2026-05-13

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'u1v2w3x4y890'
down_revision: str | Sequence[str] | None = 'n0o1p2q3r678'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'catalog_item',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('film_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['film_id'], ['film.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'external_id', name='uq_catalog_item_provider_external'),
    )
    op.create_index(op.f('ix_catalog_item_film_id'), 'catalog_item', ['film_id'], unique=False)
    op.create_index(op.f('ix_catalog_item_provider'), 'catalog_item', ['provider'], unique=False)

    op.execute(
        sa.text(
            """
            INSERT INTO catalog_item (provider, external_id, film_id)
            SELECT 'kinopoisk', CAST(kinopoisk_id AS VARCHAR), id
            FROM film
            """
        )
    )

    op.add_column('movie_card', sa.Column('catalog_item_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_movie_card_catalog_item_id_catalog_item',
        'movie_card',
        'catalog_item',
        ['catalog_item_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.create_index(
        op.f('ix_movie_card_catalog_item_id'), 'movie_card', ['catalog_item_id'], unique=False
    )

    op.execute(
        sa.text(
            """
            UPDATE movie_card AS mc
            SET catalog_item_id = ci.id
            FROM catalog_item AS ci
            WHERE ci.film_id = mc.film_id
            """
        )
    )

    op.drop_constraint('uq_movie_card_user_film', 'movie_card', type_='unique')

    op.alter_column('movie_card', 'film_id', existing_type=sa.Integer(), nullable=True)

    op.create_index(
        'uq_movie_card_user_catalog_item_id_partial',
        'movie_card',
        ['user_id', 'catalog_item_id'],
        unique=True,
        postgresql_where=sa.text('catalog_item_id IS NOT NULL'),
    )
    op.create_index(
        'uq_movie_card_user_film_id_partial',
        'movie_card',
        ['user_id', 'film_id'],
        unique=True,
        postgresql_where=sa.text('film_id IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('uq_movie_card_user_film_id_partial', table_name='movie_card')
    op.drop_index('uq_movie_card_user_catalog_item_id_partial', table_name='movie_card')

    op.execute(
        sa.text(
            """
            UPDATE movie_card AS mc
            SET film_id = ci.film_id
            FROM catalog_item AS ci
            WHERE mc.catalog_item_id = ci.id
              AND mc.film_id IS NULL
              AND ci.film_id IS NOT NULL
            """
        )
    )

    bind = op.get_bind()
    orphan = bind.execute(
        sa.text('SELECT COUNT(*) FROM movie_card WHERE film_id IS NULL')
    ).scalar_one()
    if orphan and int(orphan) > 0:
        raise RuntimeError(
            'Cannot downgrade universal_user_cards: movie_card rows with NULL film_id exist '
            '(manual or non-film cards). Remove or fix them before downgrading.'
        )

    op.alter_column('movie_card', 'film_id', existing_type=sa.Integer(), nullable=False)

    op.create_unique_constraint('uq_movie_card_user_film', 'movie_card', ['user_id', 'film_id'])

    op.drop_constraint(
        'fk_movie_card_catalog_item_id_catalog_item', 'movie_card', type_='foreignkey'
    )
    op.drop_index(op.f('ix_movie_card_catalog_item_id'), table_name='movie_card')
    op.drop_column('movie_card', 'catalog_item_id')

    op.drop_index(op.f('ix_catalog_item_provider'), table_name='catalog_item')
    op.drop_index(op.f('ix_catalog_item_film_id'), table_name='catalog_item')
    op.drop_table('catalog_item')
