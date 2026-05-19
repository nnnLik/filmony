"""game table + catalog_item.game_id for RAWG catalog

Revision ID: p3q4r5s6t890
Revises: a7b8c9d0e123
Create Date: 2026-05-14

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'p3q4r5s6t890'
down_revision: str | Sequence[str] | None = 'a7b8c9d0e123'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'game',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('rawg_id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=512), nullable=True),
        sa.Column('name_original', sa.String(length=512), nullable=True),
        sa.Column('released', sa.String(length=32), nullable=True),
        sa.Column('tba', sa.Boolean(), nullable=True),
        sa.Column('background_image', sa.String(length=2048), nullable=True),
        sa.Column('background_image_additional', sa.String(length=2048), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(length=2048), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('rating_top', sa.Integer(), nullable=True),
        sa.Column('ratings_count', sa.Integer(), nullable=True),
        sa.Column('metacritic', sa.Integer(), nullable=True),
        sa.Column('platforms_json', sa.JSON(), nullable=True),
        sa.Column('esrb_rating_json', sa.JSON(), nullable=True),
        sa.Column('ratings_json', sa.JSON(), nullable=True),
        sa.Column('added_by_status_json', sa.JSON(), nullable=True),
        sa.Column('metacritic_platforms_json', sa.JSON(), nullable=True),
        sa.Column('reactions_json', sa.JSON(), nullable=True),
        sa.Column('alternative_names_json', sa.JSON(), nullable=True),
        sa.Column('raw_search_snapshot', sa.JSON(), nullable=True),
        sa.Column('raw_detail_snapshot', sa.JSON(), nullable=True),
        sa.Column('search_synced_at', sa.DateTime(), nullable=True),
        sa.Column('detail_synced_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rawg_id', name='uq_game_rawg_id'),
    )

    op.add_column('catalog_item', sa.Column('game_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_catalog_item_game_id'), 'catalog_item', ['game_id'], unique=False)
    op.create_foreign_key(
        'fk_catalog_item_game_id_game',
        'catalog_item',
        'game',
        ['game_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_catalog_item_game_id_game', 'catalog_item', type_='foreignkey')
    op.drop_index(op.f('ix_catalog_item_game_id'), table_name='catalog_item')
    op.drop_column('catalog_item', 'game_id')

    op.drop_table('game')
