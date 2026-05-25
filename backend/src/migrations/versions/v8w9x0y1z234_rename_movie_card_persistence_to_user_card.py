"""rename movie_card* persistence to user_card, card_comment, card_tag.

Tables: movie_card → user_card, movie_card_comment → card_comment,
movie_card_tag → card_tag; FK column renames per ORM naming.

Revision ID: v8w9x0y1z234
Revises: q7r8s9t0u123

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'v8w9x0y1z234'
down_revision: str | Sequence[str] | None = 'q7r8s9t0u123'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _rename_index(old: str, new: str) -> None:
    op.execute(sa.text(f'ALTER INDEX IF EXISTS "{old}" RENAME TO "{new}"'))


def _rename_fk(bind, table: str, old: str, new: str) -> None:
    insp = sa.inspect(bind)
    for fk in insp.get_foreign_keys(table):
        if fk.get('name') == old:
            op.execute(sa.text(f'ALTER TABLE "{table}" RENAME CONSTRAINT "{old}" TO "{new}"'))
            return


def _rename_unique_constraint(bind, table: str, old: str, new: str) -> None:
    insp = sa.inspect(bind)
    names = {c['name'] for c in insp.get_unique_constraints(table) if c['name']}
    if old in names:
        op.execute(sa.text(f'ALTER TABLE "{table}" RENAME CONSTRAINT "{old}" TO "{new}"'))


def upgrade() -> None:
    bind = op.get_bind()
    assert bind is not None

    # --- user_card (table still movie_card): indexes ---
    for old, new in (
        ('ix_movie_card_film_id', 'ix_user_card_film_id'),
        ('ix_movie_card_user_id', 'ix_user_card_user_id'),
        ('ix_movie_card_catalog_item_id', 'ix_user_card_catalog_item_id'),
        ('ix_movie_card_provider', 'ix_user_card_provider'),
        ('ix_movie_card_user_card_category_id', 'ix_user_card_user_card_category_id'),
        ('uq_movie_card_user_catalog_item_id_partial', 'uq_user_card_user_catalog_item_id_partial'),
        ('uq_movie_card_user_film_id_partial', 'uq_user_card_user_film_id_partial'),
        (
            'uq_movie_card_user_provider_external_kinopoisk_partial',
            'uq_user_card_user_provider_external_kinopoisk_partial',
        ),
        ('ix_movie_card_user_id_created_at_id', 'ix_user_card_user_id_created_at_id'),
        ('ix_movie_card_created_at_id', 'ix_user_card_created_at_id'),
        ('ix_movie_card_user_favorites_order', 'ix_user_card_user_favorites_order'),
    ):
        _rename_index(old, new)

    op.rename_table('movie_card', 'user_card')
    _rename_fk(
        bind,
        'user_card',
        'fk_movie_card_catalog_item_id_catalog_item',
        'fk_user_card_catalog_item_id_catalog_item',
    )
    _rename_fk(
        bind,
        'user_card',
        'fk_movie_card_user_card_category_id',
        'fk_user_card_user_card_category_id',
    )

    # --- card_comment (table still movie_card_comment): indexes then column + table ---
    for old, new in (
        ('ix_movie_card_comment_card_parent_id', 'ix_card_comment_card_parent_id'),
        ('ix_movie_card_comment_movie_card_id', 'ix_card_comment_card_id'),
        ('ix_movie_card_comment_parent_comment_id', 'ix_card_comment_parent_comment_id'),
        ('ix_movie_card_comment_user_id', 'ix_card_comment_user_id'),
    ):
        _rename_index(old, new)

    op.alter_column(
        'movie_card_comment',
        'movie_card_id',
        new_column_name='card_id',
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.rename_table('movie_card_comment', 'card_comment')

    # --- card_tag ---
    _rename_unique_constraint(bind, 'movie_card_tag', 'uq_movie_card_tag_unique', 'uq_card_tag_card_id_tag')
    _rename_index('ix_movie_card_tag_movie_card_id', 'ix_card_tag_card_id')
    op.alter_column(
        'movie_card_tag',
        'movie_card_id',
        new_column_name='card_id',
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.rename_table('movie_card_tag', 'card_tag')

    # --- feed_post referenced card column + index ---
    _rename_index('ix_feed_post_referenced_movie_card_id', 'ix_feed_post_referenced_card_id')
    op.alter_column(
        'feed_post',
        'referenced_movie_card_id',
        new_column_name='referenced_card_id',
        existing_type=sa.Integer(),
        existing_nullable=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    assert bind is not None

    op.alter_column(
        'feed_post',
        'referenced_card_id',
        new_column_name='referenced_movie_card_id',
        existing_type=sa.Integer(),
        existing_nullable=True,
    )
    _rename_index('ix_feed_post_referenced_card_id', 'ix_feed_post_referenced_movie_card_id')

    op.rename_table('card_tag', 'movie_card_tag')
    op.alter_column(
        'movie_card_tag',
        'card_id',
        new_column_name='movie_card_id',
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    _rename_index('ix_card_tag_card_id', 'ix_movie_card_tag_movie_card_id')
    _rename_unique_constraint(bind, 'movie_card_tag', 'uq_card_tag_card_id_tag', 'uq_movie_card_tag_unique')

    op.rename_table('card_comment', 'movie_card_comment')
    op.alter_column(
        'movie_card_comment',
        'card_id',
        new_column_name='movie_card_id',
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    for old, new in (
        ('ix_card_comment_card_parent_id', 'ix_movie_card_comment_card_parent_id'),
        ('ix_card_comment_card_id', 'ix_movie_card_comment_movie_card_id'),
        ('ix_card_comment_parent_comment_id', 'ix_movie_card_comment_parent_comment_id'),
        ('ix_card_comment_user_id', 'ix_movie_card_comment_user_id'),
    ):
        _rename_index(old, new)

    _rename_fk(
        bind,
        'user_card',
        'fk_user_card_user_card_category_id',
        'fk_movie_card_user_card_category_id',
    )
    _rename_fk(
        bind,
        'user_card',
        'fk_user_card_catalog_item_id_catalog_item',
        'fk_movie_card_catalog_item_id_catalog_item',
    )
    op.rename_table('user_card', 'movie_card')

    for old, new in (
        ('ix_user_card_user_favorites_order', 'ix_movie_card_user_favorites_order'),
        ('ix_user_card_created_at_id', 'ix_movie_card_created_at_id'),
        ('ix_user_card_user_id_created_at_id', 'ix_movie_card_user_id_created_at_id'),
        (
            'uq_user_card_user_provider_external_kinopoisk_partial',
            'uq_movie_card_user_provider_external_kinopoisk_partial',
        ),
        ('uq_user_card_user_film_id_partial', 'uq_movie_card_user_film_id_partial'),
        ('uq_user_card_user_catalog_item_id_partial', 'uq_movie_card_user_catalog_item_id_partial'),
        ('ix_user_card_user_card_category_id', 'ix_movie_card_user_card_category_id'),
        ('ix_user_card_provider', 'ix_movie_card_provider'),
        ('ix_user_card_catalog_item_id', 'ix_movie_card_catalog_item_id'),
        ('ix_user_card_user_id', 'ix_movie_card_user_id'),
        ('ix_user_card_film_id', 'ix_movie_card_film_id'),
    ):
        _rename_index(old, new)
